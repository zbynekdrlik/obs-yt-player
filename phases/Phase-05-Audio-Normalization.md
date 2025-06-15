# Phase 05 – Audio Normalization Implementation

## Goal
Implement the two-pass FFmpeg loudnorm filter for consistent audio levels at -14 LUFS. This function will be called as part of the serial processing pipeline.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.1.0` → `1.2.0`)

## Requirements Reference
This phase implements audio normalization as specified in `02-requirements.md` (loudness-normalise to -14 LUFS).

## Implementation Details

### Two-Pass Loudnorm Process
1. **First Pass - Analysis**
   - Run FFmpeg with loudnorm filter to analyze audio
   - Extract loudness statistics (input levels, true peak, etc.)
   - Parse the JSON output from FFmpeg

2. **Second Pass - Normalization**
   - Apply loudnorm filter with measured values from first pass
   - Target: -14 LUFS (standard for streaming platforms)
   - Copy video stream without re-encoding
   - Re-encode audio with AAC codec at 192k bitrate

### Key Considerations
- Use temporary file for normalized output
- Atomic file operations to prevent corruption
- Handle subprocess errors and log them appropriately
- Must check `tools_ready` before using FFmpeg
- Follow `03-obs_api.md` constraints (subprocess with CREATE_NO_WINDOW on Windows)

### Error Handling
- Gracefully handle corrupt or problematic audio streams
- Return None on failure to allow pipeline to continue
- Clean up temporary files on error
- Log specific FFmpeg errors for debugging

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement normalize_audio function
- [ ] Add two-pass loudnorm logic
- [ ] Handle errors gracefully
- [ ] Clean up temporary files
- [ ] Test with various audio formats

## Testing Before Commit
1. Process a video with quiet audio - verify it gets louder
2. Process a video with loud audio - verify it gets quieter  
3. Check output is at -14 LUFS using FFmpeg or audio analysis tool
4. Verify video stream is copied (not re-encoded) - check file info
5. Test error handling with corrupt files
6. Ensure Windows console stays hidden during processing
7. Verify temporary files are cleaned up
8. Test with various audio formats (mono, stereo, surround)
9. **Verify version was incremented in script**

## Commit
After successful testing, commit with message:  
> *"Add two-pass audio normalization with FFmpeg loudnorm"*

*After verification, proceed to Phase 06.*