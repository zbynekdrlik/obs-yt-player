# Phase 03 – Playlist Sync Thread

## Goal
Implement the playlist synchronization worker that:

1. Fetches YouTube playlist data via **yt‑dlp**.
2. Queues each video for download.
3. Removes old videos no longer in the playlist (skip currently playing).
4. Runs periodically (every 60 minutes) and on *Sync Now* button click.

## Requirements Reference
This phase implements the "Playlist Synchronisation" section from `02-requirements.md`.

## Key Parts
- `sync_playlist_thread`: fetch IDs, compare with local cache, queue downloads.
- Thread‑safe access to `video_queue` and `currently_playing`.
- Handle errors gracefully (network issues, invalid playlist URL).
- Must check `tools_ready` flag before attempting to use yt-dlp.

## OBS API Constraints
Per `03-obs_api.md`:
- Heavy work (fetching playlist) must run in background thread
- Any OBS API calls must use `obs.timer_add` to run on main thread

## Testing Before Commit
1. Load script in OBS with valid playlist URL
2. Verify "Sync Now" button triggers sync
3. Check playlist is fetched successfully
4. Verify periodic sync runs every 60 minutes
5. Test with invalid playlist URL - should log error gracefully
6. Ensure OBS remains responsive during sync

## Commit
After successful testing, commit with message:  
> *"Add playlist sync thread for periodic updates."*

*After verification, proceed to Phase 04.*