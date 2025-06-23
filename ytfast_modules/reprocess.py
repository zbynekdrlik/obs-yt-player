"""
Reprocess videos that failed Gemini extraction on previous runs.
This module handles renaming files when Gemini succeeds on retry.
"""

import os
import threading
import time
from pathlib import Path

from logger import log
from state import (
    get_cache_dir, get_cached_videos, get_cached_video_info,
    should_stop_threads, get_playlist_videos, is_tools_ready,
    add_cached_video, get_gemini_api_key
)
from metadata import get_video_metadata
from utils import sanitize_filename

_reprocess_thread = None

def find_videos_to_reprocess():
    """Find all videos with _gf marker that need Gemini retry."""
    videos_to_reprocess = []
    cached_videos = get_cached_videos()
    
    for video_id, video_info in cached_videos.items():
        if video_info.get('gemini_failed', False):
            # Check if we have playlist info for this video
            playlist_videos = get_playlist_videos()
            playlist_info = playlist_videos.get(video_id)
            if playlist_info:
                videos_to_reprocess.append({
                    'id': video_id,
                    'title': playlist_info['title'],
                    'current_path': video_info['path'],
                    'song': video_info['song'],
                    'artist': video_info['artist']
                })
    
    return videos_to_reprocess

def reprocess_video(video_info):
    """Attempt to reprocess a single video with Gemini."""
    video_id = video_info['id']
    title = video_info['title']
    current_path = video_info['current_path']
    
    log(f"Retrying Gemini extraction for: {title}")
    
    # Try to get metadata again (will use Gemini if API key is available)
    song, artist, metadata_source, gemini_failed = get_video_metadata(
        current_path, title, video_id
    )
    
    if not gemini_failed and metadata_source == 'Gemini':
        # Gemini succeeded! Need to rename the file
        log(f"Gemini extraction succeeded on retry: {artist} - {song}")
        
        # Generate new filename without _gf marker
        cache_dir = get_cache_dir()
        safe_song = sanitize_filename(song)
        safe_artist = sanitize_filename(artist)
        new_filename = f"{safe_song}_{safe_artist}_{video_id}_normalized.mp4"
        new_path = os.path.join(cache_dir, new_filename)
        
        # Rename the file if paths are different
        if current_path != new_path and os.path.exists(current_path):
            try:
                # Remove new path if it exists (shouldn't happen)
                if os.path.exists(new_path):
                    os.remove(new_path)
                
                # Rename the file
                os.rename(current_path, new_path)
                log(f"Renamed file: {os.path.basename(current_path)} -> {os.path.basename(new_path)}")
                
                # Update cached video info
                add_cached_video(video_id, {
                    'path': new_path,
                    'song': song,
                    'artist': artist,
                    'normalized': True,
                    'gemini_failed': False
                })
                
                return True
            except Exception as e:
                log(f"Error renaming file: {e}")
                return False
    else:
        # Gemini still failed or no API key
        if not get_gemini_api_key():
            log(f"Skipping reprocess - no Gemini API key configured")
        else:
            log(f"Gemini extraction failed again for: {title}")
        return False

def reprocess_worker():
    """Background worker to reprocess videos with failed Gemini extraction."""
    # Wait for tools to be ready
    while not is_tools_ready() and not should_stop_threads():
        time.sleep(1)
    
    if should_stop_threads():
        return
    
    # Check if Gemini API key is configured
    if not get_gemini_api_key():
        log("No Gemini API key configured - skipping reprocess of failed videos")
        return
    
    # Find videos to reprocess
    videos_to_reprocess = find_videos_to_reprocess()
    
    if not videos_to_reprocess:
        log("No videos found that need Gemini reprocessing")
        return
    
    log(f"Found {len(videos_to_reprocess)} videos to retry Gemini extraction")
    
    # Process each video
    success_count = 0
    for video_info in videos_to_reprocess:
        if should_stop_threads():
            break
        
        if reprocess_video(video_info):
            success_count += 1
        
        # Small delay between attempts
        time.sleep(0.5)
    
    if success_count > 0:
        log(f"Successfully reprocessed {success_count} videos with Gemini")
    
    log("Gemini reprocessing complete")

def start_reprocess_thread():
    """Start the reprocess thread if needed."""
    global _reprocess_thread
    
    # Only start if not already running
    if _reprocess_thread is None or not _reprocess_thread.is_alive():
        _reprocess_thread = threading.Thread(target=reprocess_worker, daemon=True)
        _reprocess_thread.start()
        log("Started Gemini reprocess thread")