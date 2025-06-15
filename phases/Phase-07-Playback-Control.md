# Phase 07 – Playback Control

## Goal
Implement random video playback through OBS Media Source with metadata display. This phase handles the main playback logic when the scene is active.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.4.0` → `1.5.0`)

## Requirements Reference
This phase implements playback logic from `02-requirements.md`:
- Media Source `video`, Text Source `title`
- Random no-repeat playback
- Handle stop button & scene transitions

## Implementation Details

### 1. Playback State Management
```python
# Global state variables
is_playing = False
current_video_path = None
played_videos = []  # Track played video IDs
next_check_time = 0
```

### 2. Video Selection Logic
```python
def select_next_video():
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

### 3. Playback Controller (Main Thread)
```python
def playback_controller():
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

### 4. Media Control Functions
```python
def play_next_video():
    video_info = select_next_video()
    if not video_info:
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
    # Check media source state
    # Return True if playback finished
```

### 5. OBS Source Updates
- Get source by name
- Update settings
- Release references properly
- Handle missing sources gracefully

## Key Considerations
- All OBS API calls on main thread
- Use obs.timer_add for playback_controller
- Proper source reference management
- Thread-safe state access
- Handle empty cache gracefully

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Add playback state variables
- [ ] Implement select_next_video logic
- [ ] Implement playback_controller timer
- [ ] Add media source update function
- [ ] Add text source update function
- [ ] Implement media_ended detection
- [ ] Handle scene active/inactive
- [ ] Test with various cache states

## Testing Before Commit
1. Start with empty cache - verify no crash
2. Add one video - verify it loops
3. Add multiple videos - verify random order
4. Verify no repeats until all played
5. Switch scenes - verify playback stops/starts
6. Check metadata displays correctly
7. Verify smooth transitions between videos
8. Test with missing media/text source
9. Monitor CPU usage - should be minimal
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add random video playback with metadata display"*

*After verification, proceed to Phase 08.*