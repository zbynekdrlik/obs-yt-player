# Phase 06 – Playback Control & Scene Integration

## Goal
Implement the core playback logic:

- Detect active scene (match script filename).
- Update Media Source (`video`) and Text Source (`title`).
- Random playback without repeats.
- Handle *Stop Playback* button.
- React to `OBS_FRONTEND_EVENT_SCENE_CHANGED`.

## Requirements Reference
This phase implements the "Playback Logic" section from `02-requirements.md`.

## Details
- Defer media updates until transitions complete.
- Use `obs.timer_add` for main‑thread OBS API calls.
- Protect `currently_playing` with locks.
- Follow all constraints from `03-obs_api.md`.

## Testing Before Commit
1. Create scene named 'ytfast' with Media and Text sources
2. Verify scene detection works correctly
3. Test random playback without repeats
4. Check scene transition handling
5. Test Stop Playback button
6. Verify media source updates properly
7. Check text source shows correct metadata

## Commit
After successful testing, commit with message:  
> *"Implement playback control and OBS scene integration."*

*After verification, proceed to Phase 07.*