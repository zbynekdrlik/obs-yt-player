"""Playlist synchronization for OBS YouTube Player.
Handles fetching and managing YouTube playlist videos.
"""

import threading
import time
import subprocess
import json
import queue
import os

# Use absolute imports to fix module loading issue
from ytplay_modules.logger import log
from ytplay_modules.state import (
    get_playlist_url, is_tools_ready, should_stop_threads,
    is_manual_sync_triggered, set_manual_sync_triggered,
    get_playlist_videos, set_playlist_videos,
    set_thread_script_context, register_thread, unregister_thread,
    get_download_queue, set_download_queue,
    get_local_videos, get_metadata_cache
)
from ytplay_modules.tools import get_ytdlp_path

# Flag to trigger startup sync
_startup_sync_triggered = False
_startup_sync_lock = threading.Lock()

def trigger_startup_sync():
    """Trigger playlist sync at startup (called by tools module)."""
    global _startup_sync_triggered
    with _startup_sync_lock:
        _startup_sync_triggered = True
        log("Startup sync triggered")

def trigger_manual_sync():
    """Trigger manual playlist sync."""
    set_manual_sync_triggered(True)
    log("Manual playlist sync triggered")

def fetch_playlist_with_ytdlp(playlist_url):
    """Fetch playlist information using yt-dlp."""
    try:
        ytdlp_path = get_ytdlp_path()
        
        # Prepare command
        cmd = [
            ytdlp_path,
            '--flat-playlist',
            '--dump-json',
            '--no-warnings',
            playlist_url
        ]
        
        # Run command with hidden window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=30
        )
        
        if result.returncode != 0:
            log(f"yt-dlp failed: {result.stderr}")
            return []
        
        # Parse JSON output (one JSON object per line)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    videos.append({
                        'id': video_data.get('id', ''),
                        'title': video_data.get('title', 'Unknown'),
                        'duration': video_data.get('duration', 0)
                    })
                except json.JSONDecodeError:
                    continue
        
        log(f"Fetched {len(videos)} videos from playlist")
        return videos
        
    except Exception as e:
        log(f"Error fetching playlist: {e}")
        return []

def sync_playlist():
    """Synchronize playlist videos."""
    try:
        log("Starting playlist synchronization")
        
        # First scan existing cache
        from ytplay_modules.cache import scan_existing_cache, cleanup_removed_videos
        scan_existing_cache()
        
        # Fetch playlist
        playlist_url = get_playlist_url()
        if not playlist_url:
            log("No playlist URL configured")
            return False
        
        videos = fetch_playlist_with_ytdlp(playlist_url)
        
        if not videos:
            log("No videos found in playlist or fetch failed")
            return False
        
        # Update state
        set_playlist_videos(videos)
        
        # Get current cache state
        local_videos = get_local_videos()
        metadata_cache = get_metadata_cache()
        
        # Get or create download queue
        download_queue = get_download_queue()
        if not download_queue:
            download_queue = queue.Queue()
            set_download_queue(download_queue)
        
        # Queue only videos not in cache
        queued_count = 0
        skipped_count = 0
        
        for video in videos:
            video_id = video['id']
            
            # Check if already cached
            if video_id in local_videos and video_id in metadata_cache:
                # Check if file exists
                video_info = metadata_cache.get(video_id, {})
                if video_info.get('path') and os.path.exists(video_info['path']):
                    skipped_count += 1
                    continue
            
            # Queue for processing
            download_queue.put(video)
            queued_count += 1
        
        log(f"Queued {queued_count} videos for processing, {skipped_count} already in cache")
        
        # Clean up removed videos
        cleanup_removed_videos()
        
        return True
        
    except Exception as e:
        log(f"Error syncing playlist: {e}")
        return False

def playlist_sync_worker(script_path):
    """Background thread for playlist synchronization."""
    global _startup_sync_triggered
    
    # Set thread context
    set_thread_script_context(script_path)
    
    # Register thread
    register_thread('playlist', threading.current_thread())
    
    # Track if startup sync has been done
    startup_sync_done = False
    
    try:
        while not should_stop_threads():
            sync_needed = False
            
            # Check for startup sync
            with _startup_sync_lock:
                if _startup_sync_triggered and is_tools_ready() and not startup_sync_done:
                    sync_needed = True
                    _startup_sync_triggered = False
                    startup_sync_done = True
                    log("Processing startup sync")
            
            # Check for manual sync
            if is_manual_sync_triggered():
                sync_needed = True
                set_manual_sync_triggered(False)
                log("Processing manual sync")
            
            # Perform sync if needed
            if sync_needed:
                sync_playlist()
            
            # Sleep for a bit
            time.sleep(1)
    
    finally:
        # Unregister thread
        unregister_thread('playlist')
        log("Playlist sync thread exiting")

def start_playlist_sync_thread():
    """Start the playlist sync thread."""
    # Get current script path from thread-local storage
    script_path = getattr(threading.current_thread(), '_script_path', None)
    
    if not script_path:
        # Try to get from main thread state
        import ytplay_modules.state as state
        script_path = getattr(state._thread_local, 'script_path', None)
    
    if not script_path:
        log("ERROR: No script path available for playlist thread")
        return
    
    thread = threading.Thread(
        target=playlist_sync_worker,
        args=(script_path,),
        daemon=True
    )
    thread.start()