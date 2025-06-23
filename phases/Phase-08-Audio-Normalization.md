# Phase 08 – Audio Normalization

## Goal
Implement audio normalization to -14 LUFS using FFmpeg's loudnorm filter, ensuring consistent volume across all videos.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.8.0 to 1.9.0)

## Requirements Reference
This phase implements audio normalization from `02-requirements.md`:
- Normalize to **-14 LUFS** (standard for streaming platforms)
- Process videos after download and metadata extraction
- Use FFmpeg's two-pass loudnorm for accuracy

## Implementation Details

### 1. Audio Normalization Function
```python
def normalize_audio(input_path, video_id, metadata):
    """
    Normalize audio to -14 LUFS using FFmpeg's loudnorm filter.
    Returns path to normalized file or None on failure.
    """
    try:
        # Generate output filename based on metadata
        safe_song = sanitize_filename(metadata.get('song', 'Unknown'))
        safe_artist = sanitize_filename(metadata.get('artist', 'Unknown'))
        output_filename = f"{safe_song}_{safe_artist}_{video_id}_normalized.mp4"
        output_path = os.path.join(cache_dir, output_filename)
        
        # Skip if already normalized
        if os.path.exists(output_path):
            log(f"Already normalized: {output_filename}")
            return output_path
        
        log(f"Starting normalization: {metadata['artist']} - {metadata['song']}")
        
        # First pass: Analyze audio
        log("Running first pass audio analysis...")
        analysis_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
            '-f', 'null',
            '-'
        ]
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Run analysis
        result = subprocess.run(
            analysis_cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode != 0:
            log(f"FFmpeg analysis failed: {result.stderr}")
            return None
        
        # Extract loudnorm stats from output
        stats = extract_loudnorm_stats(result.stderr)
        if not stats:
            log("Failed to extract loudnorm statistics")
            return None
        
        log(f"Audio analysis complete - Input: {stats['input_i']} LUFS")
        
        # Second pass: Apply normalization
        log("Running second pass normalization...")
        
        # Build normalization filter with measured values
        loudnorm_filter = (
            f"loudnorm=I=-14:TP=-1:LRA=11:"
            f"measured_I={stats['input_i']}:"
            f"measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:"
            f"measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}"
        )
        
        normalize_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-af', loudnorm_filter,
            '-c:v', 'copy',  # Copy video stream without re-encoding
            '-c:a', 'aac',   # Re-encode audio to AAC
            '-b:a', '192k',  # Audio bitrate
            '-y',  # Overwrite output
            output_path
        ]
        
        # Show progress for long operation
        process = subprocess.Popen(
            normalize_cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        
        # Monitor progress
        for line in process.stderr:
            if 'time=' in line:
                # Extract time progress
                time_match = re.search(r'time=(\d+):(\d+):(\d+)', line)
                if time_match:
                    hours, minutes, seconds = map(int, time_match.groups())
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    # Log progress every 30 seconds
                    if total_seconds % 30 == 0:
                        log(f"Normalizing... {total_seconds}s processed")
        
        process.wait()
        
        if process.returncode != 0:
            log(f"FFmpeg normalization failed")
            return None
        
        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            log(f"Normalization complete: {output_filename} ({file_size_mb:.1f} MB)")
            
            # Clean up temp file
            try:
                os.remove(input_path)
                log(f"Removed temp file: {os.path.basename(input_path)}")
            except Exception as e:
                log(f"Error removing temp file: {e}")
            
            return output_path
        else:
            log("Normalization failed - output file missing or empty")
            return None
            
    except subprocess.TimeoutExpired:
        log("Normalization timeout after 5 minutes")
        return None
    except Exception as e:
        log(f"Normalization error: {e}")
        return None

def extract_loudnorm_stats(ffmpeg_output):
    """
    Extract loudnorm statistics from FFmpeg output.
    """
    try:
        # Find JSON output in stderr
        json_start = ffmpeg_output.rfind('{')
        json_end = ffmpeg_output.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            log("No JSON data found in FFmpeg output")
            return None
        
        json_str = ffmpeg_output[json_start:json_end]
        stats = json.loads(json_str)
        
        # Verify required fields
        required_fields = ['input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset']
        for field in required_fields:
            if field not in stats:
                log(f"Missing required field: {field}")
                return None
        
        return stats
        
    except json.JSONDecodeError as e:
        log(f"Failed to parse loudnorm JSON: {e}")
        return None
    except Exception as e:
        log(f"Error extracting loudnorm stats: {e}")
        return None

def sanitize_filename(text):
    """
    Sanitize text for use in filename.
    """
    # Remove/replace invalid filename characters
    invalid_chars = '<>:"|?*\\/'  # Invalid on Windows
    for char in invalid_chars:
        text = text.replace(char, '_')
    
    # Remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Limit length and clean up
    text = text[:50].strip().rstrip('.')
    
    return text or 'Unknown'
```

### 2. Integration with Process Worker
Update process_videos_worker to include normalization:
```python
# In process_videos_worker, after metadata extraction and cleaning:

# Normalize audio
normalized_path = normalize_audio(temp_path, video_id, metadata)
if not normalized_path:
    log(f"Failed to normalize: {title}")
    continue

# Update cached videos registry
with state_lock:
    cached_videos[video_id] = {
        'path': normalized_path,
        'song': metadata['song'],
        'artist': metadata['artist'],
        'normalized': True
    }

log(f"Video ready for playback: {metadata['artist']} - {metadata['song']}")

# TODO: Continue to Phase 09 (Playback Control)
```

## Audio Normalization Details

### Target Levels
- **Integrated Loudness**: -14 LUFS (streaming standard)
- **True Peak**: -1 dBTP (prevent clipping)
- **Loudness Range**: 11 LU (dynamic range target)

### Two-Pass Process
1. **First Pass**: Analyze audio to measure current levels
2. **Second Pass**: Apply correction based on measurements

### FFmpeg Loudnorm Filter
The loudnorm filter implements EBU R128 loudness normalization:
- More accurate than simple peak normalization
- Preserves dynamic range
- Prevents over-compression
- Industry standard for streaming

## Key Considerations
- Two-pass process ensures accuracy
- Video stream copied without re-encoding (fast)
- Audio re-encoded to AAC 192k
- Progress monitoring for long videos
- Temp files cleaned up after success
- Filename sanitization for compatibility
- Skip if already normalized

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` (increment MINOR version)
- [ ] Implement normalize_audio function
- [ ] Implement extract_loudnorm_stats helper
- [ ] Implement sanitize_filename helper
- [ ] Add two-pass loudnorm processing
- [ ] Add progress monitoring
- [ ] Handle timeout for long videos
- [ ] Clean up temp files after success
- [ ] Update cached_videos registry
- [ ] Integrate with process_videos_worker

## Testing Before Commit
1. Process video with quiet audio - verify boost
2. Process video with loud audio - verify reduction
3. Process already normalized video - verify skip
4. Test with very long video (>10 minutes)
5. Test with corrupted audio
6. Verify temp files are cleaned up
7. Check filename sanitization with special chars
8. Verify video quality unchanged (copied)
9. Test timeout handling
10. Check cached_videos registry updated
11. **Verify version was incremented**
12. **Monitor FFmpeg console output hidden**

## Commit
After successful testing, commit with message:  
> *"Add audio normalization to -14 LUFS (Phase 8)"*

*After verification, proceed to Phase 09.*
