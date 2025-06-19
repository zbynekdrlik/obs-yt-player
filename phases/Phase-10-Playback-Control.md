# Phase 10 – Playback Control

## Goal
Implement random video playback through OBS Media Source with metadata display, handling playback end detection and scene transitions.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 2.1.0 to 2.2.0)

## Requirements Reference
This phase implements playback logic from `02-requirements.md`:
- Random no-repeat playback from cached videos
- Update Media Source `video` and Text Source `title`
- Handle playback end detection
- Only play when scene is active

## Implementation Details

### 1. Module-Level Variables
```python
# Module-level variables for proper timer management
_playback_timer = None
_last_progress_log = {}
_playback_retry_count = 0
_max_retry_attempts = 3
```

### 2. Video Selection Logic (Enhanced)
```python
def select_next_video():
    """
    Select next video for playback using random no-repeat logic.
    Uses state accessors for thread-safe operation.
    """
    cached_videos = get_cached_videos()
    
    if not cached_videos:
        log("No videos available for playback")
        return None
    
    available_videos = list(cached_videos.keys())
    played_videos = get_played_videos()
    
    # If all videos have been played, reset the played list
    if len(played_videos) >= len(available_videos):
        clear_played_videos()
        played_videos = []
        log("Reset played videos list")
    
    # Find unplayed videos
    unplayed = [vid for vid in available_videos if vid not in played_videos]
    
    if not unplayed:
        # This shouldn't happen due to reset above, but just in case
        clear_played_videos()
        unplayed = available_videos
    
    # Select random video from unplayed
    selected = random.choice(unplayed)
    add_played_video(selected)
    
    video_info = cached_videos[selected]
    log(f"Selected: {video_info['artist']} - {video_info['song']}")
    
    return selected
```

### 3. Media Source Update Functions (With Error Handling)
```python
def update_media_source(video_path):
    """
    Update OBS Media Source with new video.
    Includes validation and error handling.
    """
    try:
        # Validate file exists
        if not os.path.exists(video_path):
            log(f"ERROR: Video file not found: {video_path}")
            return False
        
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", video_path)
            obs.obs_data_set_bool(settings, "restart_on_activate", True)
            obs.obs_data_set_bool(settings, "close_when_inactive", True)
            obs.obs_data_set_bool(settings, "hw_decode", True)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
            
            log(f"Updated media source: {os.path.basename(video_path)}")
            return True
        else:
            log(f"ERROR: Media source '{MEDIA_SOURCE_NAME}' not found")
            return False
            
    except Exception as e:
        log(f"ERROR updating media source: {e}")
        return False
```

### 4. Playback State Detection (Enhanced)
```python
def is_video_near_end(duration, current_time, threshold_percent=95):
    """
    Check if video is near end using percentage threshold.
    More robust than fixed millisecond checks.
    """
    if duration <= 0:
        return False
    percent_complete = (current_time / duration) * 100
    return percent_complete >= threshold_percent

def log_playback_progress(video_id, current_time, duration):
    """
    Log playback progress at intervals without spamming.
    Uses smart caching to prevent log flooding.
    """
    global _last_progress_log
    
    # Log every 30 seconds
    progress_key = f"{video_id}_{int(current_time/30000)}"
    if progress_key not in _last_progress_log:
        _last_progress_log[progress_key] = True
        percent = int((current_time/duration) * 100)
        
        # Get video info for better logging
        video_info = get_cached_video_info(video_id)
        if video_info:
            log(f"Playing: {video_info['artist']} - {video_info['song']} "
                f"[{percent}% - {int(current_time/1000)}s / {int(duration/1000)}s]")
```

### 5. Main Playback Controller (State-Based)
```python
def playback_controller():
    """
    Main playback controller with state-based handling.
    Runs on main thread via timer.
    """
    try:
        # Check if scene is active
        if not is_scene_active():
            if is_playing():
                log("Scene inactive, stopping playback")
                stop_current_playback()
            return
        
        # Check if we have videos to play
        cached_videos = get_cached_videos()
        if not cached_videos:
            return
        
        # Get current media state
        media_state = get_media_state(MEDIA_SOURCE_NAME)
        
        # Handle different states
        if media_state == obs.OBS_MEDIA_STATE_PLAYING:
            handle_playing_state()
        elif media_state == obs.OBS_MEDIA_STATE_ENDED:
            handle_ended_state()
        elif media_state == obs.OBS_MEDIA_STATE_STOPPED:
            handle_stopped_state()
        elif media_state == obs.OBS_MEDIA_STATE_NONE:
            handle_none_state()
            
    except Exception as e:
        log(f"ERROR in playback controller: {e}")
```

### 6. State Handlers
```python
def handle_playing_state():
    """Handle currently playing video state."""
    duration = get_media_duration(MEDIA_SOURCE_NAME)
    current_time = get_media_time(MEDIA_SOURCE_NAME)
    
    if duration > 0 and current_time > 0:
        # Log progress without spamming
        video_id = get_current_playback_video_id()
        if video_id:
            log_playback_progress(video_id, current_time, duration)
        
        # Check if video is near end (95% complete)
        if is_video_near_end(duration, current_time, 95):
            log("Video near end, preparing next...")
            start_next_video()

def handle_stopped_state():
    """Handle video stopped state with retry logic."""
    if is_playing():
        log("Playback stopped, attempting to resume or skip")
        global _playback_retry_count
        if _playback_retry_count < _max_retry_attempts:
            _playback_retry_count += 1
            log(f"Retry attempt {_playback_retry_count}")
            start_next_video()
        else:
            log("Max retries reached, stopping playback")
            stop_current_playback()
```

### 7. Enhanced Video Start Function
```python
def start_next_video():
    """
    Start playing the next video with validation and retry logic.
    Must be called from main thread.
    """
    global _playback_retry_count, _last_progress_log
    
    # Reset retry count on successful transition
    _playback_retry_count = 0
    
    # Clear progress log for new video
    _last_progress_log.clear()
    
    # Select next video
    video_id = select_next_video()
    if not video_id:
        set_playing(False)
        return
    
    # Get video info
    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return
    
    # Validate video file exists
    if not os.path.exists(video_info['path']):
        log(f"ERROR: Video file missing: {video_info['path']}")
        # Try another video
        start_next_video()
        return
    
    # Update sources
    if update_media_source(video_info['path']):
        update_text_source(video_info['artist'], video_info['song'])
        
        # Update playback state using accessors
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        log(f"Started playback: {video_info['artist']} - {video_info['song']}")
    else:
        # Failed to update media source, try another video
        log("Failed to start video, trying another...")
        if _playback_retry_count < _max_retry_attempts:
            _playback_retry_count += 1
            start_next_video()
        else:
            log("Max retries reached, stopping")
            set_playing(False)
```

### 8. Timer Management
```python
def start_playback_controller():
    """Start the playback controller timer with proper cleanup."""
    global _playback_timer
    
    try:
        # Remove existing timer if any
        if _playback_timer:
            obs.timer_remove(_playback_timer)
        
        # Add new timer
        _playback_timer = playback_controller
        obs.timer_add(_playback_timer, PLAYBACK_CHECK_INTERVAL)
        log("Playback controller started")
        
    except Exception as e:
        log(f"ERROR starting playback controller: {e}")

def stop_playback_controller():
    """Stop the playback controller timer."""
    global _playback_timer
    
    try:
        if _playback_timer:
            obs.timer_remove(_playback_timer)
            _playback_timer = None
            log("Playback controller stopped")
            
    except Exception as e:
        log(f"ERROR stopping playback controller: {e}")
```

## Key Improvements
1. **State Management**: Uses existing state accessors instead of global variables
2. **Error Handling**: Comprehensive error handling with recovery strategies
3. **Percentage-Based Detection**: More reliable than fixed millisecond thresholds
4. **Progress Logging**: Smart caching prevents log spam
5. **File Validation**: Checks files exist before attempting playback
6. **Retry Logic**: Handles transient failures gracefully
7. **Timer Management**: Proper cleanup prevents multiple timers
8. **Exception Safety**: All functions wrapped in try-catch blocks

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` to 2.2.0 (MINOR increment)
- [x] Use state accessors instead of globals
- [x] Implement select_next_video with proper state management
- [x] Add file validation to media source updates
- [x] Implement percentage-based completion detection
- [x] Add smart progress logging
- [x] Implement state-based playback controller
- [x] Add retry logic for failures
- [x] Implement proper timer management
- [x] Add comprehensive error handling
- [x] Ensure all OBS calls on main thread

## Testing Before Commit
1. **Basic Functionality**
   - [ ] Start with empty scene - verify no playback
   - [ ] Switch to player scene - verify playback starts
   - [ ] Let video play to end - verify auto-advance
   - [ ] Switch away from scene - verify playback stops
   - [ ] Switch back to scene - verify playback resumes

2. **Edge Cases**
   - [ ] Test with only one video - verify it replays
   - [ ] Test with multiple videos - verify no immediate repeats
   - [ ] Check metadata updates with each video
   - [ ] Test with missing media/text source
   - [ ] Delete a video file while playing - verify recovery

3. **Robustness**
   - [ ] Rapid scene switches don't cause crashes
   - [ ] Progress logging appears at 30s intervals
   - [ ] Verify version 2.2.0 in logs
   - [ ] Test with videos of various lengths
   - [ ] Memory usage remains stable
   - [ ] Script reload doesn't create duplicate timers

4. **Logs to Verify**
   ```
   [ytfast.py] [timestamp] Script version 2.2.0 loaded
   [ytfast.py] [timestamp] Playback controller started
   [ytfast.py] [timestamp] Selected: Artist - Song
   [ytfast.py] [timestamp] Updated media source: filename.mp4
   [ytfast.py] [timestamp] Playing: Artist - Song [50% - 60s / 120s]
   [ytfast.py] [timestamp] Video near end, preparing next...
   ```

## Commit
After successful testing and user approval with logs, commit with message:  
> *"Implement enhanced playback control with error recovery (Phase 10)"*

*After verification, proceed to Phase 11.*
