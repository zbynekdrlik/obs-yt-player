# Phase 03 – Playlist Sync & Core Functions

## Goal
Implement playlist synchronization that fetches video IDs and core functions for metadata retrieval and file management. This phase creates the foundation for the serial processing pipeline.

## Components to Implement

### 1. Playlist Sync Worker
- Fetches YouTube playlist data via **yt‑dlp**
- Extracts video IDs and basic info (title, duration)
- Queues video info for serial processing
- Runs **only** at startup and on *Sync Now* button click
- **NO PERIODIC SYNC** - Due to slow LTE internet

### 2. Metadata Functions
- Primary method: AcoustID fingerprinting (API key: `M6o6ia3dKu`)
- Fallback: Parse YouTube title for artist and song information
- Log transformations in format: *"YT: 'Original Title' → Song: 'Song Name', Artist: 'Artist Name'"*
- These functions will be called during video processing

### 3. File Management Functions
- Filename sanitization to remove invalid filesystem characters
- Cache directory scanning to list existing normalized files
- Cleanup function to remove duplicates and temporary files
- All operations must be thread-safe

## Requirements Reference
This phase implements the "Playlist Synchronisation" section from `02-requirements.md`.

**IMPORTANT**: NO PERIODIC SYNC - Due to slow LTE internet, sync only happens:
- Once at script startup (triggered after tools are ready)
- When user clicks "Sync Now" button

## Key Implementation Points
- Use threading.Event for sync signaling
- Queue contains video info, not actual video files
- Implement robust error handling for network issues
- Must check `tools_ready` flag before using yt-dlp
- Clean up old videos not in current playlist (skip currently playing)

## OBS API Constraints
Per `03-obs_api.md`:
- Heavy work (fetching playlist) must run in background thread
- Any OBS API calls must use `obs.timer_add` to run on main thread

## Testing Before Commit
1. Test playlist fetching with valid URL
2. Verify sync runs once at startup after tools are ready
3. Test "Sync Now" button triggers sync correctly
4. **Verify NO periodic sync occurs** - wait and ensure no automatic resync
5. Test metadata extraction with sample audio files
6. Test filename sanitization with special characters
7. Verify cache cleanup removes old files correctly
8. Test with invalid playlist URL - should log error gracefully
9. Ensure OBS remains responsive during sync

## Commit
After successful testing, commit with message:  
> *"Add playlist sync and core functions for serial processing"*

*After verification, proceed to Phase 04.*