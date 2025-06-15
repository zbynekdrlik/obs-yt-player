# Phase 03 – Playlist Sync & Queue Management

## Goal
Implement playlist synchronization that fetches video IDs and queues them for processing. This phase creates the foundation for the video processing pipeline.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.1.0` → `1.2.0`)

## Requirements Reference
This phase implements playlist synchronization from `02-requirements.md`:
- Trigger **only** at startup and via *Sync Playlist Now* button
- **NO PERIODIC SYNC** - Script runs on slow LTE internet
- Process videos **one-by-one** (queue for serial processing)
- Remove local files whose IDs left the playlist

## Components to Implement

### 1. Playlist Sync Worker
```python
def playlist_sync_worker():
    # Wait for sync_event signal
    # Check tools_ready before proceeding
    # Fetch playlist with yt-dlp
    # Queue new videos for processing
    # Clean up old videos
```

Key features:
- Triggered by `sync_event.set()`
- Fetches playlist data via yt-dlp
- Extracts video IDs and titles
- Queues videos not already cached
- NO automatic periodic sync

### 2. Playlist Fetching
```python
def fetch_playlist_with_ytdlp(playlist_url):
    # Use yt-dlp --flat-playlist
    # Return list of video info dicts
    # Handle errors gracefully
```

### 3. Cache Management
```python
def get_cached_videos():
    # Scan cache directory
    # Return dict of cached videos
    
def cleanup_old_videos():
    # Remove videos no longer in playlist
    # Skip currently playing video
```

### 4. Queue Management
- Use `queue.Queue()` for thread-safe operations
- Queue video info objects (id, title, duration)
- Process videos serially in later phases

## Key Implementation Points
- Use `threading.Event` for sync signaling
- Queue contains video info, not video files
- Implement robust error handling
- Check `tools_ready` before using yt-dlp
- Thread-safe cache operations

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement playlist_sync_worker thread
- [ ] Add sync_event for manual trigger
- [ ] Implement fetch_playlist_with_ytdlp
- [ ] Add get_cached_videos function
- [ ] Add cleanup_old_videos function
- [ ] Wire up "Sync Now" button callback
- [ ] Add startup sync trigger
- [ ] Test queue operations

## Testing Before Commit
1. Test playlist fetching with valid URL
2. Verify sync runs once at startup after tools ready
3. Test "Sync Now" button triggers sync
4. **Verify NO periodic sync** - wait 10+ minutes
5. Test with empty playlist
6. Test with invalid playlist URL
7. Verify old video cleanup works
8. Check queue fills correctly
9. Ensure OBS stays responsive
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add playlist sync and queue management"*

*After verification, proceed to Phase 04 - Video Download.*