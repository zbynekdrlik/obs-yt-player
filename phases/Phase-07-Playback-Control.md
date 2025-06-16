# Phase 07 – Cache Management & Playback Control

## Goal
Implement cache scanning, cleanup of old videos, and random video playback through OBS Media Source with metadata display. This phase starts with cache management before enabling playback.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements from `02-requirements.md`:
- Remove local files whose IDs left the playlist (skip currently playing)
- Media Source `video`, Text Source `title`
- Random no-repeat playback

## Implementation Details

### 1. Cache Scanning
```python
def get_cached_videos():
    """Scan cache directory for normalized videos."""
    videos = {}
    
    try:
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return videos
        
        # Look for normalized mp4 files
        for file_path in cache_path.glob("*_normalized.mp4"):
            # Extract video ID from filename
            match = re.search(r'_([a-zA-Z0-9_-]{11})_normalized\.mp4$', file_path.name)
            if match:
                video_id = match.group(1)
                
                # Extract metadata from filename
                parts = file_path.stem.replace('_normalized', '').split('_')
                if len(parts) >= 3:
                    # Join all parts except the last one (video_id) for song and artist
                    video_id_from_parts = parts[-1]
                    artist = parts[-2] if len(parts) > 2 else "Unknown Artist"
                    song = '_'.join(parts[:-2]) if len(parts) > 2 else "Unknown Song"
                    
                    videos[video_id] = {
                        "path": str(file_path),
                        "song": song,
                        "artist": artist,
                        "normalized": True
                    }
        
        log(f"Found {len(videos)} cached videos", "DEBUG")
        
    except Exception as e:
        log(f"Error scanning cache: {e}", "DEBUG")
    
    return videos
```

### 2. Cleanup Old Videos
```python
def cleanup_old_videos():
    """Remove videos no longer in playlist (except currently playing)."""
    try:
        with state_lock:
            current_ids = playlist_video_ids.copy()
            cached_ids = set(cached_videos.keys())
            playing = current_video_path
        
        # Find videos to remove
        to_remove = cached_ids - current_ids
        
        for video_id in to_remove:
            video_info = cached_videos.get(video_id)
            if video_info and video_info['path'] != playing:
                try:
                    if os.path.exists(video_info['path']):
                        os.remove(video_info['path'])
                        log(f"Removed old video: {video_info['path']}", "DEBUG")
                    
                    with state_lock:
                        del cached_videos[video_id]
                except Exception as e:
                    log(f"Error removing old video: {e}", "DEBUG")
                    
    except Exception as e:
        log(f"Error in cleanup_old_videos: {e}", "DEBUG")
```

### 3. Cache Initialization
Add to playlist_sync_worker after playlist fetch:
```python
# After fetching playlist and updating playlist_video_ids:
# Scan cache and cleanup
with state_lock:
    cached_videos.clear()
    cached_videos.update(get_cached_videos())

# Clean up old videos
cleanup_old_videos()

# Start playback timer if scene is active
if scene_active and not obs.timer_enabled(playback_controller):
    obs.timer_add(playback_controller, PLAYBACK_CHECK_INTERVAL)
```

### 4. Playback State Management
```python
# Global state variables
is_playing = False
current_video_path = None
played_videos = []  # Track played video IDs
next_check_time = 0
```

### 5. Video Selection Logic
```python
def select_next_video():
    """Select next video to play randomly without repeats."""
    with state_lock:
        available = [id for id in cached_videos if id not in played_videos]
        if not available:
            played_videos.clear()  # Reset when all played
            available = list(cached_videos.keys())
        
        if available:
            video_id = random.choice(available)
            played_videos.append(video_id)
            return cached_videos[video_id]
    return None
```

### 6. Playback Controller
```python
def playback_controller():
    """Main playback controller - runs on main thread."""
    global is_playing, current_video_path, next_check_time
    
    if not scene_active:
        return
    
    current_time = obs.os_gettime_ns() // 1000000
    if current_time < next_check_time:
        return
    
    # Check if video ended
    if is_playing and media_ended():
        play_next_video()
    
    # Start playback if not playing
    elif not is_playing and scene_active:
        play_next_video()
    
    next_check_time = current_time + 1000  # Check every second
```

### 7. Media Control Functions
```python
def play_next_video():
    """Play the next video in the queue."""
    video_info = select_next_video()
    if not video_info:
        log("No videos available to play", "DEBUG")
        return
    
    # Update media source
    update_media_source(video_info['path'])
    
    # Update text source
    update_text_source(f"{video_info['song']} - {video_info['artist']}")
    
    # Update state
    global is_playing, current_video_path
    is_playing = True
    current_video_path = video_info['path']

def media_ended():
    """Check if current media has finished playing."""
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if media_source:
        state = obs.obs_source_media_get_state(media_source)
        obs.obs_source_release(media_source)
        return state == obs.OBS_MEDIA_STATE_ENDED
    return True

def update_media_source(file_path):
    """Update media source with new file."""
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if media_source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "local_file", file_path)
        obs.obs_data_set_bool(settings, "restart_on_activate", True)
        obs.obs_source_update(media_source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(media_source)

def update_text_source(text):
    """Update text source with metadata."""
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if text_source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        obs.obs_source_update(text_source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(text_source)
```

## Key Considerations
- Cache operations happen before playback starts
- All OBS API calls on main thread
- Thread-safe state access
- Handle empty cache gracefully
- Proper source reference management

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement get_cached_videos function
- [ ] Implement cleanup_old_videos function
- [ ] Update playlist_sync_worker with cache operations
- [ ] Add playback state variables
- [ ] Implement video selection logic
- [ ] Implement playback controller
- [ ] Implement media control functions
- [ ] Test cache scanning and cleanup
- [ ] Test playback functionality

## Testing Before Commit
1. Test cache scanning with various filenames
2. Test cleanup removes only non-playlist videos
3. Verify currently playing video is not removed
4. Start with empty cache - verify no crash
5. Add one video - verify it loops
6. Add multiple videos - verify random order
7. Verify no repeats until all played
8. Check metadata displays correctly
9. Verify smooth transitions between videos
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add cache management and random video playback"*

*After verification, proceed to Phase 08.*