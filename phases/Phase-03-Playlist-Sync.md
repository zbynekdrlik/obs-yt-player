# Phase 03 – Playlist Sync with Cache Awareness

## Goal
Implement playlist synchronization that scans existing cache, fetches video IDs, and queues only missing videos for processing. This phase establishes efficient sync behavior from the start.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements playlist synchronization from `02-requirements.md`:
- Trigger **only** at startup and via *Sync Playlist Now* button
- **NO PERIODIC SYNC** - Script runs on slow LTE internet
- Process videos **one-by-one**: download → fingerprint → normalize → rename
- Queue only videos not already in cache

## Components to Implement

### 1. Cache Scanning Function
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

### 2. Enhanced Playlist Sync Worker
```python
def playlist_sync_worker():
    """Worker thread for playlist synchronization."""
    global sync_on_startup_done
    
    while not stop_threads:
        # Wait for sync_event signal
        if not sync_event.wait(timeout=1):
            continue
        
        sync_event.clear()
        
        # Check tools_ready before proceeding
        with state_lock:
            if not tools_ready:
                log("Sync triggered but tools not ready, skipping")
                continue
        
        log("Starting playlist synchronization")
        
        try:
            # First scan existing cache (always do this)
            scan_existing_cache()
            
            # Fetch playlist
            videos = fetch_playlist_with_ytdlp(playlist_url)
            
            if not videos:
                log("No videos found in playlist")
                continue
            
            log(f"Fetched {len(videos)} videos from playlist")
            
            # Update playlist video IDs
            with state_lock:
                playlist_video_ids.clear()
                playlist_video_ids.update(video['id'] for video in videos)
            
            # Queue only videos not in cache
            queued_count = 0
            skipped_count = 0
            
            for video in videos:
                video_id = video['id']
                
                # Check if already cached
                with state_lock:
                    if video_id in cached_videos:
                        skipped_count += 1
                        continue
                
                # Queue for processing
                video_queue.put(video)
                queued_count += 1
            
            log(f"Queued {queued_count} videos for processing, {skipped_count} already in cache")
            
            # Clean up removed videos (only after successful playlist fetch)
            cleanup_removed_videos()
            
        except Exception as e:
            log(f"Error during playlist sync: {e}")
```

### 3. Cleanup Removed Videos
```python
def cleanup_removed_videos():
    """Remove videos that are no longer in playlist."""
    with state_lock:
        # Find videos to remove
        videos_to_remove = []
        for video_id in cached_videos:
            if video_id not in playlist_video_ids:
                # Check if it's currently playing (will be implemented in playback phase)
                if not is_video_being_processed(video_id):
                    videos_to_remove.append(video_id)
                else:
                    log(f"Skipping removal of currently playing video: {video_id}")
        
        # Remove videos
        for video_id in videos_to_remove:
            video_info = cached_videos[video_id]
            try:
                os.remove(video_info['path'])
                del cached_videos[video_id]
                log(f"Removed: {video_info['artist']} - {video_info['song']}")
            except Exception as e:
                log(f"Error removing video {video_id}: {e}")
        
        if videos_to_remove:
            log(f"Cleaned up {len(videos_to_remove)} removed videos")

def is_video_being_processed(video_id):
    """Check if video is currently being downloaded/processed."""
    # For now, always return False. Will be updated in playback phase
    return False
```

### 4. Playlist Fetching
```python
def fetch_playlist_with_ytdlp(playlist_url):
    """Fetch playlist videos using yt-dlp."""
    if not playlist_url:
        log("No playlist URL configured")
        return []
    
    cmd = [
        ytdlp_path,
        '--flat-playlist',
        '--dump-json',
        '--no-warnings',
        playlist_url
    ]
    
    videos = []
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        for line in process.stdout:
            try:
                video_data = json.loads(line.strip())
                videos.append({
                    'id': video_data.get('id', ''),
                    'title': video_data.get('title', 'Unknown'),
                    'duration': video_data.get('duration', 0)
                })
            except json.JSONDecodeError:
                continue
        
        process.wait()
        
        if process.returncode != 0:
            stderr = process.stderr.read()
            log(f"yt-dlp error: {stderr}")
            return []
            
    except Exception as e:
        log(f"Error fetching playlist: {e}")
        return []
    
    return videos
```

### 5. Update Startup Sync Trigger
```python
def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    global sync_on_startup_done
    
    with state_lock:
        if sync_on_startup_done:
            return
        sync_on_startup_done = True
    
    log("Starting one-time playlist sync on startup")
    sync_event.set()
```

## Key Implementation Points
- **Always scan cache first** before fetching playlist
- Queue only videos not already in cache
- Clean up videos no longer in playlist
- Use `threading.Event` for sync signaling
- Thread-safe queue and state operations
- Proper error handling for all operations

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Add scan_existing_cache function
- [ ] Implement enhanced playlist_sync_worker
- [ ] Add cleanup_removed_videos function
- [ ] Implement fetch_playlist_with_ytdlp
- [ ] Add trigger_startup_sync function
- [ ] Update sync_now_callback to use sync_event
- [ ] Call trigger_startup_sync from tools thread
- [ ] Handle errors gracefully
- [ ] Add appropriate logging

## Testing Before Commit
1. Test with empty cache - verify all videos queued
2. Restart script - verify cached videos not re-queued
3. Test "Sync Now" button with existing cache
4. Remove video from playlist - verify cleanup
5. Test with invalid playlist URL
6. Test with empty playlist
7. Verify efficient startup (no re-downloads)
8. Check memory usage with large cache
9. Test concurrent sync requests
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add cache-aware playlist sync with cleanup"*

*After verification, proceed to Phase 04 - Video Download.*