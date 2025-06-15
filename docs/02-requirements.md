# 02‑Requirements (Functional Spec)

This file lists **all features** the final script must implement.  
It is authoritative; later Phase prompts reference this spec.

## Dependencies
- Auto‑download & update **yt‑dlp** and **FFmpeg** into `<cache_dir>/tools` (background thread).  
- Retry on failure; set `tools_ready` flag when verified.

## Playlist Synchronisation
1. Trigger **only** at startup and via *Sync Playlist Now* button.  
2. **NO PERIODIC SYNC** - Script runs on slow LTE internet, sync only on demand.
3. Process videos **one‑by‑one**: download → fingerprint → normalise → rename.  
4. Remove local files whose IDs left the playlist (skip currently playing).

## Caching & File Management
- Store videos in user‑configurable cache dir.  
- Sanitise filenames: `<song>_<artist>_<id>_normalized.mp4`.  
- Retain only newest duplicate; clean temp `.part` files.

## Metadata Retrieval
- Primary: **AcoustID** (`M6o6ia3dKu`).  
- Fallback: parse YouTube title; log transformation.

## Playback Logic
- Scene name == script filename (e.g. `ytfast`).  
- Media Source `video`, Text Source `title`.  
- Random no‑repeat playback; handle stop button & scene transitions.

## Threading
- All OBS API calls **must** run on main thread (`obs.timer_add`).  
- Separate worker threads/queues for download, normalisation, metadata.

## Logging
- Two levels: DEBUG (default 1) & NORMAL; timestamp each entry.

Refer back here from every Phase prompt to ensure no requirement is missed.  
See **03‑OBS_API.md** for environment constraints and **04‑Guidelines.md** for coding style.

*Prev → 01‑Overview.md | Next → 03‑OBS_API.md*