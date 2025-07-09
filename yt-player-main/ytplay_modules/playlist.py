"""Playlist management for OBS YouTube Player.
Handles playlist syncing and video discovery.
"""

import threading
import time
import subprocess
import json

from .logger import log
from .state import (
    get_playlist_url, sync_event, should_stop_threads,
    is_tools_ready, is_sync_on_startup_done, set_sync_on_startup_done,
    get_playlist_video_ids, set_playlist_video_ids,
    video_queue, playlist_sync_thread
)
from .config import PLAYBACK_MODE_LOOP, PLAYBACK_MODE_SINGLE
from .cache import scan_existing_cache, cleanup_removed_videos

# Import get_ytdlp_path from utils
from .utils import get_ytdlp_path

# Sync interval (30 minutes)
SYNC_INTERVAL = 1800  # seconds

def fetch_playlist_videos(playlist_url):
    """Fetch video list from YouTube playlist."""
    try:
        ytdlp_path = get_ytdlp_path()
        
        # Command to get playlist info as JSON
        cmd = [
            ytdlp_path,
            "--flat-playlist",
            "--dump-json", 
            "--no-warnings",
            "--quiet",
            "--no-check-certificate",
            playlist_url
        ]
        
        log("Fetching playlist information...")
        
        # Run yt-dlp and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            log(f"Error fetching playlist: {result.stderr}")
            return []
        
        # Parse JSON output (one JSON object per line)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    # Extract relevant info
                    video_info = {
                        'id': video_data.get('id'),
                        'title': video_data.get('title', 'Unknown Title'),
                        'url': video_data.get('url') or f"https://www.youtube.com/watch?v={video_data.get('id')}"
                    }
                    videos.append(video_info)
                except json.JSONDecodeError:
                    continue
        
        log(f"Found {len(videos)} videos in playlist")
        return videos
        
    except subprocess.TimeoutExpired:
        log("Timeout while fetching playlist")
        return []
    except Exception as e:
        log(f"Error fetching playlist: {e}")
        return []

def sync_playlist():
    """Sync playlist and queue new videos for download."""
    playlist_url = get_playlist_url()
    if not playlist_url:
        log("No playlist URL configured")
        return
    
    log(f"Syncing playlist: {playlist_url}")
    
    # Fetch current playlist
    videos = fetch_playlist_videos(playlist_url)
    if not videos:
        log("No videos found in playlist")
        return
    
    # Update playlist video IDs for cleanup
    video_ids = {video['id'] for video in videos}
    set_playlist_video_ids(video_ids)
    
    # Scan existing cache first
    from .state import is_video_cached
    scan_existing_cache()
    
    # Clean up removed videos
    cleanup_removed_videos()
    
    # Check for Gemini reprocess needs
    from .state import get_gemini_api_key, get_cached_videos
    if get_gemini_api_key():
        # Check if any cached videos need Gemini reprocessing
        cached = get_cached_videos()
        for video_id, info in cached.items():
            if info.get('gemini_failed', False):
                # Re-queue for Gemini processing
                video_queue.put({
                    'id': video_id,
                    'title': f"{info['song']} - {info['artist']}",  # Use existing metadata
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'reprocess_gemini': True
                })
                log(f"Queued for Gemini reprocess: {info['song']} - {info['artist']}")
    
    # Queue videos for download
    new_count = 0
    for video in videos:
        video_id = video['id']
        
        # Skip if already cached and normalized
        if is_video_cached(video_id):
            from .state import get_cached_video_info
            info = get_cached_video_info(video_id)
            if info and info.get('normalized'):
                # Skip if not marked for Gemini reprocessing
                if not info.get('gemini_failed', False) or not get_gemini_api_key():
                    continue
        
        # Add to download queue
        video_queue.put(video)
        new_count += 1
    
    if new_count > 0:
        log(f"Queued {new_count} videos for processing")
    else:
        log("All videos already cached")

def playlist_sync_thread():
    """Background thread for playlist syncing."""
    log("[Playlist Thread] Starting...")
    
    # Wait for tools to be ready
    while not should_stop_threads():
        if is_tools_ready():
            break
        time.sleep(1)
    
    if should_stop_threads():
        return
    
    # Do initial sync
    sync_playlist()
    set_sync_on_startup_done(True)
    
    # Main sync loop
    while not should_stop_threads():
        try:
            # Wait for sync interval or manual sync signal
            if sync_event.wait(timeout=SYNC_INTERVAL):
                # Manual sync requested
                sync_event.clear()
                log("[Playlist Thread] Manual sync triggered")
            else:
                # Regular interval sync
                log("[Playlist Thread] Periodic sync triggered")
            
            if should_stop_threads():
                break
            
            sync_playlist()
            
        except Exception as e:
            log(f"[Playlist Thread] Error: {e}")
            time.sleep(60)  # Wait a bit before retrying
    
    log("[Playlist Thread] Exiting")

def start_playlist_sync_thread():
    """Start the playlist sync thread."""
    global playlist_sync_thread
    
    if playlist_sync_thread and playlist_sync_thread.is_alive():
        return
    
    from .state import playlist_sync_thread as state_playlist_thread
    state_playlist_thread = threading.Thread(target=playlist_sync_thread, name="PlaylistThread")
    state_playlist_thread.daemon = True
    state_playlist_thread.start()

def trigger_manual_sync():
    """Trigger a manual playlist sync."""
    sync_event.set()