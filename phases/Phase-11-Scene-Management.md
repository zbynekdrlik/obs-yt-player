# Phase 11 – Scene Management & Stop Button

## Goal
Implement proper scene transition handling and stop button functionality to ensure clean playback control and resource management.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version (2.2.6 → 2.3.0)
**Remember**: Increment version with EVERY code change during development, not just once per phase.

## Requirements Reference
This phase implements scene management from `02-requirements.md`:
- Handle scene transitions properly
- Stop playback when leaving scene
- Add manual stop control
- Clean up resources on scene exit

## Implementation Summary

### 1. Stop Request State Management
Added thread-safe stop request flag to state module:
```python
# New state flag and accessors
_stop_requested = False

def is_stop_requested():
    """Check if stop has been requested."""
    with _state_lock:
        return _stop_requested

def set_stop_requested(requested):
    """Set stop request flag."""
    global _stop_requested
    with _state_lock:
        _stop_requested = requested

def clear_stop_request():
    """Clear the stop request flag."""
    global _stop_requested
    with _state_lock:
        _stop_requested = False
```

### 2. Enhanced Stop Button
Added stop button to script UI with visual indicator:
```python
# In script_properties()
obs.obs_properties_add_button(
    props,
    "stop_playback",
    "⏹ Stop Playback",
    stop_playback_callback
)

def stop_playback_callback(props, prop):
    """Callback for Stop Playback button."""
    log("Manual stop requested via button")
    # Set stop request flag - playback controller will handle it
    set_stop_requested(True)
    return True
```

### 3. Improved Scene Management
Enhanced scene module with OBS exit handling:
```python
def on_frontend_event(event):
    """Handle OBS frontend events."""
    try:
        if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
            handle_scene_change()
        elif event == obs.OBS_FRONTEND_EVENT_EXIT:
            handle_obs_exit()
        elif event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
            log("OBS finished loading")
            verify_initial_state()
    except Exception as e:
        log(f"ERROR in frontend event handler: {e}")

def handle_obs_exit():
    """Handle OBS exit event."""
    log("OBS exiting - initiating cleanup")
    set_stop_threads(True)
    if is_playing():
        set_stop_requested(True)
    time.sleep(0.1)  # Allow brief time for cleanup
```

### 4. Enhanced Playback Controller
Priority-based request handling:
```python
def playback_controller():
    """Main playback controller with stop request handling."""
    try:
        # Priority 1: Check for stop request
        if is_stop_requested():
            clear_stop_request()
            if is_playing():
                stop_current_playback()
            return
        
        # Priority 2: Check if we're shutting down
        if should_stop_threads():
            if is_playing():
                stop_current_playback()
            return
        
        # Priority 3: Check scene active
        if not is_scene_active():
            if is_playing():
                log("Scene inactive, stopping playback")
                stop_current_playback()
            return
        
        # ... rest of playback logic ...
```

### 5. Complete Source Cleanup
Enhanced stop function with full resource cleanup:
```python
def stop_current_playback():
    """Enhanced stop with complete cleanup."""
    if not is_playing():
        log("No active playback to stop")
        return
    
    try:
        # Clear media source completely
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            obs.obs_source_media_stop(source)
            
            # Clear the file path - THIS IS IMPORTANT
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", "")
            obs.obs_data_set_bool(settings, "unload_when_not_showing", True)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
        
        # Show stopped message briefly
        update_text_source("⏹ Stopped", "")
        
        # Update state
        set_playing(False)
        set_current_video_path(None)
        set_current_playback_video_id(None)
        
        # Clear the stopped message after 2 seconds
        obs.timer_add(clear_stopped_message, 2000)
```

### 6. Resource Protection
Updated cache cleanup to protect playing videos:
```python
def cleanup_removed_videos():
    """Remove videos that are no longer in playlist."""
    current_playing_id = get_current_playback_video_id()
    
    for video_id in cached_videos:
        if video_id not in playlist_ids:
            # Check if it's currently playing
            if video_id == current_playing_id:
                log(f"Skipping removal of currently playing video: {video_id}")
            else:
                videos_to_remove.append(video_id)
```

## Key Improvements Implemented
1. **State-Based Stop Request**: Thread-safe flag checked by playback controller
2. **Complete Source Cleanup**: Media file path cleared to prevent resource locks
3. **User Feedback**: "⏹ Stopped" message shown briefly
4. **Thread Safety**: All state changes through thread-safe accessors
5. **Clean Dependencies**: No circular imports between modules
6. **Comprehensive Error Handling**: Try-except blocks in all critical paths
7. **Graceful Shutdown**: Proper cleanup on OBS exit
8. **Timer Management**: Proper cleanup of all timers
9. **Resource Protection**: Currently playing video protected from deletion
10. **Priority-Based Control**: Stop requests handled before other operations

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` to 2.3.0
- [x] Add stop request state management
- [x] Add Stop Playback button to properties
- [x] Implement stop_playback_callback
- [x] Enhance scene change handling
- [x] Add OBS exit event handling
- [x] Protect playing video from deletion
- [x] Update playback controller with priorities
- [x] Implement complete source cleanup
- [x] Add user feedback messages
- [x] Handle all edge cases

## Testing Before Commit
1. **Stop Button Tests**
   - [ ] Test Stop button during playback - verify immediate stop
   - [ ] Test Stop button when not playing - verify no errors
   - [ ] Spam-click stop button rapidly - verify no crashes
   - [ ] Stop during video transition - verify clean stop

2. **Scene Management**
   - [ ] Switch scenes during playback - verify stop
   - [ ] Return to scene - verify restart
   - [ ] Rapid scene switching - verify no glitches
   - [ ] Scene switch while stop is processing

3. **OBS Exit**
   - [ ] Close OBS during playback - verify cleanup
   - [ ] Check logs for "OBS exiting" message
   - [ ] Verify no error messages on exit

4. **Resource Protection**
   - [ ] Test cleanup with playing video in removed list
   - [ ] Verify playing video not deleted
   - [ ] Check file locks are released

5. **User Feedback**
   - [ ] Verify "⏹ Stopped" appears when stopped
   - [ ] Verify message clears after 2 seconds
   - [ ] Check text source updates properly

6. **Edge Cases**
   - [ ] Stop with missing sources
   - [ ] Stop during network issues
   - [ ] Memory usage over extended use
   - [ ] **Verify version 2.3.0 in logs**
   - [ ] All timers properly cleaned up

7. **Log Verification**
   ```
   [ytfast.py] [timestamp] Script version 2.3.0 loaded
   [ytfast.py] [timestamp] Manual stop requested via button
   [ytfast.py] [timestamp] Playback stopped and all sources cleared
   [ytfast.py] [timestamp] Scene deactivated (was on: other_scene)
   [ytfast.py] [timestamp] Scene inactive, stopping playback
   [ytfast.py] [timestamp] OBS exiting - initiating cleanup
   [ytfast.py] [timestamp] Skipping removal of currently playing video: video_id
   ```

## Known Limitations
- Stop button requires manual click (no hotkey support yet)
- Stopped message duration is fixed at 2 seconds
- No play button to resume after stop (must switch scenes)

## Future Enhancements
- Add Play/Pause buttons
- Support keyboard shortcuts
- Add playback status indicator
- Save stopped state across reloads
- Add progress bar to text source

## Commit
After successful testing and user approval with logs, commit with message:  
> *"Implement scene management and stop button with enhanced cleanup (Phase 11, v2.3.0)"*

*After verification, proceed to Phase 12.*
