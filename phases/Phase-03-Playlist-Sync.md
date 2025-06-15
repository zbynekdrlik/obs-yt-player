# Phase 03 – Playlist Sync Thread

## Goal
Implement the playlist synchronization worker that:

1. Fetches YouTube playlist data via **yt‑dlp**.
2. Queues each video for download.
3. Removes old videos no longer in the playlist (skip currently playing).
4. Runs **only** at startup and on *Sync Now* button click.

## Requirements Reference
This phase implements the "Playlist Synchronisation" section from `02-requirements.md`.

**IMPORTANT**: NO PERIODIC SYNC - Due to slow LTE internet, sync only happens:
- Once at script startup
- When user clicks "Sync Now" button

## Key Parts
- `sync_playlist_thread`: fetch IDs, compare with local cache, queue downloads.
- Thread‑safe access to `video_queue` and `currently_playing`.
- Handle errors gracefully (network issues, invalid playlist URL).
- Must check `tools_ready` flag before attempting to use yt-dlp.
- **No timer-based periodic sync implementation**

## OBS API Constraints
Per `03-obs_api.md`:
- Heavy work (fetching playlist) must run in background thread
- Any OBS API calls must use `obs.timer_add` to run on main thread

## Testing Before Commit
1. Load script in OBS with valid playlist URL
2. Verify sync runs once at startup
3. Verify "Sync Now" button triggers sync
4. Check playlist is fetched successfully
5. **Verify NO periodic sync occurs** - wait and ensure no automatic resync
6. Test with invalid playlist URL - should log error gracefully
7. Ensure OBS remains responsive during sync

## Commit
After successful testing, commit with message:  
> *"Add playlist sync thread - startup and manual only"*

*After verification, proceed to Phase 04.*