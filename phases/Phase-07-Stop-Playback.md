# Phase 07 – Stop Playback Button & Final Integration

## Goal
Add the Stop Playback button to the UI and finalize all integration points between the various components.

## Components to Implement

### Stop Playback Button
- Add button to script properties UI
- Implement callback to stop current playback
- Clear media source immediately when clicked
- Reset playback state flags
- Ensure button is always responsive

### Integration Points
- Ensure all threads coordinate properly
- Verify scene change handling is robust
- Clean up resources on script unload
- Handle edge cases (missing sources, etc.)

### Cleanup Functions
- Properly signal all threads to stop on script unload
- Clear any playing media when script exits
- Release all OBS references
- Ensure no orphaned threads or processes

## Testing Before Commit
1. Test Stop Playback button during active playback
2. Verify media source clears immediately when clicked
3. Test resuming playback after stopping
4. Check that Stop button works even if no video is playing
5. Test script reload - ensure clean shutdown
6. Verify no orphaned threads after script unload
7. Test scene switching with Stop button
8. Ensure all UI elements remain responsive

## Commit
After successful testing, commit with message:  
> *"Add Stop Playback button and finalize integration"*

*After verification, proceed to Phase 08.*