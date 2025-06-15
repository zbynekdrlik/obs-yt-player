# Phase 04 – Caching & File Management

## Goal
Add functions that handle:

- Filename sanitization: `<song>_<artist>_<id>_normalized.mp4`.
- Duplicate management (keep only newest).
- Cleanup of `.part` files on startup.
- Thread‑safe file operations.

## Requirements Reference
This phase implements the "Caching & File Management" section from `02-requirements.md`.

## Key Functions
- `sanitize_filename(title, artist, video_id)`
- `get_cached_videos()` → list of normalized files in cache dir.
- `cleanup_cache()` → remove duplicates and temp files.

## Implementation Notes
- Follow naming convention from requirements
- Ensure thread-safe file operations with proper locking
- Handle edge cases (invalid characters, long filenames)

## Testing Before Commit
1. Create test files with various naming patterns
2. Verify sanitize_filename handles special characters
3. Test duplicate detection and removal
4. Verify .part file cleanup works
5. Check thread safety with concurrent operations
6. Ensure currently playing files are not deleted

## Commit
After successful testing, commit with message:  
> *"Implement cache management and filename sanitization."*

*After verification, proceed to Phase 05.*