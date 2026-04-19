# 📦 Installation

## Docker (Recommended)

### 1. Create config directory

```bash
mkdir -p /path/to/config
```

### 2. Create configuration file

```bash
cp config.json.example /path/to/config/config.json
```

Edit the config file — see [[Configuration]] for details.

### 3. Run the container

```bash
docker run -d \
  --name jellstream \
  --network host \
  --restart unless-stopped \
  -v /path/to/config:/app/config \
  ghcr.io/techsuchti/jellstream:latest
```

> **Note:** `--network host` is recommended so the bridge can reach Jellyfin on your local network. If you use bridge networking, make sure the container can resolve your Jellyfin server.

### 4. Verify

Open `http://your-server:7777/player_api.php?username=YOUR_USER&password=YOUR_PASS` in a browser. You should see a JSON response with server info.

## Docker Compose

```yaml
version: "3"
services:
  jellstream:
    image: ghcr.io/techsuchti/jellstream:latest
    container_name: jellstream
    network_mode: host
    restart: unless-stopped
    volumes:
      - /path/to/config:/app/config
```

## Manual Installation

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
git clone https://github.com/Techsuchti/jellstream.git
cd jellstream
pip install -r requirements.txt
cp config/config.json.example config/config.json
# Edit config/config.json
./start_server.sh
```

### Systemd Service (Optional)

Create `/etc/systemd/system/jellstream.service`:

```ini
[Unit]
Description=Jellyfin Xtream Bridge
After=network.target

[Service]
Type=simple
User=bridge
WorkingDirectory=/opt/jellstream
ExecStart=/opt/jellstream/start_server.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now jellstream
```