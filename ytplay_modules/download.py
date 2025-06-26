"""Download management for OBS YouTube Player."""

import time
from logger import log
from state import get_state, should_stop_threads

def start_video_processing_thread():
    """Start video processing thread."""
    # Thread is started by main.py
    video_processing_worker()

def video_processing_worker():
    """Background thread for video processing."""
    log("Video processing thread started")
    
    while not should_stop_threads():
        # Check for videos to download
        state = get_state()
        download_queue = state.get('download_queue', [])
        
        if download_queue:
            # Process videos (placeholder)
            video = download_queue.pop(0)
            log(f"Processing video: {video.get('title', 'Unknown')}")
        
        time.sleep(1)
    
    log("Video processing thread exiting")