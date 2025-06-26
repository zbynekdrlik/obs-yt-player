"""
Playlist synchronization for OBS YouTube Player.
Handles fetching and managing YouTube playlist videos.
"""

import threading
import time

from logger import log
from state import (
    get_playlist_url, is_tools_ready, should_stop_threads,
    is_manual_sync_triggered, set_manual_sync_triggered,
    get_playlist_videos, set_playlist_videos,
    set_thread_script_context, register_thread, unregister_thread
)

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

def fetch_playlist_videos():
    """Fetch videos from YouTube playlist."""
    playlist_url = get_playlist_url()
    if not playlist_url:
        log("No playlist URL configured")
        return []
    
    log(f"Fetching playlist: {playlist_url}")
    
    # TODO: Implement actual playlist fetching with yt-dlp
    # For now, return empty list to allow system to start
    log("Playlist fetching not yet implemented")
    return []

def sync_playlist():
    """Synchronize playlist videos."""
    try:
        # Fetch latest playlist
        videos = fetch_playlist_videos()
        
        if videos:
            # Update state
            set_playlist_videos(videos)
            log(f"Playlist updated with {len(videos)} videos")
            
            # Trigger cache cleanup
            from cache import cleanup_removed_videos
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
    
    try:
        while not should_stop_threads():
            sync_needed = False
            
            # Check for startup sync
            with _startup_sync_lock:
                if _startup_sync_triggered and is_tools_ready():
                    sync_needed = True
                    _startup_sync_triggered = False
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
    # Get current script path from thread context
    import threading
    script_path = getattr(threading.local(), 'script_path', None)
    
    thread = threading.Thread(
        target=playlist_sync_worker,
        args=(script_path,),
        daemon=True
    )
    thread.start()
