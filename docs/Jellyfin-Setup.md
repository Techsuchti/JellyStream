# 🎬 Jellyfin Setup

The bridge needs a dedicated Jellyfin user to access your media library.

## 1. Create a Bridge User

1. Open Jellyfin Dashboard → **Users** → **Add User**
2. Set a username (e.g., `bridge`) and a strong password
3. **Important:** Under **Library Access**, make sure the user can access all libraries you want to expose
4. Disable any unnecessary permissions (remote access, administration, etc.)

## 2. Verify Access

Open this URL in a browser to test authentication:

```
http://YOUR_JELLYFIN:8096/Users/AuthenticateByName
```

With headers:
```
X-Emby-Authorization: MediaBrowser Client="JellyStream", Device="Bridge", DeviceId="xtream-bridge", Version="1.0"
Content-Type: application/json
```

Body:
```json
{"Username": "bridge", "Pw": "your-password"}
```

You should get a JSON response with an `AccessToken` and `User` object.

## 3. Library Detection

The bridge automatically detects your Jellyfin libraries:

| Jellyfin Library Type | Becomes |
|----------------------|---------|
| `movies` | VOD Category |
| `tvshows` | Series Category |
| `null` (no type set) | Auto-detected by probing content |

### Libraries Without CollectionType

Some Jellyfin libraries have no `CollectionType` set (e.g., "Kinder", "TV_Aufnahmen"). The bridge handles these by:

1. Querying each untyped library for `Movie` items (limit 1)
2. If movies found → VOD category
3. If no movies, checking for `Series` items
4. If series found → Series category

This means **any** Jellyfin library will be correctly categorized, regardless of its configured type.

## 4. Category Mapping

Jellyfin library UUIDs become Xtream category IDs:

| Jellyfin Library | UUID (Category ID) |
|-----------------|-------------------|
| Filme | `7a2175bccb1f1a94152cbd2b2bae8f6d` |
| Horror | `fc3d996041ae3e1fc148af30b88380f3` |
| Kinder | `d63fa61d249a0135dc028fcdd0c1271e` |

These UUIDs are stable — they won't change unless you delete and recreate the library.

## 5. Adding New Content

When you add new movies/series to Jellyfin:

1. They appear automatically in the next API request (no restart needed)
2. The bridge rebuilds category maps on **every** request
3. Dispatcharr will pick up new content on its next refresh cycle

If content doesn't appear in your IPTV app, trigger a manual refresh in Dispatcharr.