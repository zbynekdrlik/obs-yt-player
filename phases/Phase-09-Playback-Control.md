# Phase 09 – Playback Control

## Goal
Implement random video playback through OBS Media Source with metadata display, handling playback end detection and scene transitions.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version
**Remember**: Increment version with EVERY code change during development, not just once per phase.

## Requirements Reference
This phase implements playback logic from `02-requirements.md`:
- Random no-repeat playback from cached videos
- Update Media Source `video` and Text Source `title`
- Handle playback end detection
- Only play when scene is active
- **Title display timing**: Clear 2s before end, show 2s after start

## Implementation Details

### 1. Module-Level Variables
```python
# Module-level variables for proper timer management
_playback_timer = None
_last_progress_log = {}
_playback_retry_count = 0
_max_retry_attempts = 3
_waiting_for_videos_logged = False
_last_cached_count = 0
_first_run = True
_sources_verified = False
_initial_state_checked = False
_title_clear_timer = None
_title_show_timer = None
_pending_title_info = None
_title_clear_scheduled = False
```

### 2. Title Timing Implementation
The script implements precise title display timing to prevent text appearing on black screens during transitions:

```python
# Title timing constants (in seconds)
TITLE_CLEAR_BEFORE_END = 2.0  # Clear title 2 seconds before song ends
TITLE_SHOW_AFTER_START = 2.0  # Show title 2 seconds after song starts

def clear_title_before_end_callback():
    """Callback to clear title before song ends."""
    global _title_clear_timer, _title_clear_scheduled
    # Remove the timer to prevent it from firing again
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
    _title_clear_scheduled = False
    log("Clearing title before song end")
    update_text_source("", "")

def show_title_after_start_callback():
    """Callback to show title after song starts."""
    global _title_show_timer, _pending_title_info
    # Remove the timer to prevent it from firing again
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None
    
    if _pending_title_info:
        song = _pending_title_info.get('song', 'Unknown Song')
        artist = _pending_title_info.get('artist', 'Unknown Artist')
        log(f"Showing title after delay: {song} - {artist}")
        update_text_source(song, artist)
        _pending_title_info = None

def schedule_title_clear(duration_ms):
    """Schedule clearing of title before song ends."""
    global _title_clear_timer, _title_clear_scheduled
    
    # Cancel any existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        
    # Calculate when to clear (duration - 2 seconds)
    clear_time_ms = duration_ms - (TITLE_CLEAR_BEFORE_END * 1000)
    
    if clear_time_ms > 0:
        # Schedule the clear
        _title_clear_timer = clear_title_before_end_callback
        obs.timer_add(_title_clear_timer, int(clear_time_ms))
        _title_clear_scheduled = True
        log(f"Scheduled title clear in {clear_time_ms/1000:.1f} seconds")

def schedule_title_show(video_info):
    """Schedule showing of title after song starts."""
    global _title_show_timer, _pending_title_info
    
    # Cancel any existing timer
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
    
    # Store the title info for later
    _pending_title_info = video_info
    
    # Clear title immediately
    update_text_source("", "")
    
    # Schedule the show
    _title_show_timer = show_title_after_start_callback
    obs.timer_add(_title_show_timer, int(TITLE_SHOW_AFTER_START * 1000))
    log(f"Scheduled title show in {TITLE_SHOW_AFTER_START} seconds")

def cancel_title_timers():
    """Cancel any pending title timers."""
    global _title_clear_timer, _title_show_timer, _pending_title_info, _title_clear_scheduled
    
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
        
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None
        
    _pending_title_info = None
    _title_clear_scheduled = False
```

### 3. Dynamic Video Availability
The playback controller continuously monitors for videos and handles these scenarios:
- **Empty cache startup**: Waits for first video to be downloaded
- **Dynamic addition**: Detects and announces new videos as they're processed
- **Automatic start**: Begins playback as soon as first video is available
- **State synchronization**: Handles cases where media is already playing on startup

```python
def playback_controller():
    """
    Continuously monitors for videos and manages playback.
    Handles dynamic video availability - starts when first video ready.
    """
    # Track changes in video count
    if current_count != _last_cached_count:
        if _last_cached_count == 0 and current_count > 0:
            log(f"First video available! Starting playback with {current_count} video(s)")
        elif current_count > _last_cached_count:
            log(f"New video added to cache. Total videos: {current_count}")
```

### 4. Video Selection Logic (Enhanced)
```python
def select_next_video():
    """
    Select next video for playback using random no-repeat logic.
    Handles single video scenario without adding to played list.
    """
    # Special handling for single video
    if len(available_videos) == 1:
        selected = available_videos[0]
        # Don't add to played list if it's the only video
        return selected
    
    # Multi-video logic with no-repeat
    # ... rest of implementation
```

### 5. Media Source Update Functions (With Error Handling)
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

def update_text_source(song, artist):
    """
    Update OBS Text Source with metadata.
    Must be called from main thread.
    Format: Song - Artist
    """
    try:
        source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        if source:
            # Handle empty text for clearing
            if song and artist:
                text = f"{song} - {artist}"
            elif song:
                text = song
            elif artist:
                text = artist
            else:
                text = ""  # Allow empty when clearing
                
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
            
            if text:
                log(f"Updated text source: {text}")
            return True
        else:
            log(f"WARNING: Text source '{TEXT_SOURCE_NAME}' not found")
            return False
            
    except Exception as e:
        log(f"ERROR updating text source: {e}")
        return False
```

### 6. Source Verification
```python
def verify_sources():
    """Verify that required sources exist and log their status."""
    global _sources_verified
    
    # Check scene, media source, and text source
    # Log verification results once or when sources are missing
    # This helps users identify setup issues
```

### 7. Playback State Detection (Enhanced)
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
            log(f"Playing: {video_info['song']} - {video_info['artist']} "
                f"[{percent}% - {int(current_time/1000)}s / {int(duration/1000)}s]")
```

### 8. Main Playback Controller (State-Based)
```python
def playback_controller():
    """
    Main playback controller with state-based handling.
    Runs on main thread via timer.
    """
    try:
        # Verify sources exist
        if not verify_sources():
            return
        
        # Check if scene is active
        if not is_scene_active():
            if is_playing():
                log("Scene inactive, stopping playback")
                stop_current_playback()
            return
        
        # Check if we have videos to play
        cached_videos = get_cached_videos()
        if not cached_videos:
            # Log waiting message only once
            if not _waiting_for_videos_logged:
                log("Waiting for videos to be downloaded and processed...")
                _waiting_for_videos_logged = True
            return
        
        # Get current media state
        media_state = get_media_state(MEDIA_SOURCE_NAME)
        
        # Handle initial state mismatch
        if not _initial_state_checked:
            _initial_state_checked = True
            if media_state == obs.OBS_MEDIA_STATE_PLAYING and not is_playing():
                log("Media source is already playing - synchronizing state")
                # Stop and restart for clean state
        
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

### 9. State Handlers
```python
def handle_playing_state():
    """Handle currently playing video state."""
    # Sync state if needed
    if not is_playing():
        log("Media playing but state out of sync - updating state")
        set_playing(True)
        return
    
    duration = get_media_duration(MEDIA_SOURCE_NAME)
    current_time = get_media_time(MEDIA_SOURCE_NAME)
    
    if duration > 0 and current_time > 0:
        # Log progress without spamming
        video_id = get_current_playback_video_id()
        if video_id:
            log_playback_progress(video_id, current_time, duration)
        
        # Check if we need to schedule title clear
        global _title_clear_timer, _title_clear_scheduled
        if not _title_clear_scheduled and _title_clear_timer is None:
            # Calculate remaining time
            remaining_ms = duration - current_time
            if remaining_ms > (TITLE_CLEAR_BEFORE_END * 1000) and remaining_ms < ((TITLE_CLEAR_BEFORE_END + 1) * 1000):
                # We're within the window where we should schedule the clear
                schedule_title_clear_from_current(remaining_ms)

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

### 10. Enhanced Video Start Function
```python
def start_next_video():
    """
    Start playing the next video with validation and retry logic.
    Must be called from main thread.
    """
    global _playback_retry_count, _last_progress_log
    
    log("start_next_video called")
    
    # Cancel any pending title timers
    cancel_title_timers()
    
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
    
    # Update media source first
    if update_media_source(video_info['path']):
        # Schedule title display (will clear immediately and show after delay)
        schedule_title_show(video_info)
        
        # Update playback state using accessors
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        log(f"Started playback: {video_info['song']} - {video_info['artist']}")
        
        # Try to get duration and schedule title clear
        duration = get_media_duration(MEDIA_SOURCE_NAME)
        if duration > 0:
            schedule_title_clear(duration)
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

### 11. Timer Management
```python
def start_playback_controller():
    """Start the playback controller timer with proper cleanup."""
    global _playback_timer, _initial_state_checked
    
    try:
        # Reset initial state check
        _initial_state_checked = False
        
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
        # Cancel any pending title timers
        cancel_title_timers()
        
        if _playback_timer:
            obs.timer_remove(_playback_timer)
            _playback_timer = None
            log("Playback controller stopped")
            
    except Exception as e:
        log(f"ERROR stopping playback controller: {e}")

def stop_current_playback():
    """
    Enhanced stop with complete cleanup.
    Must be called from main thread.
    """
    global _last_progress_log, _playback_retry_count
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # ... rest of stop implementation
```

## Key Features Implemented
1. **Text Format**: Changed to "Song - Artist" format for better readability
2. **State Synchronization**: Added handling for media already playing on startup
3. **Source Verification**: Automatic verification of required OBS sources
4. **Cache Scanning**: Fixed to handle video IDs with underscores
5. **Error Handling**: Comprehensive error handling with recovery strategies
6. **Percentage-Based Detection**: More reliable than fixed millisecond thresholds
7. **Progress Logging**: Smart caching prevents log spam
8. **File Validation**: Checks files exist before attempting playback
9. **Retry Logic**: Handles transient failures gracefully
10. **Timer Management**: Proper cleanup prevents multiple timers
11. **Exception Safety**: All functions wrapped in try-catch blocks
12. **Dynamic Video Availability**: Continuously monitors and starts playback when videos become available
13. **Title Display Timing**: Precise control of when titles appear and disappear to avoid text on black screens

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` (increment MINOR version, then PATCH for each fix)
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
- [x] Handle dynamic video availability
- [x] Support empty cache startup
- [x] Announce new videos as they're added
- [x] Change text format to "Song - Artist"
- [x] Add source verification
- [x] Fix cache scanning for complex video IDs
- [x] Add state synchronization
- [x] Implement title display timing (clear 2s before end, show 2s after start)
- [x] Add timer callbacks with proper cleanup
- [x] Prevent timer callback repetition

## Testing Before Commit
1. **Basic Functionality**
   - [ ] Start with empty scene - verify no playback
   - [ ] Switch to player scene - verify playback starts
   - [ ] Let video play to end - verify auto-advance
   - [ ] Switch away from scene - verify playback stops
   - [ ] Switch back to scene - verify playback resumes

2. **Dynamic Video Availability**
   - [ ] Start with empty cache - verify "Waiting for videos..." message
   - [ ] Let first video download - verify auto-start with "First video available!"
   - [ ] Let more videos download - verify "New video added to cache" messages
   - [ ] Verify new videos join playback pool automatically

3. **Title Display Timing**
   - [ ] Verify title appears 2 seconds after song starts
   - [ ] Verify "Scheduled title show in 2.0 seconds" log message
   - [ ] Verify title clears 2 seconds before song ends
   - [ ] Verify "Scheduled title clear in X.X seconds" log message
   - [ ] Verify smooth transitions without text on black screens
   - [ ] Verify timer callbacks only fire once

4. **Edge Cases**
   - [ ] Test with only one video - verify it replays
   - [ ] Test with multiple videos - verify no immediate repeats
   - [ ] Check metadata updates with each video (Song - Artist format)
   - [ ] Test with missing media/text source
   - [ ] Delete a video file while playing - verify recovery
   - [ ] Test with video IDs containing underscores

5. **State Synchronization**
   - [ ] Start playback manually, then reload script - verify state sync
   - [ ] Verify "Media source is already playing - synchronizing state" message
   - [ ] Confirm clean restart after synchronization

6. **Source Verification**
   - [ ] Test with missing scene - verify error message
   - [ ] Test with missing media source - verify warning
   - [ ] Test with missing text source - verify warning
   - [ ] Verify source verification output in logs

7. **Robustness**
   - [ ] Rapid scene switches don't cause crashes
   - [ ] Progress logging appears at 30s intervals
   - [ ] **Verify incremented version in logs**
   - [ ] Test with videos of various lengths
   - [ ] Memory usage remains stable
   - [ ] Script reload doesn't create duplicate timers

8. **Logs to Verify**
   ```
   [ytfast.py] [timestamp] Script version X.Y.Z loaded
   [ytfast.py] [timestamp] Playback controller started
   [ytfast.py] [timestamp] === SOURCE VERIFICATION ===
   [ytfast.py] [timestamp] Scene 'ytfast': ✓ EXISTS
   [ytfast.py] [timestamp] Media Source 'video': ✓ EXISTS (type: ffmpeg_source)
   [ytfast.py] [timestamp] Text Source 'title': ✓ EXISTS
   [ytfast.py] [timestamp] ==========================
   [ytfast.py] [timestamp] Waiting for videos to be downloaded and processed...
   [ytfast.py] [timestamp] First video available! Starting playback with 1 video(s)
   [ytfast.py] [timestamp] Selected: Song Title - Artist Name
   [ytfast.py] [timestamp] Updated media source: filename.mp4
   [ytfast.py] [timestamp] Scheduled title show in 2.0 seconds
   [ytfast.py] [timestamp] Started playback: Song Title - Artist Name
   [ytfast.py] [timestamp] Scheduled title clear in XXX.X seconds
   [ytfast.py] [timestamp] Showing title after delay: Song Title - Artist Name
   [ytfast.py] [timestamp] Updated text source: Song Title - Artist Name
   [ytfast.py] [timestamp] New video added to cache. Total videos: 2
   [ytfast.py] [timestamp] Playing: Song Title - Artist Name [50% - 60s / 120s]
   [ytfast.py] [timestamp] Scheduled title clear in X.X seconds (remaining: X.Xs)
   [ytfast.py] [timestamp] Clearing title before song end
   [ytfast.py] [timestamp] Playback ended, starting next video
   ```

## Commit
After successful testing and user approval with logs, commit with message:  
> *"Implement enhanced playback control with Song-Artist format, state sync, and title timing (Phase 9)"*

*After verification, proceed to Phase 10.*
