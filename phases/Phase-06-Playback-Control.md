# Phase 06 – Playback Control & Scene Integration

## Goal
Implement the core playback logic:

- Detect active scene (match script filename).
- Update Media Source (`video`) and Text Source (`title`).
- Random playback without repeats.
- Handle *Stop Playback* button.
- React to `OBS_FRONTEND_EVENT_SCENE_CHANGED`.

## Details
- Defer media updates until transitions complete.
- Use `obs.timer_add` for main‑thread OBS API calls.
- Protect `currently_playing` with locks.

## Commit
Suggested commit message:  
> *"Implement playback control and OBS scene integration."*

*After verification, proceed to Phase 07.*