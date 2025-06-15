# 07‑Phase 03 – Video Download & Caching

## Goal
Implement the **download_worker** to:

1. Use `yt-dlp` to download each queued video at ≤ 1440p into the cache dir.
2. Name files using `<song>_<artist>_<id>.mp4` (metadata filled later).
3. Set modification date to now.
4. Skip if file already exists; update timestamp if re‑downloaded.

Include cleanup logic:
- Remove obsolete files (IDs not in playlist & not current video).
- Delete leftover `.part` files.

## Commit
Suggested commit message:  
> *"Add download worker and cache cleanup logic."*