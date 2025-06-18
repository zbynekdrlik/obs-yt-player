# Phase 12 – Final Polish & Optimization

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

### 1. Progress Summary Logging
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

### 2. Robust Error Recovery
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

### 3. Performance Optimizations
```python
# Add to module constants
MAX_CONCURRENT_DOWNLOADS = 1  # Already serial, but make it explicit
CACHE_SCAN_BATCH_SIZE = 100  # Process files in batches
MAX_RETRY_ATTEMPTS = 3  # Retry failed downloads

# Track failed downloads
failed_downloads = {}  # video_id: attempt_count

def should_retry_download(video_id):
    """Check if download should be retried."""
    attempts = failed_downloads.get(video_id, 0)
    return attempts < MAX_RETRY_ATTEMPTS

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

### 4. Cache Integrity Validation
```python
def validate_cache_integrity():
    """Validate cache integrity - called after cache scan."""
    log("Validating cache integrity...")
    
    with state_lock:
        invalid_entries = []
        
        for video_id, info in cached_videos.items():
            # Check if file exists
            if not os.path.exists(info['path']):
                invalid_entries.append(video_id)
                continue
            
            # Check if file has reasonable size (at least 1MB)
            try:
                file_size = os.path.getsize(info['path'])
                if file_size < 1024 * 1024:
                    invalid_entries.append(video_id)
                    log(f"Invalid file size for {video_id}: {file_size} bytes")
            except Exception as e:
                invalid_entries.append(video_id)
                log(f"Error checking file size for {video_id}: {e}")
        
        # Remove invalid entries
        for video_id in invalid_entries:
            del cached_videos[video_id]
            log(f"Removed invalid cache entry: {video_id}")
        
        if invalid_entries:
            log(f"Removed {len(invalid_entries)} invalid cache entries")
        else:
            log("Cache integrity verified")

# Call this after scan_existing_cache in playlist_sync_worker
```

### 5. User Experience Improvements
```python
def format_time(seconds):
    """Format seconds into human-readable time."""
    if seconds is None or seconds < 0:
        return "unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

# Use in logging:
log(f"Video duration: {format_time(duration)}")
log(f"File size: {format_size(file_size)}")
```

### 6. Complete Feature Summary
```python
def log_startup_summary():
    """Log complete feature summary on startup."""
    log("=" * 50)
    log(f"OBS YouTube Player v{SCRIPT_VERSION}")
    log(f"Scene: {SCENE_NAME}")
    log(f"Cache: {cache_dir}")
    log(f"Playlist: {playlist_url}")
    log("Features:")
    log("  - Cache-aware sync (no re-downloads)")
    log("  - Auto-download from YouTube playlists")
    log("  - AcoustID music recognition")
    log("  - iTunes metadata search")
    log("  - Smart title parsing")
    log("  - Universal title cleaning")
    log("  - Audio normalization to -14 LUFS")
    log("  - Random no-repeat playback")
    log("  - Scene-aware playback control")
    log("  - Automatic cleanup of removed videos")
    log("=" * 50)

# Add to script_load after settings update:
log_startup_summary()
```

### 7. Enhanced Error Handling
```python
def safe_file_operation(operation, *args, **kwargs):
    """Safely execute file operations with retry logic."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return operation(*args, **kwargs)
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            raise
        except Exception as e:
            log(f"File operation failed: {e}")
            raise

# Update download error handling in process_videos_worker:
if not download_success:
    video_id = video_info['id']
    failed_downloads[video_id] = failed_downloads.get(video_id, 0) + 1
    
    if should_retry_download(video_id):
        log(f"Queueing retry for {video_info['title']} (attempt {failed_downloads[video_id] + 1})")
        video_queue.put(video_info)  # Re-queue for retry
    else:
        log(f"Max retries reached for {video_info['title']}, skipping")
```

### 8. Resource Monitoring
```python
def log_resource_usage():
    """Log current resource usage."""
    try:
        import psutil
        process = psutil.Process()
        
        # Memory usage
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # CPU usage (over 1 second interval)
        cpu_percent = process.cpu_percent(interval=1)
        
        # Thread count
        thread_count = threading.active_count()
        
        log(f"Resources - Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%, Threads: {thread_count}")
    except ImportError:
        # psutil not available in OBS environment
        thread_count = threading.active_count()
        log(f"Active threads: {thread_count}")
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
11. ✓ Retry logic for failed downloads
12. ✓ Cache integrity validation

### Performance Testing
1. ✓ Startup time with large cache
2. ✓ Memory usage over time
3. ✓ CPU usage during processing
4. ✓ Disk space management
5. ✓ Thread cleanup verification
6. ✓ File operation efficiency

### Integration Testing
1. ✓ Multiple script instances
2. ✓ OBS restart during processing
3. ✓ Scene collection switching
4. ✓ Profile switching
5. ✓ All metadata sources together

## Final Implementation Checklist
- [ ] Update `SCRIPT_VERSION` to 2.0.0
- [ ] Add progress summary logging
- [ ] Add cache integrity validation
- [ ] Add corrupt video handling
- [ ] Add retry logic for failed downloads
- [ ] Add time and size formatting helpers
- [ ] Add startup feature summary
- [ ] Add resource monitoring (optional)
- [ ] Update error handling throughout
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
> *"Final polish and optimization - v2.0.0 release (Phase 12)"*

## Post-Release
- Monitor for user feedback
- Plan future enhancements
- Consider playlist-specific settings
- Explore visualization options
- Community feature requests

*Congratulations! The OBS YouTube Player is now complete and production-ready.*