# Phase 04 – Serial Video Processing Pipeline

## Goal
Implement the main processing worker that handles videos **one at a time** through the complete pipeline: download → metadata → normalization → save. This ensures each video is fully processed before the next download begins.

## Requirements
**CRITICAL**: Each video must be **fully processed** before the next download begins:
1. Download video from YouTube
2. Extract metadata (song/artist)
3. Normalize audio to -14 LUFS
4. Save with proper filename
5. Only then process next video

This serial approach is essential for slow internet connections and prevents incomplete files from accumulating.

## Key Implementation Points

### Process Videos Worker
- Fetches one video at a time from the queue
- Checks if video is already cached before downloading
- Downloads to temporary file with yt-dlp
- Extracts metadata using functions from Phase 3
- Normalizes audio using FFmpeg (details in Phase 5)
- Saves with final filename format: `<song>_<artist>_<id>_normalized.mp4`
- Updates cached_videos dictionary
- Cleans up all temporary files

### Download Function
- Uses yt-dlp with resolution limit (MAX_RESOLUTION)
- Downloads to temporary filename first
- Handles download errors gracefully
- Returns path to downloaded file or None on failure

### Integration Points
- Must check `tools_ready` before processing
- Uses metadata functions from Phase 3
- Calls normalization function (implemented in Phase 5)
- Updates global cached_videos with thread safety
- Logs progress at each major step

## Testing Before Commit
1. Queue multiple videos for processing
2. Verify serial processing (one at a time) - monitor network usage
3. Check that each video completes all steps before next starts
4. Verify proper error handling for failed downloads
5. Test that temporary files are cleaned up
6. Monitor CPU and network usage - should show sequential pattern
7. Test with slow/interrupted internet connection
8. Verify cached videos aren't re-downloaded

## Commit
After successful testing, commit with message:  
> *"Implement serial video processing pipeline"*

*After verification, proceed to Phase 05.*