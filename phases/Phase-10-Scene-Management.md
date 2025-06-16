# Phase 10 – Scene Management & Stop Button

## Goal
Implement proper scene transition handling and stop button functionality to ensure clean playback control and resource management.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.8.0 to 1.9.0)

## Requirements Reference
This phase implements scene management from `02-requirements.md`:
- Handle scene transitions properly
- Stop playback when leaving scene
- Add manual stop control
- Clean up resources on scene exit

## Implementation Details

### 1. Enhanced Stop Button
Add stop button to script properties:
```python
def script_properties():
    """Define script properties shown in OBS UI."""
    props = obs.obs_properties_create()
    
    # Playlist URL text field
    obs.obs_properties_add_text(
        props, 
        "playlist_url", 
        "YouTube Playlist URL", 
        obs.OBS_TEXT_DEFAULT
    )
    
    # Cache directory text field
    obs.obs_properties_add_text(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_TEXT_DEFAULT
    )
    
    # Sync Now button
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # Stop Playback button
    obs.obs_properties_add_button(
        props,
        "stop_playback",
        "Stop Playback",
        stop_playback_callback
    )
    
    return props

def stop_playback_callback(props, prop):
    """Callback for Stop Playback button."""
    log("Manual stop requested")
    
    # Use timer to ensure it runs on main thread
    obs.timer_add(stop_playback_once, 100)
    return True

def stop_playback_once():
    """Stop playback once from timer."""
    obs.timer_remove(stop_playback_once)
    
    if is_playing:
        stop_current_playback()
        log("Playback stopped by user")
    else:
        log("No active playback to stop")
```

### 2. Improved Scene Transition Handling
```python
def on_frontend_event(event):
    """Handle OBS frontend events."""
    global scene_active
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        handle_scene_change()
    elif event == obs.OBS_FRONTEND_EVENT_EXIT:
        # Clean shutdown when OBS is closing
        log("OBS exiting, cleaning up...")
        cleanup_on_exit()

def handle_scene_change():
    """Handle scene change events."""
    global scene_active
    
    # Get current scene
    current_scene = obs.obs_frontend_get_current_scene()
    if not current_scene:
        return
    
    scene_name = obs.obs_source_get_name(current_scene)
    was_active = scene_active
    scene_active = (scene_name == SCENE_NAME)
    
    # Handle activation
    if scene_active and not was_active:
        log(f"Scene activated: {scene_name}")
        # Playback will start automatically via playback_controller
        
    # Handle deactivation
    elif not scene_active and was_active:
        log(f"Scene deactivated, was on: {scene_name}")
        # Stop playback immediately
        if is_playing:
            # Use timer to ensure it runs on main thread
            obs.timer_add(stop_on_scene_exit, 100)
    
    obs.obs_source_release(current_scene)

def stop_on_scene_exit():
    """Stop playback when exiting scene."""
    obs.timer_remove(stop_on_scene_exit)
    
    if not scene_active and is_playing:
        stop_current_playback()
        log("Stopped playback on scene exit")
```

### 3. Cleanup Functions
```python
def cleanup_on_exit():
    """Clean up resources when OBS exits."""
    global stop_threads
    
    # Signal all threads to stop
    stop_threads = True
    
    # Stop any active playback
    if is_playing:
        stop_current_playback()
    
    # Clear sources
    clear_all_sources()
    
    log("Cleanup completed")

def clear_all_sources():
    """Clear all source content."""
    # Clear media source
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "local_file", "")
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
    
    # Clear text source
    source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if source:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", "")
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
```

### 4. Resource Protection
```python
def is_video_being_processed(video_id):
    """Check if video is currently being downloaded/processed."""
    # This will be called before deleting files
    return video_id == current_playback_video_id

def cleanup_removed_videos():
    """Remove videos that are no longer in playlist."""
    with state_lock:
        # Find videos to remove
        videos_to_remove = []
        for video_id in cached_videos:
            if video_id not in playlist_video_ids:
                # Check if it's currently playing
                if not is_video_being_processed(video_id):
                    videos_to_remove.append(video_id)
                else:
                    log(f"Skipping removal of currently playing video: {video_id}")
        
        # Remove videos
        for video_id in videos_to_remove:
            video_info = cached_videos[video_id]
            try:
                os.remove(video_info['path'])
                del cached_videos[video_id]
                log(f"Removed: {video_info['artist']} - {video_info['song']}")
            except Exception as e:
                log(f"Error removing video {video_id}: {e}")
        
        if videos_to_remove:
            log(f"Cleaned up {len(videos_to_remove)} removed videos")
```

### 5. Update Playback Controller
Enhance the playback controller with better state management:
```python
def playback_controller():
    """Main playback controller - runs on main thread via timer."""
    global is_playing, current_video_path, current_playback_video_id
    
    # Skip if we're shutting down
    if stop_threads:
        return
    
    # Check if scene is active
    if not scene_active:
        if is_playing:
            log("Scene inactive, stopping playback")
            stop_current_playback()
        return
    
    # Check if we have videos to play
    with state_lock:
        if not cached_videos:
            if is_playing:
                # No videos available anymore
                stop_current_playback()
            return
    
    # Rest of existing playback_controller code...
```

### 6. Update Stop Current Playback
Enhance stop function with better cleanup:
```python
def stop_current_playback():
    """Stop current playback and clear sources."""
    global is_playing, current_video_path, current_playback_video_id
    
    if not is_playing:
        return
    
    # Stop media source
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if source:
        # Stop playback
        obs.obs_source_media_stop(source)
        
        # Clear the file path
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "local_file", "")
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        
        obs.obs_source_release(source)
    
    # Clear text
    update_text_source("", "")
    
    # Update state
    is_playing = False
    current_video_path = None
    current_playback_video_id = None
    
    log("Playback stopped and sources cleared")
```

## Key Considerations
- All source updates must be on main thread
- Protect currently playing video from deletion
- Clean scene transitions without glitches
- Proper resource cleanup on exit
- Manual stop button for user control
- Clear sources when stopping
- Handle edge cases gracefully

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` (increment MINOR version)
- [ ] Add Stop Playback button to properties
- [ ] Implement stop_playback_callback
- [ ] Enhance scene change handling
- [ ] Add cleanup_on_exit function
- [ ] Add clear_all_sources function
- [ ] Protect playing video from deletion
- [ ] Update cleanup_removed_videos
- [ ] Enhance playback_controller checks
- [ ] Improve stop_current_playback
- [ ] Handle OBS exit event

## Testing Before Commit
1. Test Stop button during playback
2. Test Stop button when not playing
3. Switch scenes during playback - verify stop
4. Return to scene - verify restart
5. Close OBS during playback - verify cleanup
6. Test cleanup with playing video in removed list
7. Verify sources cleared on stop
8. Test rapid scene switching
9. Test stop during video transition
10. Verify no resource leaks
11. **Verify version was incremented**
12. **Check all timers cleaned up**

## Commit
After successful testing, commit with message:  
> *"Add scene management and stop button (Phase 10)"*

*After verification, proceed to Phase 11.*