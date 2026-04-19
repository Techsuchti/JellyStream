# 📺 Dispatcharr Integration

Dispatcharr is an IPTV management platform that can consume the Xtream Codes API.

## 1. Add M3U/XC Source

1. Open Dispatcharr → **Settings** → **M3U Accounts** → **Add Account**
2. **Account Type:** Xtream Codes
3. **Name:** Jellyfin (or any name you prefer)
4. **URL:** `http://YOUR_BRIDGE_IP:7777`
5. **Username:** Your Xtream username from `config.json`
6. **Password:** Your Xtream password from `config.json`

## 2. Import Categories

After adding the account, Dispatcharr will automatically discover:

- **VOD Categories** — Your Jellyfin movie libraries (Filme, Horror, Kinder, etc.)
- **Series Categories** — Your Jellyfin TV show libraries
- **VOD Streams** — All movies from each library
- **Series** — All TV shows with episode listings

## 3. Refresh Content

To update content (e.g., after adding new movies to Jellyfin):

### Via UI
- M3U Accounts → Click **Refresh** on your Jellyfin account

### Via Django ORM (advanced)
```bash
docker exec -it Dispatcharr python3 -c '
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dispatcharr.settings")
django.setup()
from apps.m3u.tasks import refresh_single_m3u_account
refresh_single_m3u_account(YOUR_ACCOUNT_ID)
'
```

### Clear and Re-import (nuclear option)
```bash
docker exec -it Dispatcharr python3 -c '
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dispatcharr.settings")
django.setup()
from apps.vod.models import Movie, Series, VODCategory
Movie.objects.all().delete()
Series.objects.all().delete()
VODCategory.objects.all().delete()
from apps.m3u.tasks import refresh_single_m3u_account
refresh_single_m3u_account(YOUR_ACCOUNT_ID)
'
```

## 4. Streaming

When a user clicks play in Dispatcharr:

1. Dispatcharr requests the stream URL from the bridge
2. The bridge redirects to Jellyfin's direct stream URL
3. The client plays the stream directly from Jellyfin

### Supported Formats
- **MP4** — Direct play (most reliable)
- **MKV** — May require transcoding in Jellyfin
- **HLS** (`.m3u8`) — Available for clients that support it

## 5. Troubleshooting

| Problem | Solution |
|---------|----------|
| Categories show but 0 content | Bridge not mapping categories correctly — check bridge logs |
| Content in "Uncategorized" | Bridge `category_id` mismatch — restart bridge and re-import |
| Stream won't play | Check Jellyfin network access from client device |
| New movies not appearing | Trigger a refresh in Dispatcharr |
| Bridge shows 0 categories | Check Jellyfin user has library access |