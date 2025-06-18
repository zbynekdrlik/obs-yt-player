# Phase 09 – Playback Control

## Goal
Implement random video playback through OBS Media Source with metadata display, handling playback end detection and scene transitions.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements playback logic from `02-requirements.md`:
- Random no-repeat playback from cached videos
- Update Media Source `video` and Text Source `title`
- Handle playback end detection
- Only play when scene is active

## Implementation Details

### 1. Playback State Management
```python
# Add to global variables section:
current_playback_video_id = None  # Track currently playing video ID
```

### 2. Video Selection Logic
```python
def select_next_video():
    """
    Select next video for playback using random no-repeat logic.
    Returns video_id or None if no videos available.
    """
    with state_lock:
        # Get list of available videos
        available_videos = list(cached_videos.keys())
        
        if not available_videos:
            log("No videos available for playback")
            return None
        
        # If all videos have been played, reset the played list
        if len(played_videos) >= len(available_videos):
            played_videos.clear()
            log("Reset played videos list")
        
        # Find unplayed videos
        unplayed = [vid for vid in available_videos if vid not in played_videos]
        
        if not unplayed:
            # This shouldn't happen due to reset above, but just in case
            played_videos.clear()
            unplayed = available_videos
        
        # Select random video from unplayed
        selected = random.choice(unplayed)
        played_videos.append(selected)
        
        video_info = cached_videos[selected]
        log(f"Selected: {video_info['artist']} - {video_info['song']}")
        
        return selected
```

### 3. Media Source Update Functions
```python
def update_media_source(video_path):
    """
    Update OBS Media Source with new video.
    Must be called from main thread.
    """
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "local_file", video_path)
        obs.obs_data_set_bool(settings, "restart_on_activate", True)
        obs.obs_data_set_bool(settings, "close_when_inactive", True)
        
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        
        log(f"Updated media source: {os.path.basename(video_path)}")
        return True
    else:
        log(f"Media source '{MEDIA_SOURCE_NAME}' not found")
        return False

def update_text_source(artist, song):
    """
    Update OBS Text Source with metadata.
    Must be called from main thread.
    """
    source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if source:
        text = f"{artist} - {song}"
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        
        log(f"Updated text source: {text}")
        return True
    else:
        log(f"Text source '{TEXT_SOURCE_NAME}' not found")
        return False
```

### 4. Playback End Detection
```python
def get_media_state(source_name):
    """
    Get current state of media source.
    Returns one of: OBS_MEDIA_STATE_NONE, OBS_MEDIA_STATE_PLAYING,
                    OBS_MEDIA_STATE_STOPPED, OBS_MEDIA_STATE_ENDED
    """
    source = obs.obs_get_source_by_name(source_name)
    if source:
        state = obs.obs_source_media_get_state(source)
        obs.obs_source_release(source)
        return state
    return obs.OBS_MEDIA_STATE_NONE

def get_media_duration(source_name):
    """
    Get duration of current media in milliseconds.
    """
    source = obs.obs_get_source_by_name(source_name)
    if source:
        duration = obs.obs_source_media_get_duration(source)
        obs.obs_source_release(source)
        return duration
    return 0

def get_media_time(source_name):
    """
    Get current playback time in milliseconds.
    """
    source = obs.obs_get_source_by_name(source_name)
    if source:
        time = obs.obs_source_media_get_time(source)
        obs.obs_source_release(source)
        return time
    return 0
```

### 5. Main Playback Controller
```python
def playback_controller():
    """
    Main playback controller - runs on main thread via timer.
    """
    global is_playing, current_video_path, current_playback_video_id
    
    # Check if scene is active
    if not scene_active:
        if is_playing:
            log("Scene inactive, stopping playback")
            stop_current_playback()
        return
    
    # Check if we have videos to play
    with state_lock:
        if not cached_videos:
            return
    
    # Get current media state
    media_state = get_media_state(MEDIA_SOURCE_NAME)
    
    # Handle different states
    if media_state == obs.OBS_MEDIA_STATE_PLAYING:
        # Video is playing, check if near end
        duration = get_media_duration(MEDIA_SOURCE_NAME)
        current_time = get_media_time(MEDIA_SOURCE_NAME)
        
        if duration > 0 and current_time > 0:
            time_remaining = duration - current_time
            # Log progress every 30 seconds
            if int(current_time / 1000) % 30 == 0:
                log(f"Playing: {int(current_time/1000)}s / {int(duration/1000)}s")
            
            # Check if within last 500ms
            if time_remaining < 500:
                log("Video ending, preparing next...")
                start_next_video()
                
    elif media_state == obs.OBS_MEDIA_STATE_ENDED or media_state == obs.OBS_MEDIA_STATE_STOPPED:
        # Video ended or was stopped
        if is_playing:
            log("Playback ended, starting next video")
            start_next_video()
            
    elif media_state == obs.OBS_MEDIA_STATE_NONE:
        # No media loaded
        if scene_active and not is_playing:
            log("Scene active, starting playback")
            start_next_video()

def start_next_video():
    """
    Start playing the next video.
    Must be called from main thread.
    """
    global is_playing, current_video_path, current_playback_video_id
    
    # Select next video
    video_id = select_next_video()
    if not video_id:
        is_playing = False
        return
    
    # Get video info
    with state_lock:
        video_info = cached_videos.get(video_id)
        if not video_info:
            return
    
    # Update sources
    if update_media_source(video_info['path']):
        update_text_source(video_info['artist'], video_info['song'])
        
        # Update playback state
        is_playing = True
        current_video_path = video_info['path']
        current_playback_video_id = video_id
        
        log(f"Started playback: {video_info['artist']} - {video_info['song']}")
    else:
        is_playing = False

def stop_current_playback():
    """
    Stop current playback and clear sources.
    Must be called from main thread.
    """
    global is_playing, current_video_path, current_playback_video_id
    
    # Stop media source
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if source:
        obs.obs_source_media_stop(source)
        obs.obs_source_release(source)
    
    # Clear text
    update_text_source("", "")
    
    # Update state
    is_playing = False
    current_video_path = None
    current_playback_video_id = None
    
    log("Playback stopped")
```

### 6. Update Script Load/Unload
Update script_load to start playback timer:
```python
def script_load(settings):
    # ... existing code ...
    
    # Start playback controller timer
    obs.timer_add(playback_controller, PLAYBACK_CHECK_INTERVAL)
    
    log("Script loaded successfully")
```

Update script_unload to properly stop:
```python
def script_unload():
    # ... existing code ...
    
    # Stop playback
    if is_playing:
        stop_current_playback()
    
    # ... rest of existing code ...
```

### 7. Handle Scene Changes
Update on_frontend_event to handle scene changes:
```python
def on_frontend_event(event):
    """Handle OBS frontend events."""
    global scene_active
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        # Check if our scene is active
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            scene_name = obs.obs_source_get_name(current_scene)
            was_active = scene_active
            scene_active = (scene_name == SCENE_NAME)
            
            # Log scene transition
            if scene_active and not was_active:
                log(f"Scene activated: {scene_name}")
            elif not scene_active and was_active:
                log(f"Scene deactivated, was: {scene_name}")
                
            obs.obs_source_release(current_scene)
```

## Key Considerations
- All OBS API calls must be on main thread (via timer)
- Random selection without immediate repeats
- Detect playback end to auto-advance
- Stop playback when scene inactive
- Handle edge cases (no videos, all played)
- Progress logging for long videos
- Clean state management

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` (increment MINOR version)
- [ ] Add current_playback_video_id global
- [ ] Implement select_next_video with no-repeat logic
- [ ] Implement media source update functions
- [ ] Implement playback state detection
- [ ] Implement main playback_controller
- [ ] Implement start_next_video
- [ ] Implement stop_current_playback
- [ ] Add playback timer in script_load
- [ ] Update scene change handling
- [ ] Ensure all OBS calls on main thread

## Testing Before Commit
1. Start with empty scene - verify no playback
2. Switch to player scene - verify playback starts
3. Let video play to end - verify auto-advance
4. Switch away from scene - verify playback stops
5. Switch back to scene - verify playback resumes
6. Test with only one video - verify it replays
7. Test with multiple videos - verify no immediate repeats
8. Check metadata updates with each video
9. Test with missing media/text source
10. Verify progress logging for long videos
11. **Verify version was incremented**
12. **Test with various video lengths**

## Commit
After successful testing, commit with message:  
> *"Add random playback control with auto-advance (Phase 9)"*

*After verification, proceed to Phase 10.*
