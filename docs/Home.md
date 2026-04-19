# 🏠 Home

**JellyStream** exposes your Jellyfin media library through the Xtream Codes API, making it accessible in IPTV apps like Dispatcharr, TiviMate, IPTV Smarters, and more.

## ✨ Features

- 🎬 Full VOD (movies) and Series support via Xtream Codes API
- 📂 Dynamic category mapping from Jellyfin libraries
- 🔐 Username/password authentication for both Jellyfin and Xtream clients
- 🔄 Auto-refresh — category mappings rebuilt on every request (catches new content instantly)
- 🏷️ Smart library detection — detects libraries without `CollectionType` by probing content
- 🖼️ Artwork support — exposes Jellyfin thumbnails as stream icons
- 🐳 Docker-ready with simple configuration

## 📖 Documentation

| Page | Description |
|------|-------------|
| [[Installation]] | Install via Docker or manual setup |
| [[Configuration]] | Configure the bridge for your setup |
| [[Jellyfin Setup]] | Prepare Jellyfin for the bridge |
| [[Dispatcharr Integration]] | Connect Dispatcharr to the bridge |
| [[API Reference]] | Xtream Codes API endpoints |
| [[Troubleshooting]] | Common issues and fixes |

## Quick Start

```bash
docker run -d \
  --name jellstream \
  --network host \
  -v /path/to/config:/app/config \
  ghcr.io/techsuchti/jellstream:v1.1.4
```

See [[Installation]] for detailed instructions.
