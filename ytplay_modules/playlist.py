"""
Playlist synchronization for OBS YouTube Player.
Fetches playlist information and manages sync operations.
"""

import subprocess
import json
import time
import threading
import os

from config import SCRIPT_VERSION
from logger import log
from state import (
    get_current_script_path, set_thread_script_context,
    get_or_create_state, should_stop_threads_safe,
    is_tools_ready, get_playlist_url,
    is_sync_on_startup_done, set_sync_on_startup_done,
    set_playlist_video_ids, is_video_cached,
    get_script_name
)
from utils import get_ytdlp_path
from cache import scan_existing_cache, cleanup_removed_videos

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

def playlist_sync_worker(script_path):
    """Background thread for playlist synchronization - NO PERIODIC SYNC."""
    # v3.6.2: Set script context for this thread
    set_thread_script_context(script_path)
    
    # Get state objects for this script
    try:
        state = get_or_create_state(script_path)
    except:
        # State doesn't exist, exit thread
        log("Playlist sync thread exiting - state not found")
        return
    
    # Log thread startup with script name
    script_name = get_script_name()
    log(f"Playlist sync thread started for {script_name}")
    
    while not should_stop_threads_safe(script_path):
        # Wait for sync signal or timeout
        if not state.sync_event.wait(timeout=1):
            continue
        
        # Clear the event
        state.sync_event.clear()
        
        # Check if we should exit
        if should_stop_threads_safe(script_path):
            break
            
        # Wait for tools to be ready
        if not is_tools_ready():
            log("Sync requested but tools not ready")
            continue
        
        log("Starting playlist synchronization")
        
        try:
            # First scan existing cache (Phase 3 addition)
            scan_existing_cache()
            
            # Fetch playlist
            playlist_url = get_playlist_url()
            
            # Skip if no URL configured
            if not playlist_url or playlist_url.strip() == "":
                log("No playlist URL configured - skipping sync")
                continue
                
            videos = fetch_playlist_with_ytdlp(playlist_url)
            
            if not videos:
                log("No videos found in playlist or fetch failed")
                continue
            
            # Update playlist video IDs
            video_ids = [video['id'] for video in videos]
            set_playlist_video_ids(video_ids)
            
            # Queue only videos not in cache (Phase 3 enhancement)
            queued_count = 0
            skipped_count = 0
            
            for video in videos:
                video_id = video['id']
                
                # Check if already cached
                if is_video_cached(video_id):
                    skipped_count += 1
                    continue
                
                # Queue for processing
                state.video_queue.put(video)
                queued_count += 1
            
            log(f"Queued {queued_count} videos for processing, {skipped_count} already in cache")
            
            # Clean up removed videos (Phase 3 addition)
            cleanup_removed_videos()
            
        except Exception as e:
            log(f"Error in playlist sync: {e}")
    
    log(f"Playlist sync thread exiting for {script_name}")

def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    if is_sync_on_startup_done():
        return
    
    set_sync_on_startup_done(True)
    log("Starting one-time playlist sync on startup")
    
    try:
        # Get current script's sync event
        state = get_or_create_state()
        state.sync_event.set()  # Signal playlist sync thread to run
    except Exception as e:
        log(f"Error triggering startup sync: {e}")

def trigger_manual_sync():
    """Trigger manual playlist sync."""
    try:
        # Get current script's sync event
        state = get_or_create_state()
        state.sync_event.set()
    except Exception as e:
        log(f"Error triggering manual sync: {e}")

def start_playlist_sync_thread():
    """Start the playlist sync thread."""
    # v3.6.2: Get current script path to pass to thread
    script_path = get_current_script_path()
    try:
        state = get_or_create_state(script_path)
        
        # Create and start thread with script context
        state.playlist_sync_thread = threading.Thread(
            target=playlist_sync_worker, 
            args=(script_path,),
            daemon=True
        )
        state.playlist_sync_thread.start()
    except Exception as e:
        log(f"Error starting playlist sync thread: {e}")
