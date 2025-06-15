# Phase 04 – Caching & File Management

## Goal
Add functions that handle:

- Filename sanitization: `<song>_<artist>_<id>_normalized.mp4`.
- Duplicate management (keep only newest).
- Cleanup of `.part` files on startup.
- Thread‑safe file operations.

## Key Functions
- `sanitize_filename(title, artist, video_id)`
- `get_cached_videos()` → list of normalized files in cache dir.
- `cleanup_cache()` → remove duplicates and temp files.

## Commit
Suggested commit message:  
> *"Implement cache management and filename sanitization."*

*After verification, proceed to Phase 05.*