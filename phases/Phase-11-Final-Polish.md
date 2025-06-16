# Phase 11 – Final Polish & Optimization

## Goal
Final testing, optimization, and polish to ensure a production-ready script with robust error handling and optimal performance.

## Version Increment
**This phase finalizes the script** → Increment to 2.0.0 (major release)

## Requirements Reference
This phase ensures all requirements from `02-requirements.md` are fully implemented and optimized:
- Verify all features work together seamlessly
- Optimize performance and resource usage
- Add final error handling and edge cases
- Complete documentation

## Implementation Details

### 1. Scan Cache on Startup
```python
def scan_existing_cache():
    """Scan cache directory for existing normalized videos."""
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return
    
    log("Scanning cache for existing videos...")
    found_count = 0
    
    # Look for normalized videos
    for file_path in cache_path.glob("*_normalized.mp4"):
        try:
            # Extract video ID from filename
            # Format: song_artist_videoId_normalized.mp4
            filename = file_path.stem  # Remove .mp4
            parts = filename.rsplit('_', 2)  # Split from right
            
            if len(parts) >= 3 and parts[2] == 'normalized':
                video_id = parts[1]
                
                # Try to extract metadata from filename
                metadata_parts = parts[0].split('_', 1)
                if len(metadata_parts) == 2:
                    song, artist = metadata_parts
                else:
                    song = parts[0]
                    artist = "Unknown Artist"
                
                # Add to cached videos
                with state_lock:
                    if video_id not in cached_videos:
                        cached_videos[video_id] = {
                            'path': str(file_path),
                            'song': song.replace('_', ' '),
                            'artist': artist.replace('_', ' '),
                            'normalized': True
                        }
                        found_count += 1
                        
        except Exception as e:
            log(f"Error scanning file {file_path}: {e}")
    
    if found_count > 0:
        log(f"Found {found_count} existing videos in cache")
```

### 2. Add to Tools Setup Worker
Update tools_setup_worker to scan cache after tools are ready:
```python
def tools_setup_worker():
    """Background thread for setting up tools."""
    global stop_threads
    
    while not stop_threads:
        try:
            # Ensure cache directory exists
            if not ensure_cache_directory():
                time.sleep(TOOLS_CHECK_INTERVAL)
                continue
            
            # Try to setup tools
            if setup_tools():
                # Tools are ready
                log("Tools setup complete")
                
                # Scan existing cache
                scan_existing_cache()
                
                # Trigger startup sync
                trigger_startup_sync()
                break
            
            # Rest of existing code...
```

### 3. Progress Summary Logging
```python
def log_processing_summary():
    """Log summary of processing progress."""
    with state_lock:
        total_videos = len(playlist_video_ids)
        cached_count = len(cached_videos)
        pending_count = video_queue.qsize()
        
    log(f"Progress: {cached_count}/{total_videos} videos ready, {pending_count} pending")

# Add to process_videos_worker after each video:
log_processing_summary()
```

### 4. Robust Error Recovery
```python
def handle_corrupt_video(video_id, file_path):
    """Handle corrupted video files."""
    log(f"Handling corrupt video: {video_id}")
    
    try:
        # Remove from cache registry
        with state_lock:
            if video_id in cached_videos:
                del cached_videos[video_id]
        
        # Delete corrupt file
        if os.path.exists(file_path):
            os.remove(file_path)
            log(f"Removed corrupt file: {file_path}")
        
        # Re-queue for download
        video_info = {
            'id': video_id,
            'title': 'Unknown (re-download)',
            'duration': 0
        }
        video_queue.put(video_info)
        log(f"Re-queued video {video_id} for download")
        
    except Exception as e:
        log(f"Error handling corrupt video: {e}")
```

### 5. Performance Optimizations
```python
# Add to module constants
MAX_CONCURRENT_DOWNLOADS = 1  # Already serial, but make it explicit
CACHE_SCAN_BATCH_SIZE = 100  # Process files in batches

# Optimize file operations
def batch_remove_files(file_paths):
    """Remove multiple files efficiently."""
    removed_count = 0
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                removed_count += 1
        except Exception as e:
            log(f"Error removing {path}: {e}")
    
    return removed_count
```

### 6. Final Safety Checks
```python
def validate_cache_integrity():
    """Validate cache integrity on startup."""
    log("Validating cache integrity...")
    
    with state_lock:
        invalid_entries = []
        
        for video_id, info in cached_videos.items():
            # Check if file exists
            if not os.path.exists(info['path']):
                invalid_entries.append(video_id)
                continue
            
            # Check if file has reasonable size (at least 1MB)
            file_size = os.path.getsize(info['path'])
            if file_size < 1024 * 1024:
                invalid_entries.append(video_id)
                log(f"Invalid file size for {video_id}: {file_size} bytes")
        
        # Remove invalid entries
        for video_id in invalid_entries:
            del cached_videos[video_id]
            log(f"Removed invalid cache entry: {video_id}")
        
        if invalid_entries:
            log(f"Removed {len(invalid_entries)} invalid cache entries")
        else:
            log("Cache integrity verified")
```

### 7. User Experience Improvements
```python
def format_time(seconds):
    """Format seconds into human-readable time."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Use in logging:
log(f"Video duration: {format_time(duration)}")
```

### 8. Complete Feature Summary
```python
def log_startup_summary():
    """Log complete feature summary on startup."""
    log("=" * 50)
    log(f"OBS YouTube Player v{SCRIPT_VERSION}")
    log(f"Scene: {SCENE_NAME}")
    log(f"Cache: {cache_dir}")
    log(f"Playlist: {playlist_url}")
    log("Features:")
    log("  - Auto-download from YouTube playlists")
    log("  - AcoustID music recognition")
    log("  - iTunes metadata search")
    log("  - Smart title parsing")
    log("  - Audio normalization to -14 LUFS")
    log("  - Random no-repeat playback")
    log("  - Scene-aware playback control")
    log("=" * 50)

# Add to script_load after settings update:
log_startup_summary()
```

## Testing Checklist

### Functional Testing
1. ✓ Fresh install - no cache
2. ✓ Existing cache with videos
3. ✓ Corrupt video handling
4. ✓ Network failure recovery
5. ✓ Empty playlist handling
6. ✓ Invalid playlist URL
7. ✓ Missing tools recovery
8. ✓ Scene switching stress test
9. ✓ Long playlist (100+ videos)
10. ✓ Unicode/special characters

### Performance Testing
1. ✓ Startup time with large cache
2. ✓ Memory usage over time
3. ✓ CPU usage during processing
4. ✓ Disk space management
5. ✓ Thread cleanup verification

### Integration Testing
1. ✓ Multiple script instances
2. ✓ OBS restart during processing
3. ✓ Scene collection switching
4. ✓ Profile switching
5. ✓ All metadata sources together

## Final Implementation Checklist
- [ ] Update `SCRIPT_VERSION` to 2.0.0
- [ ] Add scan_existing_cache function
- [ ] Add cache integrity validation
- [ ] Add progress summary logging
- [ ] Add corrupt video handling
- [ ] Add time formatting helper
- [ ] Add startup feature summary
- [ ] Update tools_setup_worker
- [ ] Test all edge cases
- [ ] Verify thread safety
- [ ] Check resource cleanup

## Documentation Updates
- Update README with final features
- Add troubleshooting guide
- Document all script properties
- Add examples of supported formats
- Include performance recommendations

## Commit
After successful testing, commit with message:  
> *"Final polish and optimization - v2.0.0 release (Phase 11)"*

## Post-Release
- Monitor for user feedback
- Plan future enhancements
- Consider playlist-specific settings
- Explore visualization options
- Community feature requests

*Congratulations! The OBS YouTube Player is now complete and production-ready.*