# 📡 API Reference

The bridge implements the Xtream Codes API standard.

## Authentication

All endpoints require `username` and `password` query parameters:

```
?username=YOUR_USER&password=YOUR_PASS
```

## Base URL

```
http://YOUR_BRIDGE_IP:7777/player_api.php
```

## Endpoints

### Server Info

```
GET /player_api.php?username=X&password=X
```

Returns server info and user account details.

### VOD Categories

```
GET /player_api.php?username=X&password=X&action=get_vod_categories
```

Returns movie categories (mapped from Jellyfin libraries).

**Response:**
```json
[
  {
    "category_id": "7a2175bccb1f1a94152cbd2b2bae8f6d",
    "category_name": "Filme",
    "parent_id": 0
  }
]
```

### VOD Streams (All Movies)

```
GET /player_api.php?username=X&password=X&action=get_vod_streams
```

Returns all movies across all categories.

### VOD Streams (By Category)

```
GET /player_api.php?username=X&password=X&action=get_vod_streams&category_id=LIBRARY_UUID
```

Returns movies from a specific Jellyfin library.

**Response:**
```json
[
  {
    "num": 3157827358,
    "name": "Movie Title",
    "stream_type": "movie",
    "stream_id": "abc123def456",
    "stream_icon": "http://jellyfin:8096/Items/abc123/Images/Primary?api_key=...",
    "rating": 7.5,
    "rating_5based": 3.8,
    "added": "1700000000",
    "category_id": "7a2175bccb1f1a94152cbd2b2bae8f6d",
    "container_extension": "mp4"
  }
]
```

### VOD Info (Movie Details)

```
GET /player_api.php?username=X&password=X&action=get_vod_info&vod_id=ITEM_ID
```

Returns detailed movie information including plot, cast, genres, runtime, etc.

### Series Categories

```
GET /player_api.php?username=X&password=X&action=get_series_categories
```

### Series List

```
GET /player_api.php?username=X&password=X&action=get_series
GET /player_api.php?username=X&password=X&action=get_series&category_id=LIBRARY_UUID
```

### Series Info

```
GET /player_api.php?username=X&password=X&action=get_series_info&series_id=SERIES_ID
```

### Stream URLs

```
GET /movie/USERNAME/PASSWORD/STREAM_ID.mp4
GET /series/USERNAME/PASSWORD/STREAM_ID.mp4
```

These redirect (302) to Jellyfin's direct stream URL.

### HLS Streams

```
GET /movie/USERNAME/PASSWORD/STREAM_ID.m3u8
```

Returns an HLS playlist URL from Jellyfin.

### Empty Endpoints

```
GET /player_api.php?username=X&password=X&action=get_live_categories
GET /player_api.php?username=X&password=X&action=get_live_streams
```

Returns empty arrays `[]` (live TV not supported).