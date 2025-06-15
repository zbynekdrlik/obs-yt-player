# Phase 06 – Audio Normalization

## Goal
Implement two-pass FFmpeg loudnorm filter to normalize audio to -14 LUFS. This ensures consistent volume levels across all videos in the playlist.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.3.0` → `1.4.0`)

## Requirements Reference
This phase implements audio normalization from `02-requirements.md`:
- Loudness-normalise audio to -14 LUFS with FFmpeg

## Implementation Details

### Two-Pass Loudnorm Process

#### First Pass - Analysis
```python
def analyze_loudness(input_path):
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
        '-f', 'null',
        '-'
    ]
    # Parse JSON output for loudness parameters
    return loudness_params
```

#### Second Pass - Normalization
```python
def normalize_audio(input_path, video_id):
    # 1. Analyze loudness (first pass)
    params = analyze_loudness(input_path)
    
    # 2. Apply normalization (second pass)
    output_path = f"{video_id}_normalized_temp.mp4"
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-af', f'loudnorm=I=-14:TP=-1:LRA=11:measured_I={params["input_i"]}:...',
        '-c:v', 'copy',  # Copy video stream
        '-c:a', 'aac',   # Re-encode audio
        '-b:a', '192k',  # Audio bitrate
        output_path
    ]
    return output_path
```

### Key Parameters
- **Target Integrated Loudness**: -14 LUFS (streaming standard)
- **Target True Peak**: -1 dBTP
- **Loudness Range**: 11 LU
- **Audio Codec**: AAC at 192 kbps
- **Video**: Copy without re-encoding

### Error Handling
- Catch FFmpeg errors and log them
- Handle corrupt audio streams
- Return None on failure
- Clean up temp files on error
- Support various audio formats (mono/stereo/surround)

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement analyze_loudness function
- [ ] Parse JSON output from FFmpeg
- [ ] Implement normalize_audio with two-pass
- [ ] Copy video stream without re-encoding
- [ ] Handle subprocess errors properly
- [ ] Hide console window on Windows
- [ ] Clean up temporary files
- [ ] Test with various audio formats

## Testing Before Commit
1. Process quiet video - verify volume increases
2. Process loud video - verify volume decreases
3. Use FFmpeg to verify output is -14 LUFS:
   ```
   ffmpeg -i output.mp4 -af loudnorm=I=-14:TP=-1:LRA=11:print_format=summary -f null -
   ```
4. Verify video stream is copied (check codec info)
5. Test with mono audio - should work
6. Test with surround audio - should work
7. Test with corrupt audio - should fail gracefully
8. Verify temp files are cleaned up
9. Check console stays hidden (Windows)
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Implement two-pass audio normalization to -14 LUFS"*

*After verification, proceed to Phase 07.*