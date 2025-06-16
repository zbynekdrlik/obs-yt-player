# Phase 03 – Playlist Sync & Queue Management

## Goal
Implement playlist synchronization that fetches video IDs and queues them for processing. This phase focuses ONLY on fetching playlist data and queueing - no cache operations yet.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements playlist synchronization from `02-requirements.md`:
- Trigger **only** at startup and via *Sync Playlist Now* button
- **NO PERIODIC SYNC** - Script runs on slow LTE internet
- Queue videos for serial processing

## Components to Implement

### 1. Playlist Sync Worker
```python
def playlist_sync_worker():
    while not stop_threads:
        # Wait for sync_event signal
        if not sync_event.wait(timeout=1):
            continue
        
        sync_event.clear()
        
        # Check tools_ready before proceeding
        with state_lock:
            if not tools_ready:
                continue
        
        # Fetch playlist
        videos = fetch_playlist_with_ytdlp(playlist_url)
        
        # Update playlist video IDs
        with state_lock:
            playlist_video_ids.clear()
            playlist_video_ids.update(video['id'] for video in videos)
        
        # Queue videos for processing
        for video in videos:
            video_queue.put(video)
```

### 2. Playlist Fetching
```python
def fetch_playlist_with_ytdlp(playlist_url):
    cmd = [
        ytdlp_path,
        '--flat-playlist',
        '--dump-json',
        '--no-warnings',
        playlist_url
    ]
    # Parse JSON output
    # Return list of {'id': ..., 'title': ..., 'duration': ...}
```

### 3. Startup Sync Trigger
```python
def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    global sync_on_startup_done
    
    with state_lock:
        if sync_on_startup_done:
            return
        sync_on_startup_done = True
    
    log("Starting one-time playlist sync on startup", "NORMAL")
    sync_event.set()
```

### 4. Manual Sync Button
Update `sync_now_callback` to trigger sync:
```python
def sync_now_callback(props, prop):
    with state_lock:
        if not tools_ready:
            log("Cannot sync - tools not ready yet", "NORMAL")
            return True
    
    sync_event.set()
    return True
```

## Key Implementation Points
- Use `threading.Event` for sync signaling
- Queue contains video info dicts, not files
- NO cache scanning in this phase
- NO cleanup operations in this phase
- Thread-safe queue and state operations
- Call trigger_startup_sync from tools_setup_worker

## What This Phase Does NOT Do
- Does NOT scan cache directory
- Does NOT cleanup old videos
- Does NOT check if videos are already downloaded
- Cache operations moved to Phase 7

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement complete playlist_sync_worker
- [ ] Implement fetch_playlist_with_ytdlp
- [ ] Add trigger_startup_sync function
- [ ] Update sync_now_callback to use sync_event
- [ ] Call trigger_startup_sync from tools thread
- [ ] Handle errors gracefully
- [ ] Add appropriate logging

## Testing Before Commit
1. Test playlist fetching with valid URL
2. Verify sync runs once at startup after tools ready
3. Test "Sync Now" button triggers sync
4. **Verify NO periodic sync** - wait 10+ minutes
5. Test with empty playlist
6. Test with invalid playlist URL
7. Check queue fills with video info
8. Verify thread-safe operations
9. Ensure OBS stays responsive
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add playlist sync and queue management"*

*After verification, proceed to Phase 04 - Video Download.*