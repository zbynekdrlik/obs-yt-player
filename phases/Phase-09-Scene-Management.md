# Phase 09 – Scene Management

## Goal
Handle scene transitions properly - stop playback when leaving the scene, resume when returning, and clean up resources appropriately.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements scene transition handling from `02-requirements.md`:
- Handle stop button & scene transitions
- Media Source control based on scene activity

## Implementation Details

### 1. Scene Change Detection
Update the existing `on_frontend_event`:
```python
def on_frontend_event(event):
    global scene_active
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            scene_name = obs.obs_source_get_name(current_scene)
            scene_active = (scene_name == SCENE_NAME)
            
            # Handle transition
            if scene_active:
                on_scene_activated()
            else:
                on_scene_deactivated()
                
            obs.obs_source_release(current_scene)
```

### 2. Scene Activation Handler
```python
def on_scene_activated():
    """Called when our scene becomes active."""
    global is_playing
    
    # Start playback timer if not already running
    if not obs.timer_enabled(playback_controller):
        obs.timer_add(playback_controller, PLAYBACK_CHECK_INTERVAL)
    
    # Log activation
    log(f"Scene '{SCENE_NAME}' activated - starting playback", "DEBUG")
```

### 3. Scene Deactivation Handler
```python
def on_scene_deactivated():
    """Called when switching away from our scene."""
    global is_playing, current_video_path
    
    # Stop playback timer
    obs.timer_remove(playback_controller)
    
    # Stop current video
    stop_current_video()
    
    # Reset state
    is_playing = False
    current_video_path = None
    
    log(f"Scene '{SCENE_NAME}' deactivated - stopping playback", "DEBUG")
```

### 4. Stop Playback Function
```python
def stop_current_video():
    """Stop the currently playing video."""
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if media_source:
        # Create empty settings to clear the source
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "local_file", "")
        obs.obs_source_update(media_source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(media_source)
    
    # Clear text source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if text_source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", "")
        obs.obs_source_update(text_source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(text_source)
```

### 5. Transition Handling
- Stop video immediately on scene exit
- Don't start new video during transition
- Resume playback when scene is fully active
- Handle rapid scene switching gracefully

## Key Considerations
- Remove timer when scene inactive (save CPU)
- Clear sources to free resources
- Handle preview/program scenes correctly
- Thread-safe state management
- Graceful handling of missing sources
- Timer management using obs.timer_enabled()

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement on_scene_activated
- [ ] Implement on_scene_deactivated
- [ ] Add stop_current_video function
- [ ] Update on_frontend_event handler
- [ ] Handle timer start/stop properly
- [ ] Clear media and text sources
- [ ] Test scene transitions
- [ ] Add appropriate logging

## Testing Before Commit
1. Switch to script scene - verify playback starts
2. Switch away - verify playback stops immediately
3. Switch back - verify playback resumes
4. Rapid scene switching - no crashes or issues
5. Check media source clears when leaving
6. Check text source clears when leaving
7. Verify timer stops when scene inactive
8. Monitor CPU usage when scene inactive
9. Test with scene in preview (Studio Mode)
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add scene transition handling and playback control"*

*After verification, proceed to Phase 10.*