# JellyStream

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/techsuchti)

A bridge server that exposes Jellyfin's movie and series library through the Xtream Codes API, allowing IPTV apps (like Dispatcharr, TiviMate, etc.) to access Jellyfin content.

## Features

- 🎬 **Movies & Series** — Full VOD and series support via Xtream Codes API
- 📂 **Dynamic Categories** — Automatically maps Jellyfin libraries to IPTV categories
- 🔐 **Authentication** — Username/password auth for both Jellyfin and Xtream clients
- 🔄 **Auto-refresh** — Category mappings rebuilt on every request (catches new content instantly)
- 🏷️ **Library Detection** — Detects libraries without `CollectionType` by probing content (movies vs series)
- 🖼️ **Thumbnails** — Exposes Jellyfin artwork as stream icons

## Quick Start

### 1. Configure

```bash
cp config/config.json.example config/config.json
```

Edit `config/config.json`:

```json
{
  "jellyfin": {
    "server_url": "http://your-jellyfin-server:8096",
    "username": "your-bridge-user",
    "password": "your-bridge-password"
  },
  "xtream_server": {
    "host": "0.0.0.0",
    "port": 7777,
    "server_url": "http://your-server:7777",
    "users": {
      "xtream_user": "xtream_password"
    }
  }
}
```

### 2. Run with Docker

```bash
docker run -d \
  --name jellstream \
  --network host \
  -v /path/to/config:/app/config \
  ghcr.io/techsuchti/jellstream:latest
```

### 3. Run manually

```bash
pip install -r requirements.txt
./start_server.sh
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/player_api.php` | Main Xtream Codes API endpoint |
| `/movie/<user>/<pass>/<id>.<ext>` | Movie stream redirect |
| `/series/<user>/<pass>/<id>.<ext>` | Episode stream redirect |

### Xtream Actions

- `get_vod_categories` — List movie categories (from Jellyfin libraries)
- `get_vod_streams` — List movies (optionally filtered by category)
- `get_vod_info` — Movie details
- `get_series_categories` — List series categories
- `get_series` — List series
- `get_series_info` — Series details with episodes

## How It Works

1. Bridge authenticates with Jellyfin using username/password
2. On each API request, it queries Jellyfin libraries and builds category maps
3. Jellyfin library UUIDs become Xtream category IDs
4. Movies/series are mapped to their parent library as categories
5. Stream URLs redirect to Jellyfin's direct stream endpoint

## Jellyfin Setup

Create a dedicated Jellyfin user (e.g., "bridge") with access to all libraries you want to expose. The bridge will automatically detect:

- Libraries with `CollectionType: "movies"` → VOD categories
- Libraries with `CollectionType: "tvshows"` → Series categories
- Libraries with `CollectionType: null` → Probed for content type (movies or series)

## License

MIT