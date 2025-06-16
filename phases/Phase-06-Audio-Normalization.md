# Phase 06 – Audio Normalization & Final Rename

## Goal
Implement two-pass FFmpeg loudnorm filter to normalize audio to -14 LUFS, then rename the file to its final format with metadata. This completes the video processing pipeline.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements from `02-requirements.md`:
- Loudness-normalise audio to -14 LUFS with FFmpeg
- Sanitise filenames: `<song>_<artist>_<id>_normalized.mp4`

## Implementation Details

### 1. Two-Pass Loudnorm Process

#### First Pass - Analysis
```python
def analyze_loudness(input_path):
    """Analyze audio loudness using FFmpeg."""
    cmd = [
        get_ffmpeg_path(),
        '-i', input_path,
        '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
        '-f', 'null',
        '-'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse JSON from stderr
    json_start = result.stderr.rfind('{')
    if json_start != -1:
        json_str = result.stderr[json_start:]
        return json.loads(json_str)
    
    return None
```

#### Second Pass - Normalization
```python
def normalize_audio(input_path, output_path, loudness_params):
    """Apply loudness normalization."""
    # Build loudnorm filter with measured values
    loudnorm_filter = (
        f'loudnorm=I=-14:TP=-1:LRA=11:'
        f'measured_I={loudness_params["input_i"]}:'
        f'measured_LRA={loudness_params["input_lra"]}:'
        f'measured_TP={loudness_params["input_tp"]}:'
        f'measured_thresh={loudness_params["input_thresh"]}:'
        f'offset={loudness_params["target_offset"]}'
    )
    
    cmd = [
        get_ffmpeg_path(),
        '-i', input_path,
        '-af', loudnorm_filter,
        '-c:v', 'copy',      # Copy video stream
        '-c:a', 'aac',       # Re-encode audio
        '-b:a', '192k',      # Audio bitrate
        '-y',                # Overwrite output
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0
```

### 2. Complete Normalization Process
```python
def normalize_video(input_path, video_id, song, artist):
    """Normalize audio and rename to final format."""
    try:
        # Analyze loudness
        params = analyze_loudness(input_path)
        if not params:
            log("Failed to analyze loudness", "NORMAL")
            return None
        
        # Create temporary normalized file
        temp_normalized = os.path.join(cache_dir, f"{video_id}_normalized_temp.mp4")
        
        # Apply normalization
        if not normalize_audio(input_path, temp_normalized, params):
            log("Failed to normalize audio", "NORMAL")
            return None
        
        # Create final filename
        final_filename = sanitize_filename(song, artist, video_id)
        final_path = os.path.join(cache_dir, final_filename)
        
        # Rename to final name
        os.rename(temp_normalized, final_path)
        
        # Clean up original temp file
        os.remove(input_path)
        
        log(f"Normalized and saved: {final_filename}", "NORMAL")
        return final_path
        
    except Exception as e:
        log(f"Normalization error: {e}", "NORMAL")
        return None
```

### 3. Filename Sanitization
```python
def sanitize_filename(song, artist, video_id):
    """Create safe filename from metadata."""
    def clean_string(s):
        # Remove non-ASCII characters
        s = unicodedata.normalize('NFKD', s)
        s = s.encode('ASCII', 'ignore').decode('ASCII')
        
        # Replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            s = s.replace(char, '_')
        
        # Remove multiple underscores and trim
        s = re.sub(r'_+', '_', s)
        s = s.strip('_. ')
        
        # Limit length
        return s[:50] if s else "unknown"
    
    clean_song = clean_string(song)
    clean_artist = clean_string(artist)
    
    return f"{clean_song}_{clean_artist}_{video_id}_normalized.mp4"
```

### 4. Update Cached Videos
```python
# In process_videos_worker, after successful normalization:
with state_lock:
    cached_videos[video_id] = {
        "path": final_path,
        "song": song,
        "artist": artist,
        "normalized": True
    }
```

## Key Parameters
- **Target Integrated Loudness**: -14 LUFS (streaming standard)
- **Target True Peak**: -1 dBTP
- **Loudness Range**: 11 LU
- **Audio Codec**: AAC at 192 kbps
- **Video**: Copy without re-encoding

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement analyze_loudness function
- [ ] Implement normalize_audio function
- [ ] Implement normalize_video wrapper
- [ ] Implement sanitize_filename function
- [ ] Update process_videos_worker integration
- [ ] Update cached_videos after success
- [ ] Clean up all temporary files
- [ ] Handle errors gracefully

## Testing Before Commit
1. Process quiet video - verify volume increases
2. Process loud video - verify volume decreases
3. Verify output is -14 LUFS using FFmpeg
4. Check final filename format is correct
5. Verify special characters in metadata are handled
6. Test with very long song/artist names
7. Verify video stream is copied (not re-encoded)
8. Check all temp files are cleaned up
9. Verify cached_videos is updated correctly
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Implement audio normalization and final file naming"*

*After verification, proceed to Phase 07.*