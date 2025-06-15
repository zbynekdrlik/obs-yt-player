# Phase 04 – Video Download

## Goal
Implement the video download functionality using yt-dlp. This phase focuses solely on downloading videos from YouTube to temporary files, preparing them for metadata extraction and audio normalization in subsequent phases.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.1.0` → `1.2.0`)

## Requirements Reference
This phase implements the download portion of the processing pipeline from `02-requirements.md`:
- Process videos **one-by-one**: download → fingerprint → normalise → rename
- Essential for slow internet connections

## Implementation Details

### Download Function (`download_video`)
1. **Input Parameters**
   - `video_id`: YouTube video ID
   - `title`: Video title for logging

2. **Download Process**
   - Use yt-dlp with format selection: `best[height<=1440]`
   - Download to temporary file: `{video_id}_temp.mp4`
   - Show progress at: 0%, 25%, 50%, 75%, 100%
   - Use FFmpeg location for format merging if needed

3. **Error Handling**
   - Remove existing temp file before download
   - Handle timeouts (10 minute default)
   - Verify file exists and has content
   - Return None on failure, path on success

### Process Queue Worker Updates
- Get video from queue
- Check if already cached
- Call download_video function
- Pass to next phase (metadata) on success
- Clean up and continue on failure

### Key Considerations
- Hide console window on Windows
- Log file size after successful download
- Handle network interruptions gracefully
- Support resume if possible
- Thread-safe queue operations

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement download_video function
- [ ] Add progress parsing from yt-dlp output
- [ ] Update process_videos_worker to use new function
- [ ] Handle download errors gracefully
- [ ] Test with various video formats
- [ ] Verify temp file cleanup

## Testing Before Commit
1. Download a short video - verify progress tracking
2. Download a long video - test timeout handling
3. Interrupt network during download - verify error handling
4. Try downloading age-restricted video - should fail gracefully
5. Download video requiring format merge - verify FFmpeg usage
6. Check temp files are created in cache directory
7. Verify console window stays hidden (Windows)
8. Monitor bandwidth usage - should be one video at a time
9. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Implement video download with progress tracking"*

*After verification, proceed to Phase 05.*