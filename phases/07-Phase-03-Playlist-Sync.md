# 07-Phase 03 – Playlist Sync Thread

## Goal
Implement the playlist synchronization worker that:

1. Fetches YouTube playlist data via **yt‑dlp**.
2. Queues each video for download.
3. Removes old videos no longer in the playlist (skip currently playing).
4. Runs periodically (every 30 minutes) and on *Sync Now* button click.

## Key Parts
- `sync_playlist_thread`: fetch IDs, compare with local cache, queue downloads.
- Thread‑safe access to `video_queue` and `currently_playing`.
- Handle errors gracefully (network issues, invalid playlist URL).

## Commit
Suggested commit message:  
> *"Add playlist sync thread for periodic updates."*

*After verification, proceed to Phase 04.*