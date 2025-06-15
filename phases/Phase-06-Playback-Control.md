# Phase 06 – Playback Control & Scene Integration

## Goal
Implement the core playback logic:

- Detect active scene (match script filename)
- Update Media Source (`video`) and Text Source (`title`)
- Random playback without repeats
- React to `OBS_FRONTEND_EVENT_SCENE_CHANGED`
- Start/stop playback based on scene state

## Requirements Reference
This phase implements the "Playback Logic" section from `02-requirements.md`.

## Key Implementation Points

### Scene Detection
- Monitor OBS frontend events for scene changes
- Check if active scene name matches script filename
- Start playback timer when scene becomes active
- Stop playback when scene becomes inactive

### Playback Controller
- Runs on main thread via `obs.timer_add`
- Checks if current media is still playing
- Selects random video from cached videos
- Tracks played videos to avoid repeats
- Resets played list when all videos have been played

### Media Updates
- Update Media Source with video file path
- Update Text Source with "Song - Artist" format
- Defer updates until scene transitions complete
- Handle missing sources gracefully

### State Management
- Track currently playing video
- Maintain played videos list
- Protect shared state with locks
- Clear media source when playback stops

## OBS API Constraints
Per `03-obs_api.md`:
- All OBS API calls must run on main thread
- Use `obs.timer_add` for periodic checks
- Release all OBS references properly

## Testing Before Commit
1. Create scene named after script (e.g., 'ytfast')
2. Add Media Source named 'video' to the scene
3. Add Text Source named 'title' to the scene
4. Verify playback starts when scene is activated
5. Check random selection without repeats
6. Verify playback stops when switching scenes
7. Test that all videos play before list resets
8. Ensure smooth scene transitions
9. Check metadata displays correctly in text source
10. Verify no memory leaks from OBS references

## Commit
After successful testing, commit with message:  
> *"Implement playback control and OBS scene integration"*

*After verification, proceed to Phase 07.*