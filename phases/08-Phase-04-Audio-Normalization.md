# 08‑Phase 04 – Audio Normalisation

## Goal
Add a **normalisation_worker** that:

1. Performs two‑pass `ffmpeg -af loudnorm=I=-14:LRA=11:TP=-1.5` on each downloaded file not yet ending in `_normalized.mp4`.
2. Appends `_normalized` suffix to filename.
3. Uses at most one concurrent FFmpeg process.
4. Skips file if it's currently playing.

## Commit
Suggested commit message:  
> *"Implement audio normalisation worker (−14 LUFS)."*