# Phase 05 – Audio Normalization Thread

## Goal
Create a worker that:

- Monitors `normalize_queue` for downloaded videos.
- Runs FFmpeg loudnorm (−14 LUFS).
- Replaces temp files atomically.
- Adds normalized videos to `ready_videos` list.

## Requirements Reference
This phase implements audio normalization as specified in `02-requirements.md` (loudness-normalise to -14 LUFS).

## Notes
- Use two‑pass loudnorm for accuracy.
- Handle subprocess errors and log them.
- Must check `tools_ready` before using FFmpeg.
- Follow `03-obs_api.md` constraints (subprocess with CREATE_NO_WINDOW on Windows).

## Testing Before Commit
1. Queue a test video for normalization
2. Verify FFmpeg runs with correct parameters
3. Check output is normalized to -14 LUFS
4. Test atomic file replacement
5. Verify error handling for corrupt files
6. Ensure Windows doesn't show console windows

## Commit
After successful testing, commit with message:  
> *"Add audio normalization with FFmpeg loudnorm."*

*After verification, proceed to Phase 06.*