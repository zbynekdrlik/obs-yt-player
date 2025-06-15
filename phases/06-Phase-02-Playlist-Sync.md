# 06‑Phase 02 – Playlist Synchronisation

## Goal
Implement the **playlist_sync_thread** and related helpers so that:

1. On startup or *Sync Now* button, a background thread fetches the playlist (default URL in 02‑Requirements.md) via `yt-dlp --flat-playlist`.
2. For each video ID not yet in cache, queue a download task (next phases will handle download).
3. Mark removed IDs for deletion.
4. Log progress in DEBUG mode.

## Constraints
- **Do not** perform downloads or file writes here; just queue tasks.
- Respect `tools_ready` flag; if False, re‑queue sync after 60 s.
- All OBS API calls must run on main thread (see 03‑OBS_API.md).

## Commit
Suggested commit message:  
> *"Implement playlist sync thread and ID queueing."*