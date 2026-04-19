"""
Xtream Codes Server Implementation.
This server implements the Xtream Codes API and translates requests
to Jellyfin API calls for Movies and TV Series.
"""
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from flask import Flask, request, Response, jsonify, send_file

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jellyfin_client import JellyfinClient

# Detect if we're in a real terminal
NO_COLOR = os.environ.get('NO_COLOR', '') or not sys.stderr.isatty()

# ANSI color codes
if NO_COLOR:
    GREY = GREEN = YELLOW = RED = BOLD_RED = CYAN = MAGENTA = BOLD = RESET = ""
else:
    GREY = "\033[90m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_RED = "\033[1;31m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    def format(self, record):
        if NO_COLOR:
            # Clean format for Docker logs / non-TTY
            timestamp = self.formatTime(record, datefmt='%Y-%m-%d %H:%M:%S')
            level = f"{record.levelname:<8}"
            name = record.name
            msg = record.getMessage()
            return f"{timestamp} {level} {name}: {msg}"
        else:
            # Colorful format for real terminals
            color = {
                logging.DEBUG: GREY,
                logging.INFO: GREEN,
                logging.WARNING: YELLOW,
                logging.ERROR: RED,
                logging.CRITICAL: BOLD_RED,
            }.get(record.levelno, RESET)
            timestamp = f"{CYAN}{self.formatTime(record, datefmt='%Y-%m-%d %H:%M:%S')}{RESET}"
            level = f"{color}{record.levelname:<8}{RESET}"
            name = f"{MAGENTA}{record.name}{RESET}"
            msg = record.getMessage()
            if record.levelno >= logging.WARNING:
                msg = f"{color}{msg}{RESET}"
            return f"{timestamp} {level} {name}: {msg}"


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Suppress noisy werkzeug logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)


class XtreamServer:
    """Xtream Codes API Server backed by Jellyfin"""

    def __init__(self, config_path: str = 'config/config.json'):
        self.config = self._load_config(config_path)
        self.jellyfin = JellyfinClient(
            self.config['jellyfin']['server_url'],
            self.config['jellyfin'].get('api_key'), username=self.config['jellyfin'].get('username'), password=self.config['jellyfin'].get('password')
        )
        self.users = self.config['xtream_server']['users']
        self.jellyfin_user_id = None
        # Cache for library -> category mapping
        self._movie_libraries = None
        self._series_libraries = None
        self._movie_category_map = {}  # item_id -> category_id
        self._series_category_map = {}  # item_id -> category_id
        self._init_jellyfin_user()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        possible_paths = [
            config_path,
            os.path.join(os.path.dirname(__file__), '..', config_path),
            '/config/config.json'
        ]
        
        config_found = None
        for path in possible_paths:
            if os.path.exists(path):
                config_found = path
                break
        
        if not config_found:
            raise FileNotFoundError(
                f"Config file not found. Tried: {possible_paths}. "
                f"Copy config/config.json.example to config/config.json and configure it."
            )
        
        config_path = config_found
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def _init_jellyfin_user(self):
        """Initialize Jellyfin user ID (uses first user)"""
        try:
            users = self.jellyfin.get_users()
            if users:
                self.jellyfin_user_id = users[0]['Id']
                logger.info(
                    f"Using Jellyfin user: {users[0].get('Name')} "
                    f"({self.jellyfin_user_id})"
                )
                # Build category maps
                self._build_category_maps()
            else:
                logger.error("No users found in Jellyfin")
        except Exception as e:
            logger.error(f"Failed to get Jellyfin users: {str(e)}")

    def _build_category_maps(self):
        """Build mapping of item IDs to their library (category) IDs."""
        try:
            self._movie_category_map.clear()
            self._series_category_map.clear()

            # Get movie libraries
            self._movie_libraries = self.jellyfin.get_movie_libraries(self.jellyfin_user_id)
            for lib in self._movie_libraries:
                lib_id = lib['Id']
                movies = self.jellyfin.get_movies(self.jellyfin_user_id, parent_id=lib_id)
                for movie in movies:
                    self._movie_category_map[movie['Id']] = lib_id
                logger.info(f"{GREEN}  ✓{RESET} {len(movies)} movies → {BOLD}{lib.get('Name')}{RESET} ({lib_id})")

            # Get series libraries
            self._series_libraries = self.jellyfin.get_series_libraries(self.jellyfin_user_id)
            for lib in self._series_libraries:
                lib_id = lib['Id']
                series = self.jellyfin.get_series(self.jellyfin_user_id, parent_id=lib_id)
                for show in series:
                    self._series_category_map[show['Id']] = lib_id
                logger.info(f"{GREEN}  ✓{RESET} {len(series)} series → {BOLD}{lib.get('Name')}{RESET} ({lib_id})")

        except Exception as e:
            logger.error(f"Failed to build category maps: {str(e)}")

    def authenticate(self, username: str, password: str) -> bool:
        return (
            username in self.users and
            self.users[username] == password
        )

    def get_server_info(self, username: str) -> Dict[str, Any]:
        from datetime import datetime
        import time

        return {
            'user_info': {
                'username': username,
                'password': self.users[username],
                'message': 'Welcome to JellyStream',
                'auth': 1,
                'status': 'Active',
                'exp_date': '9999999999',
                'is_trial': '0',
                'active_cons': '0',
                'created_at': str(int(time.time())),
                'max_connections': '1',
                'allowed_output_formats': ['m3u8', 'ts', 'mp4']
            },
            'server_info': {
                'url': self.config['xtream_server'].get(
                    'server_url',
                    'http://localhost:8080'
                ),
                'port': str(self.config['xtream_server']['port']),
                'https_port': '',
                'server_protocol': 'http',
                'rtmp_port': '',
                'timezone': 'UTC',
                'timestamp_now': int(time.time()),
                'time_now': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def get_vod_categories(self) -> List[Dict[str, Any]]:
        if not self.jellyfin_user_id:
            return []

        try:
            if not self._movie_libraries:
                self._movie_libraries = self.jellyfin.get_movie_libraries(self.jellyfin_user_id)
            
            categories = []
            for lib in self._movie_libraries:
                categories.append({
                    'category_id': lib['Id'],
                    'category_name': lib.get('Name', 'Movies'),
                    'parent_id': 0
                })
            
            if not categories:
                categories.append({
                    'category_id': '0',
                    'category_name': 'All Movies',
                    'parent_id': 0
                })
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get VOD categories: {str(e)}")
            return []

    def get_vod_streams(self, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.jellyfin_user_id:
            return []

        try:
            # Refresh category maps on every call to catch new items
            self._build_category_maps()

            # If specific category requested, query that library
            if category_id and category_id != '0':
                movies = self.jellyfin.get_movies(self.jellyfin_user_id, parent_id=category_id)
            else:
                # No category specified - get ALL movies from all libraries
                movies = []
                if not self._movie_libraries:
                    self._movie_libraries = self.jellyfin.get_movie_libraries(self.jellyfin_user_id)
                for lib in self._movie_libraries:
                    lib_movies = self.jellyfin.get_movies(self.jellyfin_user_id, parent_id=lib['Id'])
                    movies.extend(lib_movies)
            
            streams = []
            for movie in movies:
                stream_id = movie['Id']
                container = self._get_container_extension(movie)
                # Use the category map to get the correct category_id
                movie_cat_id = self._movie_category_map.get(stream_id, category_id or '0')
                
                streams.append({
                    'num': int(stream_id.replace('-', '')[:8], 16),
                    'name': movie.get('Name', 'Unknown'),
                    'stream_type': 'movie',
                    'stream_id': stream_id,
                    'stream_icon': self._get_image_url(movie),
                    'rating': movie.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        movie.get('CommunityRating', 0)
                    ),
                    'added': self._parse_date(
                        movie.get('PremiereDate', '')
                    ),
                    'category_id': movie_cat_id,
                    'container_extension': container,
                    'custom_sid': '',
                    'direct_source': ''
                })
            
            return streams
        except Exception as e:
            logger.error(f"Failed to get VOD streams: {str(e)}")
            return []

    def get_vod_info(self, vod_id: str) -> Dict[str, Any]:
        if not self.jellyfin_user_id:
            return {}

        try:
            movie = self.jellyfin.get_item_details(
                self.jellyfin_user_id,
                vod_id
            )
            container = self._get_container_extension(movie)
            movie_cat_id = self._movie_category_map.get(vod_id, '0')
            
            movie_data = {
                'info': {
                    'kinopoisk_url': '',
                    'tmdb_id': movie.get('ProviderIds', {}).get('Tmdb', ''),
                    'name': movie.get('Name', ''),
                    'o_name': movie.get('OriginalTitle', ''),
                    'cover_big': self._get_image_url(movie, 'Primary'),
                    'movie_image': self._get_image_url(movie, 'Backdrop'),
                    'releasedate': movie.get('PremiereDate', ''),
                    'episode_run_time': str(
                        movie.get('RunTimeTicks', 0) // 10000000 // 60
                    ),
                    'youtube_trailer': '',
                    'director': ', '.join(
                        p['Name'] for p in movie.get('People', []) if p.get('Type') == 'Director'
                    ) if movie.get('People') else '',
                    'actors': ', '.join(
                        p['Name'] for p in movie.get('People', []) if p.get('Type') == 'Actor'
                    ) if movie.get('People') else '',
                    'cast': ', '.join(
                        p['Name'] for p in movie.get('People', [])
                    ) if movie.get('People') else '',
                    'description': movie.get('Overview', ''),
                    'plot': movie.get('Overview', ''),
                    'age': movie.get('OfficialRating', ''),
                    'mpaa_rating': movie.get('OfficialRating', ''),
                    'rating_5based': self._convert_rating_to_5(
                        movie.get('CommunityRating', 0)
                    ),
                    'rating': movie.get('CommunityRating', 0),
                    'country': '',
                    'genre': ', '.join(movie.get('Genres', [])),
                    'duration_secs': str(
                        movie.get('RunTimeTicks', 0) // 10000000
                    ),
                    'duration': self._format_duration(
                        movie.get('RunTimeTicks', 0)
                    ),
                    'video': self._get_video_info(movie),
                    'audio': self._get_audio_info(movie),
                    'bitrate': self._get_bitrate(movie)
                },
                'movie_data': {
                    'stream_id': vod_id,
                    'name': movie.get('Name', ''),
                    'added': self._parse_date(
                        movie.get('PremiereDate', '')
                    ),
                    'category_id': movie_cat_id,
                    'container_extension': container,
                    'custom_sid': '',
                    'direct_source': ''
                }
            }
            
            return movie_data
        except Exception as e:
            logger.error(f"Failed to get VOD info: {str(e)}")
            return {}

    def get_series_categories(self) -> List[Dict[str, Any]]:
        if not self.jellyfin_user_id:
            return []

        try:
            if not self._series_libraries:
                self._series_libraries = self.jellyfin.get_series_libraries(self.jellyfin_user_id)
            
            categories = []
            for lib in self._series_libraries:
                categories.append({
                    'category_id': lib['Id'],
                    'category_name': lib.get('Name', 'TV Shows'),
                    'parent_id': 0
                })
            
            if not categories:
                categories.append({
                    'category_id': '0',
                    'category_name': 'All Series',
                    'parent_id': 0
                })
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get series categories: {str(e)}")
            return []

    def get_series(self, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.jellyfin_user_id:
            return []

        try:
            # Refresh category maps on every call to catch new items
            self._build_category_maps()

            if category_id and category_id != '0':
                series_list = self.jellyfin.get_series(self.jellyfin_user_id, parent_id=category_id)
            else:
                series_list = []
                if not self._series_libraries:
                    self._series_libraries = self.jellyfin.get_series_libraries(self.jellyfin_user_id)
                for lib in self._series_libraries:
                    lib_series = self.jellyfin.get_series(self.jellyfin_user_id, parent_id=lib['Id'])
                    series_list.extend(lib_series)
            
            series = []
            for show in series_list:
                series_id = show['Id']
                show_cat_id = self._series_category_map.get(series_id, category_id or '0')
                
                series.append({
                    'num': int(series_id.replace('-', '')[:8], 16),
                    'name': show.get('Name', 'Unknown'),
                    'series_id': series_id,
                    'cover': self._get_image_url(show),
                    'plot': show.get('Overview', ''),
                    'cast': '',
                    'director': '',
                    'genre': ', '.join(show.get('Genres', [])),
                    'releaseDate': show.get('PremiereDate', ''),
                    'last_modified': self._parse_date(
                        show.get('PremiereDate', '')
                    ),
                    'rating': show.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        show.get('CommunityRating', 0)
                    ),
                    'backdrop_path': [self._get_image_url(show, 'Backdrop')],
                    'youtube_trailer': '',
                    'episode_run_time': '',
                    'category_id': show_cat_id
                })
            
            return series
        except Exception as e:
            logger.error(f"Failed to get series: {str(e)}")
            return []

    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        if not self.jellyfin_user_id:
            return {}

        try:
            series_data = self.jellyfin.get_series_info(
                self.jellyfin_user_id,
                series_id
            )
            
            series_info = series_data['info']
            episodes = series_data['episodes']
            
            series_cat_id = self._series_category_map.get(series_id, '0')
            
            seasons = []
            episodes_dict = {}
            
            for season_num, season_episodes in episodes.items():
                if not season_episodes:
                    continue
                
                season_list = []
                for episode in season_episodes:
                    episode_num = episode.get('IndexNumber', 0)
                    container = self._get_container_extension(episode)
                    
                    episode_data = {
                        'id': episode['Id'],
                        'episode_num': episode_num,
                        'title': episode.get('Name', ''),
                        'container_extension': container,
                        'info': {
                            'name': episode.get('Name', ''),
                            'releasedate': episode.get('PremiereDate', ''),
                            'plot': episode.get('Overview', ''),
                            'duration_secs': str(
                                episode.get('RunTimeTicks', 0) // 10000000
                            ),
                            'duration': self._format_duration(
                                episode.get('RunTimeTicks', 0)
                            ),
                            'video': self._get_video_info(episode),
                            'audio': self._get_audio_info(episode),
                            'bitrate': self._get_bitrate(episode),
                            'rating': episode.get('CommunityRating', 0)
                        },
                        'custom_sid': '',
                        'added': self._parse_date(
                            episode.get('PremiereDate', '')
                        ),
                        'season': int(season_num),
                        'direct_source': ''
                    }
                    season_list.append(episode_data)
                
                if season_list:
                    episodes_dict[season_num] = season_list
                    seasons.append({
                        'season_number': int(season_num),
                        'name': f'Season {season_num}',
                        'episode_count': len(season_list),
                        'overview': '',
                        'cover': self._get_image_url(series_info),
                        'cover_big': self._get_image_url(
                            series_info,
                            'Primary'
                        ),
                    })
            
            result = {
                'seasons': seasons,
                'info': {
                    'name': series_info.get('Name', ''),
                    'cover': self._get_image_url(series_info),
                    'plot': series_info.get('Overview', ''),
                    'cast': '',
                    'director': '',
                    'genre': ', '.join(series_info.get('Genres', [])),
                    'releaseDate': series_info.get('PremiereDate', ''),
                    'last_modified': self._parse_date(
                        series_info.get('PremiereDate', '')
                    ),
                    'rating': series_info.get('CommunityRating', 0),
                    'rating_5based': self._convert_rating_to_5(
                        series_info.get('CommunityRating', 0)
                    ),
                    'backdrop_path': [
                        self._get_image_url(series_info, 'Backdrop')
                    ],
                    'youtube_trailer': '',
                    'episode_run_time': '',
                    'category_id': series_cat_id
                },
                'episodes': episodes_dict
            }
            
            return result
        except Exception as e:
            logger.error(f"Failed to get series info: {str(e)}")
            return {}

    def _get_container_extension(self, item: Dict[str, Any]) -> str:
        media_sources = item.get('MediaSources', [])
        if media_sources:
            container = media_sources[0].get('Container', 'mp4')
            return container.lower()
        return 'mp4'

    def _get_image_url(self, item: Dict[str, Any], image_type: str = 'Primary') -> str:
        item_id = item.get('Id', '')
        if not item_id:
            return ''
        return (
            f"{self.jellyfin.server_url}/Items/{item_id}/Images/{image_type}"
            f"?api_key={self.jellyfin.api_key}"
        )

    def _convert_rating_to_5(self, rating: float) -> float:
        return round(rating / 2, 1) if rating else 0

    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return ''
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return str(int(dt.timestamp()))
        except Exception:
            return ''

    def _format_duration(self, ticks: int) -> str:
        seconds = ticks // 10000000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_video_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        media_sources = item.get('MediaSources', [])
        if not media_sources:
            return {}
        video_streams = [
            s for s in media_sources[0].get('MediaStreams', [])
            if s.get('Type') == 'Video'
        ]
        if not video_streams:
            return {}
        video = video_streams[0]
        return {
            'codec': video.get('Codec', ''),
            'width': video.get('Width', 0),
            'height': video.get('Height', 0),
            'bitrate': video.get('BitRate', 0)
        }

    def _get_audio_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        media_sources = item.get('MediaSources', [])
        if not media_sources:
            return {}
        audio_streams = [
            s for s in media_sources[0].get('MediaStreams', [])
            if s.get('Type') == 'Audio'
        ]
        if not audio_streams:
            return {}
        audio = audio_streams[0]
        return {
            'codec': audio.get('Codec', ''),
            'channels': audio.get('Channels', 0),
            'bitrate': audio.get('BitRate', 0)
        }

    def _get_bitrate(self, item: Dict[str, Any]) -> int:
        media_sources = item.get('MediaSources', [])
        if media_sources:
            return media_sources[0].get('Bitrate', 0)
        return 0


# Initialize server
server = XtreamServer()


@app.route('/player_api.php', methods=['GET'])
def player_api():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')

    if not username or not password:
        logger.warning("API request missing credentials")
        return jsonify({'error': 'Missing credentials'}), 401

    if not server.authenticate(username, password):
        logger.warning(f"Authentication failed for user: {username}")
        return jsonify({'error': 'Invalid credentials'}), 401

    logger.info(f"[{username}] API request: action={action}")

    if not action:
        return jsonify(server.get_server_info(username))

    if action == 'get_vod_categories':
        result = server.get_vod_categories()
        logger.info(f"[{username}] Returning {len(result)} VOD categories")
        return jsonify(result)

    if action == 'get_vod_streams':
        category_id = request.args.get('category_id')
        result = server.get_vod_streams(category_id)
        logger.info(f"[{username}] Returning {len(result)} VOD streams (category={category_id or 'all'})")
        return jsonify(result)

    if action == 'get_vod_info':
        vod_id = request.args.get('vod_id')
        if not vod_id:
            return jsonify({'error': 'Missing vod_id'}), 400
        result = server.get_vod_info(vod_id)
        logger.info(f"[{username}] VOD info for {vod_id[:8]}...")
        return jsonify(result)

    if action == 'get_series_categories':
        result = server.get_series_categories()
        logger.info(f"[{username}] Returning {len(result)} series categories")
        return jsonify(result)

    if action == 'get_series':
        category_id = request.args.get('category_id')
        result = server.get_series(category_id)
        logger.info(f"[{username}] Returning {len(result)} series (category={category_id or 'all'})")
        return jsonify(result)

    if action == 'get_series_info':
        series_id = request.args.get('series_id')
        if not series_id:
            return jsonify({'error': 'Missing series_id'}), 400
        result = server.get_series_info(series_id)
        logger.info(f"[{username}] Series info for {series_id[:8]}...")
        return jsonify(result)

    if action == 'get_live_categories':
        return jsonify([])

    if action == 'get_live_streams':
        return jsonify([])

    logger.warning(f"[{username}] Unknown action: {action}")
    return jsonify({'error': f'Unknown action: {action}'}), 400


@app.route('/movie/<username>/<password>/<stream_id>.<container>')
def stream_movie(username, password, stream_id, container):
    if not server.authenticate(username, password):
        logger.warning(f"Stream auth failed for user: {username}")
        return jsonify({'error': 'Invalid credentials'}), 401
    logger.info(f"[{username}] Movie stream: {stream_id[:8]}... ({container})")
    if container == 'm3u8':
        stream_url = server.jellyfin.get_hls_stream_url(stream_id)
    else:
        stream_url = server.jellyfin.get_stream_url(stream_id, container)
    return Response(status=302, headers={'Location': stream_url})


@app.route('/series/<username>/<password>/<stream_id>.<container>')
def stream_episode(username, password, stream_id, container):
    if not server.authenticate(username, password):
        logger.warning(f"Stream auth failed for user: {username}")
        return jsonify({'error': 'Invalid credentials'}), 401
    logger.info(f"[{username}] Episode stream: {stream_id[:8]}... ({container})")
    if container == 'm3u8':
        stream_url = server.jellyfin.get_hls_stream_url(stream_id)
    else:
        stream_url = server.jellyfin.get_stream_url(stream_id, container)
    return Response(status=302, headers={'Location': stream_url})


def main():
    host = server.config['xtream_server']['host']
    port = server.config['xtream_server']['port']
    
    # Startup banner
    print()
    print(f"{CYAN}╔═══════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║{RESET}  {BOLD}JellyStream by Techsuchti{RESET}                  {CYAN}║{RESET}")
    print(f"{CYAN}║{RESET}  https://github.com/Techsuchti/JellyStream  {CYAN}║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════╝{RESET}")
    print()
    logger.info(f"{GREEN}Starting JellyStream on {host}:{port}{RESET}")
    logger.info(f"{GREEN}JellyStream is ready ✓{RESET}")
    
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()