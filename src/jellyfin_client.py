"""
Jellyfin API Client for accessing Movies and TV Series.
Supports both API key and username/password authentication.
"""
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class JellyfinClient:
    """Client for interacting with Jellyfin API"""

    def __init__(self, server_url: str, api_key: str = None, username: str = None, password: str = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        self.user_id = None
        self.session = requests.Session()

        # If no API key but username/password provided, authenticate
        if not self.api_key and self.username:
            self._authenticate()

        if self.api_key:
            self.session.headers.update({
                'X-Emby-Token': self.api_key,
                'Accept': 'application/json'
            })
        else:
            self.session.headers.update({
                'Accept': 'application/json'
            })

    def _authenticate(self):
        """Authenticate with Jellyfin using username/password to get API key."""
        try:
            auth_headers = {
                'X-Emby-Authorization': f'MediaBrowser Client="JellyStream", Device="Bridge", DeviceId="xtream-bridge", Version="1.0"',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.post(
                f'{self.server_url}/Users/AuthenticateByName',
                headers=auth_headers,
                json={'Username': self.username, 'Pw': self.password},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.api_key = data.get('AccessToken')
            self.user_id = data.get('User', {}).get('Id')
            logger.info(f'Jellyfin auth successful for user: {self.username}, user_id: {self.user_id}')
        except Exception as e:
            logger.error(f'Jellyfin authentication failed: {e}')
            raise

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.server_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Jellyfin API request failed: {str(e)}")
            raise

    def get_users(self) -> List[Dict[str, Any]]:
        return self._make_request('Users')

    def get_items(self, user_id: str, include_item_types: Optional[str] = None,
                  parent_id: Optional[str] = None, recursive: bool = True,
                  fields: Optional[str] = None) -> Dict[str, Any]:
        params = {'UserId': user_id, 'Recursive': str(recursive).lower()}
        if include_item_types:
            params['IncludeItemTypes'] = include_item_types
        if parent_id:
            params['ParentId'] = parent_id
        if fields:
            params['Fields'] = fields
        return self._make_request('Items', params)

    def get_movie_libraries(self, user_id: str) -> List[Dict[str, Any]]:
        params = {'UserId': user_id, 'IncludeItemTypes': 'CollectionFolder'}
        response = self._make_request('Items', params)
        result = []
        for item in response.get('Items', []):
            ct = item.get('CollectionType')
            if ct == 'movies':
                result.append(item)
            elif ct is None:
                # Check if library contains movies (query with parentId, limit 1)
                try:
                    check = self._make_request('Items', {
                        'UserId': user_id,
                        'ParentId': item['Id'],
                        'IncludeItemTypes': 'Movie',
                        'Recursive': 'true',
                        'Limit': 1
                    })
                    if check.get('Items'):
                        result.append(item)
                except Exception:
                    pass
        return result

    def get_series_libraries(self, user_id: str) -> List[Dict[str, Any]]:
        params = {'UserId': user_id, 'IncludeItemTypes': 'CollectionFolder'}
        response = self._make_request('Items', params)
        result = []
        for item in response.get('Items', []):
            ct = item.get('CollectionType')
            if ct == 'tvshows':
                result.append(item)
            elif ct is None:
                # Check if library contains series (query with parentId, limit 1)
                try:
                    check = self._make_request('Items', {
                        'UserId': user_id,
                        'ParentId': item['Id'],
                        'IncludeItemTypes': 'Series',
                        'Recursive': 'true',
                        'Limit': 1
                    })
                    if check.get('Items'):
                        result.append(item)
                except Exception:
                    pass
        return result

    def get_movies(self, user_id: str, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'Movie',
            'Recursive': 'true',
            'Fields': 'Path,MediaSources,ProviderIds,Overview,Genres,ProductionYear,PremiereDate,CommunityRating,OfficialRating'
        }
        if parent_id:
            params['ParentId'] = parent_id
        response = self._make_request('Items', params)
        return response.get('Items', [])

    def get_series(self, user_id: str, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {
            'UserId': user_id,
            'IncludeItemTypes': 'Series',
            'Recursive': 'true',
            'Fields': 'Path,ProviderIds,Overview,Genres,ProductionYear,PremiereDate,CommunityRating,OfficialRating'
        }
        if parent_id:
            params['ParentId'] = parent_id
        response = self._make_request('Items', params)
        return response.get('Items', [])

    def get_series_info(self, user_id: str, series_id: str) -> Dict[str, Any]:
        series = self._make_request(f'Users/{user_id}/Items/{series_id}')
        seasons_response = self._make_request(f'Shows/{series_id}/Seasons', {'UserId': user_id, 'Fields': 'Overview'})
        seasons = seasons_response.get('Items', [])
        episodes_by_season = {}
        for season in seasons:
            season_id = season.get('Id')
            episodes_response = self._make_request(
                f'Shows/{series_id}/Episodes',
                {'UserId': user_id, 'SeasonId': season_id, 'Fields': 'Path,MediaSources,Overview,ProductionYear,PremiereDate'}
            )
            season_number = season.get('IndexNumber', 0)
            episodes_by_season[str(season_number)] = episodes_response.get('Items', [])
        return {'info': series, 'seasons': seasons, 'episodes': episodes_by_season}

    def get_item_details(self, user_id: str, item_id: str) -> Dict[str, Any]:
        return self._make_request(f'Users/{user_id}/Items/{item_id}')

    def get_stream_url(self, item_id: str, container: str = 'mp4') -> str:
        return f"{self.server_url}/Videos/{item_id}/stream.{container}?api_key={self.api_key}&Static=true"

    def get_hls_stream_url(self, item_id: str, max_streaming_bitrate: int = 120000000,
                           video_codec: str = 'h264,hevc', audio_codec: str = 'aac,mp3,ac3,eac3') -> str:
        params = [
            f"api_key={self.api_key}",
            f"MaxStreamingBitrate={max_streaming_bitrate}",
            f"VideoCodec={video_codec}",
            f"AudioCodec={audio_codec}",
            "TranscodingMaxAudioChannels=2",
            "RequireAvc=false",
            "SegmentContainer=ts",
            "BreakOnNonKeyFrames=true",
            "h264-profile=high,main,baseline,constrainedbaseline",
            "h264-level=51",
            "TranscodeReasons=",
        ]
        return f"{self.server_url}/Videos/{item_id}/master.m3u8?{'&'.join(params)}"

    def close(self):
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.debug(f"Error closing Jellyfin session: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        self.close()