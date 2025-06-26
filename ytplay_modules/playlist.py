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
    get_state, is_tools_ready, should_stop_threads, get_playlist_url
)
from tools import get_ytdlp_path
from cache import scan_existing_cache, cleanup_removed_videos, get_cached_videos

def fetch_playlist_with_ytdlp(playlist_url):
    """Fetch playlist information using yt-dlp."""
    try:
        ytdlp_path = get_ytdlp_path()
        if not ytdlp_path:
            log("yt-dlp path not available")
            return []
        
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

def playlist_sync_worker():
    """Background thread for playlist synchronization - NO PERIODIC SYNC."""
    state = get_state()
    
    while not should_stop_threads():
        # Wait for sync signal using threading event
        sync_event = state.get('sync_event')
        if not sync_event:
            # Create sync event if not exists
            sync_event = threading.Event()
            state['sync_event'] = sync_event
        
        # Wait for sync signal or timeout
        if not sync_event.wait(timeout=1):
            continue
        
        # Clear the event
        sync_event.clear()
        
        # Check if we should exit
        if should_stop_threads():
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
            if not playlist_url:
                log("No playlist URL configured")
                continue
                
            videos = fetch_playlist_with_ytdlp(playlist_url)
            
            if not videos:
                log("No videos found in playlist or fetch failed")
                continue
            
            # Update playlist video IDs
            video_ids = set([video['id'] for video in videos])
            state['playlist_video_ids'] = video_ids
            
            # Get download queue
            if 'download_queue' not in state:
                state['download_queue'] = []
            download_queue = state['download_queue']
            
            # Queue only videos not in cache (Phase 3 enhancement)
            queued_count = 0
            skipped_count = 0
            cached_videos = get_cached_videos()
            
            for video in videos:
                video_id = video['id']
                
                # Check if already cached
                if video_id in cached_videos:
                    skipped_count += 1
                    continue
                
                # Queue for processing
                download_queue.append(video)
                queued_count += 1
            
            log(f"Queued {queued_count} videos for processing, {skipped_count} already in cache")
            
            # Clean up removed videos (Phase 3 addition)
            cleanup_removed_videos()
            
        except Exception as e:
            log(f"Error in playlist sync: {e}")
    
    log("Playlist sync thread exiting")

def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    state = get_state()
    
    if state.get('sync_on_startup_done', False):
        return
    
    state['sync_on_startup_done'] = True
    log("Starting one-time playlist sync on startup")
    
    # Get or create sync event
    sync_event = state.get('sync_event')
    if not sync_event:
        sync_event = threading.Event()
        state['sync_event'] = sync_event
    
    sync_event.set()  # Signal playlist sync thread to run

def trigger_manual_sync():
    """Trigger manual playlist sync."""
    state = get_state()
    
    # Get or create sync event
    sync_event = state.get('sync_event')
    if not sync_event:
        sync_event = threading.Event()
        state['sync_event'] = sync_event
    
    sync_event.set()

def start_playlist_sync_thread():
    """Start the playlist sync thread."""
    # Thread is started by main.py
    playlist_sync_worker()
