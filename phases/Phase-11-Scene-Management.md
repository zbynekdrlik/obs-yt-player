# Phase 11 – Scene Management

## Goal
Implement proper scene transition handling functionality to ensure clean playback control and resource management.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version (2.2.6 → 2.3.0)
**Bug fixes and enhancements** → Increment PATCH versions:
- v2.3.1: Scene return fix
- v2.3.5: Title flash fix
- v2.3.6-2.3.7: Transition handling
- v2.3.8: Removed stop button functionality

**Remember**: Increment version with EVERY code change during development, not just once per phase.

## Requirements Reference
This phase implements scene management from `02-requirements.md`:
- Handle scene transitions properly
- Stop playback when leaving scene
- Clean up resources on scene exit
- Support transition-aware playback (start on transition begin, stop after transition end)

## Implementation Summary

### 1. Enhanced Scene Management
Scene module with OBS exit handling:
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
    time.sleep(0.1)  # Allow brief time for cleanup
```

### 2. Enhanced Playback Controller
Priority-based request handling:
```python
def playback_controller():
    """Main playback controller with scene management."""
    try:
        # Priority 1: Check if we're shutting down
        if should_stop_threads():
            if is_playing():
                stop_current_playback()
            return
        
        # Priority 2: Check scene active
        if not is_scene_active():
            if is_playing():
                log("Scene inactive, stopping playback")
                stop_current_playback()
            return
        
        # ... rest of playback logic ...
```

### 3. Complete Source Cleanup (v2.3.5)
Enhanced stop function without status messages to prevent UI flashing:
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
        
        # Clear text source - no status messages to prevent flashing
        update_text_source("", "")
        
        # Update state
        set_playing(False)
        set_current_video_path(None)
        set_current_playback_video_id(None)
```

### 4. Resource Protection
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

### 5. Scene Return Fix (v2.3.1)
Fixed issue where playback wouldn't restart when returning to scene:
```python
def handle_playing_state():
    """Handle currently playing video state."""
    if not is_playing():
        log("Media playing but state out of sync - updating state")
        # Check if we actually have valid playback info
        current_video_id = get_current_playback_video_id()
        current_path = get_current_video_path()
        
        if not current_video_id or not current_path:
            # We don't have valid playback info, so stop and restart
            log("No valid playback info - stopping and restarting")
            source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
            if source:
                obs.obs_source_media_stop(source)
                obs.obs_source_release(source)
            # Now start fresh
            start_next_video()
            return
```

### 6. Transition Handling (v2.3.6-2.3.7)
Added proper scene transition support using available OBS events:
```python
def handle_scene_change():
    """Handle scene change events with transition awareness."""
    global _last_scene_change_time, _pending_deactivation, _deactivation_timer
    
    current_time = time.time() * 1000  # Convert to milliseconds
    time_since_last_change = current_time - _last_scene_change_time
    _last_scene_change_time = current_time
    
    # Get transition duration
    transition_duration = obs.obs_frontend_get_transition_duration()
    
    # Check if this is likely a transition
    is_likely_transition = (time_since_last_change < 100) or is_studio_mode_active()
    
    if is_active:
        # Scene becoming active - start immediately
        log(f"Scene activated: {scene_name}")
        set_scene_active(True)
        # Playback controller will handle starting
        
    else:
        # Scene becoming inactive
        if is_likely_transition and transition_duration > 300:
            # This is likely a transition - delay the deactivation
            log(f"Scene transitioning out, delaying stop for {transition_duration}ms")
            _pending_deactivation = True
            
            # Set timer for deactivation after transition completes
            if _deactivation_timer:
                obs.timer_remove(delayed_deactivation)
            _deactivation_timer = delayed_deactivation
            obs.timer_add(_deactivation_timer, int(transition_duration))
```

## Key Improvements Implemented
1. **Complete Source Cleanup**: Media file path cleared to prevent resource locks
2. **No Status Messages** (v2.3.5): Removed "Ready" and "⏹ Stopped" to prevent UI flashing
3. **Thread Safety**: All state changes through thread-safe accessors
4. **Clean Dependencies**: No circular imports between modules
5. **Comprehensive Error Handling**: Try-except blocks in all critical paths
6. **Graceful Shutdown**: Proper cleanup on OBS exit
7. **Timer Management**: Proper cleanup of all timers
8. **Resource Protection**: Currently playing video protected from deletion
9. **Scene Return Fix** (v2.3.1): Playback properly restarts when returning to scene
10. **Transition Support** (v2.3.6-2.3.7): Start immediately on transition to scene, continue until transition completes when leaving
11. **Simplified Interface** (v2.3.8): Removed manual stop button for cleaner, automatic control

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` to 2.3.0
- [x] Enhance scene change handling
- [x] Add OBS exit event handling
- [x] Protect playing video from deletion
- [x] Update playback controller with priorities
- [x] Implement complete source cleanup
- [x] Handle all edge cases
- [x] Fix scene return playback issue (v2.3.1)
- [x] Remove status messages to fix UI flashing (v2.3.5)
- [x] Add transition detection and handling (v2.3.6-2.3.7)
- [x] Remove stop button functionality (v2.3.8)

## Testing Before Commit
1. **Scene Management**
   - [x] Switch scenes during playback - verify stop
   - [x] Return to scene - **verify playback restarts** (v2.3.1 fix)
   - [x] Rapid scene switching - verify no glitches

2. **Transition Handling** (v2.3.6-2.3.7)
   - [x] Test with 5+ second transitions
   - [x] Verify video starts immediately when transitioning TO scene
   - [x] Verify video continues playing during fade-out
   - [x] Test in Studio Mode (preview/program)
   - [x] Test with different transition types

3. **OBS Exit**
   - [x] Close OBS during playback - verify cleanup
   - [x] Check logs for "OBS exiting" message
   - [x] Verify no error messages on exit

4. **Resource Protection**
   - [x] Test cleanup with playing video in removed list
   - [x] Verify playing video not deleted
   - [x] Check file locks are released

5. **User Experience**
   - [x] Verify no "⏹ Stopped" or "Ready" messages (v2.3.5)
   - [x] Verify clean transitions without UI flashing
   - [x] Check text source updates properly

6. **Edge Cases**
   - [x] Stop with missing sources
   - [x] Stop during network issues
   - [x] Memory usage over extended use
   - [x] **Verify version 2.3.8 in logs**
   - [x] All timers properly cleaned up

7. **Log Verification**
   ```
   [ytfast.py] [timestamp] Script version 2.3.8 loaded
   [ytfast.py] [timestamp] Playback stopped and all sources cleared
   [ytfast.py] [timestamp] Scene transitioning out, delaying stop for 5000ms
   [ytfast.py] [timestamp] Deactivating scene after transition delay
   [ytfast.py] [timestamp] Scene activated: ytfast
   [ytfast.py] [timestamp] No valid playback info - stopping and restarting
   [ytfast.py] [timestamp] start_next_video called
   [ytfast.py] [timestamp] Started playback: Song - Artist
   ```

## Known Limitations
- Transition detection relies on timing and Studio Mode detection
- No manual playback control (by design for simplicity)

## Future Enhancements
- Add Play/Pause buttons if needed
- Support keyboard shortcuts
- Add playback status indicator
- Save stopped state across reloads
- Add progress bar to text source
- Detect transition events more precisely when OBS API supports it

## Commit
After successful testing and user approval with logs, commit with message:  
> *"Complete Phase 11: Scene management with transition support and simplified interface (v2.3.8)"*

*After verification, proceed to Phase 12.*
