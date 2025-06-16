# Phase 04 – Video Download

## Goal
Implement the video download functionality using yt-dlp. Process videos from the queue one-by-one, downloading them to temporary files for subsequent processing.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements the download portion of the processing pipeline from `02-requirements.md`:
- Process videos **one-by-one**: download → fingerprint → normalise → rename
- Essential for slow internet connections

## Implementation Details

### 1. Process Videos Worker
```python
def process_videos_worker():
    """Process videos serially - download, metadata, normalize."""
    global stop_threads
    
    while not stop_threads:
        try:
            # Get video from queue (timeout to check stop_threads)
            video_info = video_queue.get(timeout=1)
            
            # Process this video through all stages
            video_id = video_info['id']
            title = video_info['title']
            
            # Skip if already fully processed
            with state_lock:
                if video_id in cached_videos:
                    continue
            
            # Download video
            temp_path = download_video(video_id, title)
            if not temp_path:
                continue
                
            # TODO: Continue to metadata extraction (Phase 5)
            # TODO: Continue to normalization (Phase 6)
            # TODO: Final rename will happen in Phase 6
            
            # IMPORTANT: Keep temp file for future phases
            # Do NOT delete the downloaded file yet!
            
        except queue.Empty:
            continue
        except Exception as e:
            log(f"Error processing video: {e}", "NORMAL")
```

### 2. Download Function
```python
def download_video(video_id, title):
    """Download video to temporary file."""
    output_path = os.path.join(cache_dir, f"{video_id}_temp.mp4")
    
    # Remove existing temp file
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # First, get video info to log quality
    info_cmd = [
        get_ytdlp_path(),
        '-f', f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]/best',
        '--print', '%(width)s,%(height)s,%(fps)s,%(vcodec)s,%(acodec)s',
        '--no-warnings',
        f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    # Log video quality information
    # Example output: "Video quality: 1920x1080 @ 30fps, video: h264, audio: aac"
    
    # Then download with progress tracking
    cmd = [
        get_ytdlp_path(),
        '-f', f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]/best',
        '--merge-output-format', 'mp4',
        '--ffmpeg-location', get_ffmpeg_path(),
        '--no-playlist',
        '--no-warnings',
        '--progress',
        '--newline',
        '-o', output_path,
        f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    # Execute and parse progress
    # Return output_path on success, None on failure
```

### 3. Download Strategy
- Use yt-dlp for downloading
- Video format: best quality up to 1440p (balance quality/size)
- Format selection: `bestvideo[height<=1440]+bestaudio/best[height<=1440]/best`
  - First try: Download best video + best audio separately and merge
  - Fallback 1: Download best combined format up to 1440p
  - Fallback 2: Download best available format
- Audio: already included in video container
- Save to temporary file first ({video_id}_temp.mp4)

### 4. Quality Logging
Before downloading, query and log video quality information:
- Resolution (width x height)
- Frame rate (fps)
- Video codec (e.g., h264, av01, vp9)
- Audio codec (e.g., aac, opus)

Example log output:
```
[NORMAL] Video quality: 2560x1080 @ 25fps, video: av01.0.12M.08, audio: opus
[NORMAL] Starting download: Video Title (VideoID)
```

### 5. Progress Tracking
Parse yt-dlp progress output:
```python
def parse_progress(line, video_id, title):
    # Look for: [download]  XX.X% of ~XXX.XXMiB at XXX.XXKiB/s
    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
    if match:
        percent = float(match.group(1))
        # Log at milestones: 0%, 25%, 50%, 75%, 100%
```

### 6. Error Handling
- Network interruptions
- Age-restricted videos
- Private/deleted videos
- Timeout after 10 minutes
- Clean up partial downloads

### 7. Important Notes
- **Keep downloaded files**: Downloaded temp files must be preserved for Phase 5 and 6
- **Serial processing**: One video at a time for bandwidth management
- **Skip cached**: Check `cached_videos` to avoid re-downloading
- **Quality priority**: Prioritize high quality (up to 1440p) over small file size
- **Quality transparency**: Log resolution and codecs before download

## Key Implementation Points
- Start process_videos_worker thread in start_worker_threads
- Hide console window on Windows
- Log video quality (resolution, fps, codecs) before download
- Log download progress at milestones only
- Verify downloaded file exists and has size > 0
- Thread-safe operations
- One video at a time (serial processing)
- **DO NOT delete temp files after download**

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement process_videos_worker thread
- [ ] Implement download_video function
- [ ] Add quality information logging
- [ ] Add progress parsing
- [ ] Handle various error cases
- [ ] Start thread in start_worker_threads
- [ ] Test with different video types
- [ ] Verify serial processing
- [ ] **Verify temp files are preserved**

## Testing Before Commit
1. Download a short video - verify progress tracking
2. Download a long video - test timeout handling
3. Interrupt network during download - verify error handling
4. Try downloading age-restricted video - should fail gracefully
5. Download video requiring format merge - verify FFmpeg usage
6. **Check temp files remain in cache directory after download**
7. Verify console window stays hidden (Windows)
8. Monitor bandwidth - should be one video at a time
9. Check queue processing works correctly
10. **Verify version was incremented**
11. **Verify video quality is high (1080p/1440p, not 360p)**
12. **Verify quality information is logged (resolution, fps, codecs)**

## Commit
After successful testing, commit with message:  
> *"Implement video download with progress tracking"*

*After verification, proceed to Phase 05.*