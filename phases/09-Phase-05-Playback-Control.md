# 09‑Phase 05 – Playback Control & Scene Logic

## Goal
Implement random playback orchestration:

- On first normalised video ready **and** scene live, start playback in Media Source `video`.
- Maintain `played_videos` list to avoid repeats.
- Switch video when:
  - Media ends.
  - Stop pressed on source.
  - Scene transitions out (after transition, not during).
- Update Text Source `title` with `<song> - <artist>` (metadata from Phase 06).

## Constraints
- All OBS API calls on main thread (`obs.timer_add`).
- Debounce state checks to ≤ 1 Hz.

## Commit
Suggested commit message:  
> *"Add playback controller with random no‑repeat logic."*