# ⚙️ Configuration

The bridge is configured via `config/config.json`.

## Full Configuration

```json
{
  "jellyfin": {
    "server_url": "http://192.168.1.100:8096",
    "username": "bridge",
    "password": "your-secure-password"
  },
  "xtream_server": {
    "host": "0.0.0.0",
    "port": 7777,
    "server_url": "http://your-server:7777",
    "users": {
      "user1": "password1",
      "user2": "password2"
    }
  }
}
```

## Jellyfin Section

| Field | Required | Description |
|-------|----------|-------------|
| `server_url` | ✅ | URL of your Jellyfin server (include port if non-default) |
| `username` | ✅ | Jellyfin user for the bridge (see [[Jellyfin Setup]]) |
| `password` | ✅ | Password for the Jellyfin user |
| `api_key` | ❌ | Alternative: use an API key instead of username/password |

> **Tip:** Use `username`/`password` instead of `api_key` — session tokens from API keys can expire.

## Xtream Server Section

| Field | Required | Description |
|-------|----------|-------------|
| `host` | ✅ | Bind address (`0.0.0.0` for all interfaces) |
| `port` | ✅ | Port to listen on (default: `7777`) |
| `server_url` | ✅ | Public URL of this bridge (used in stream redirects) |
| `users` | ✅ | Dictionary of Xtream username → password pairs |

### Adding Multiple Users

```json
"users": {
  "living_room": "secure_pass_1",
  "bedroom": "secure_pass_2",
  "phone": "secure_pass_3"
}
```

Each user has full access to all content — per-library restrictions are not yet supported.

## Environment Variables

You can also set the config path via environment variable:

```bash
export BRIDGE_CONFIG=/app/config/config.json
```

## Port Considerations

- Default port is `7777` — make sure it doesn't conflict with other services
- If using a reverse proxy (nginx, Caddy), set `server_url` to your public URL
- The bridge needs to reach Jellyfin directly, so `server_url` in the `jellyfin` section should use the internal address