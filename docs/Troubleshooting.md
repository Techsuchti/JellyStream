# 🔧 Troubleshooting

## Bridge Shows 0 Categories

**Cause:** Jellyfin user doesn't have access to any libraries.

**Fix:**
1. Open Jellyfin Dashboard → Users → Your bridge user
2. Check **Library Access** — make sure at least one library is accessible
3. Restart the bridge container

## Movies Show as "Uncategorized"

**Cause:** The bridge couldn't map movies to their Jellyfin library.

**Fix:**
1. Restart the bridge — category maps are rebuilt on every request
2. If still uncategorized, check that your Jellyfin libraries have a `CollectionType` set (`movies`, `tvshows`, or `null`)
3. Re-import in Dispatcharr (clear old data first)

## Bridge Container Keeps Restarting

**Cause:** Usually a config error or Jellyfin unreachable.

**Fix:**
```bash
# Check logs
docker logs jellstream

# Common issues:
# - "config/config.json not found" → mount config volume correctly
# - "Jellyfin authentication failed" → check username/password
# - "Connection refused" → check Jellyfin URL and network
```

## Stream Won't Play

**Possible causes:**

1. **Client can't reach Jellyfin** — The stream URL contains your internal Jellyfin IP. Make sure the client device can reach it.
2. **Transcoding required** — Some formats need Jellyfin transcoding. Make sure Jellyfin has transcoding enabled.
3. **Auth token expired** — Restart the bridge to get a fresh token.

**Fix for external access:** Use a reverse proxy (nginx/Caddy) in front of Jellyfin and set `server_url` in the bridge config to your public domain.

## New Content Not Appearing

The bridge rebuilds category maps on every request, so new content should appear automatically. If it doesn't:

1. **In Dispatcharr:** Trigger a manual refresh of the M3U account
2. **In other apps:** Restart the app or wait for the next EPG refresh cycle
3. **Nuclear option:** Clear all VOD data in Dispatcharr and re-import

## Port 7777 Already in Use

Change the port in `config.json`:

```json
"xtream_server": {
    "port": 8080,
    ...
}
```

Then restart the container.

## Jellyfin Library Not Detected

Libraries with `CollectionType: null` are probed automatically. If a library still doesn't appear:

1. Check if the library contains any items (empty libraries are skipped)
2. Make sure the bridge user has access to the library
3. Check the bridge logs for errors during `_build_category_maps()`

## Docker Networking Issues

If the bridge can't reach Jellyfin:

```bash
# Test connectivity from inside the container
docker exec -it jellstream curl http://JELLYFIN_IP:8096/Health
```

With `--network host`, the container shares the host's network stack and can reach any local service.

## Reset Everything

```bash
# Stop and remove the container
docker stop jellstream
docker rm jellstream

# Delete config
rm -rf /path/to/config/config.json

# Re-create
docker run -d --name jellstream --network host \
  -v /path/to/config:/app/config \
  ghcr.io/techsuchti/jellstream:latest
```