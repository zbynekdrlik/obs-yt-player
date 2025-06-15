# Phase 05 – Audio Normalization Thread

## Goal
Create a worker that:

- Monitors `normalize_queue` for downloaded videos.
- Runs FFmpeg loudnorm (−14 LUFS).
- Replaces temp files atomically.
- Adds normalized videos to `ready_videos` list.

## Notes
- Use two‑pass loudnorm for accuracy.
- Handle subprocess errors and log them.

## Commit
Suggested commit message:  
> *"Add audio normalization with FFmpeg loudnorm."*

*After verification, proceed to Phase 06.*