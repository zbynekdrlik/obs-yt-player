# 10‑Phase 06 – Metadata Retrieval

## Goal
Implement a **metadata_worker**:

1. Extract temporary audio with `yt-dlp -f bestaudio`.
2. Generate fingerprint via AcoustID (`M6o6ia3dKu`); on success, set `song`, `artist`.
3. Fallback: parse YouTube title to derive metadata.
4. Store metadata in filename & in-memory dict; update Text Source via main thread.

## Commit
Suggested commit message:  
> *"Add metadata worker (AcoustID + title fallback)."*