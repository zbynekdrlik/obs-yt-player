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
- Store videos in user‑configurable cache dir (editable text field).  
- **Default cache location**: `<script_directory>/<scriptname>-cache/`
  - Example: `ytfast.py` → `./ytfast-cache/`
  - Allows multiple script instances with separate caches
  - Users can easily modify path in text field
- Sanitise filenames: `<song>_<artist>_<id>_normalized.mp4`.  
- Retain only newest duplicate; clean temp `.part` files.

## Metadata Retrieval
- Primary: **AcoustID** (`RXS1uld515`).  
- Fallback: parse YouTube title; log transformation.

## Playback Logic
- Scene name == script filename without extension (e.g. `ytfast.py` → scene `ytfast`).  
- Media Source `video`, Text Source `title`.  
- Random no‑repeat playback; handle stop button & scene transitions.

## Threading
- All OBS API calls **must** run on main thread (`obs.timer_add`).  
- Separate worker threads/queues for download, normalisation, metadata.

## Logging
- Thread-aware logging system with timestamp and script identification.
- Format depends on thread context:
  - Main thread: `[timestamp] message` (OBS prepends script name)
  - Background threads: `[timestamp] [script_name] message` (to identify source)
- OBS output format:
  - Main thread: `[script.py] [timestamp] message`
  - Background threads: `[Unknown Script] [timestamp] [script_name] message`
- This allows distinguishing between multiple script instances in background threads.
- No debug levels or toggles - all messages are logged equally.
- Log script version on startup.

## Versioning
- Maintain version constant in script (e.g., `SCRIPT_VERSION = "1.3.6"`)
- Increment version with each development iteration:
  - PATCH: Bug fixes, minor changes
  - MINOR: New features, non-breaking changes
  - MAJOR: Breaking changes, major refactors
- Log version on script startup

## Default Configuration
- **Default Playlist URL**: `https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U`
- Users can change this in OBS script properties to any valid YouTube playlist

Refer back here from every Phase prompt to ensure no requirement is missed.  
See **03‑OBS_API.md** for environment constraints and **04‑Guidelines.md** for coding style.

*Prev → 01‑Overview.md | Next → 03‑OBS_API.md*
