"""
Video download module for OBS YouTube Player.
Handles downloading videos from YouTube.
"""

import threading
import time
import queue

from logger import log
from state import (
    should_stop_threads, get_download_queue, set_download_queue,
    set_thread_script_context, register_thread, unregister_thread
)

def download_video_worker(script_path):
    """Background thread for video downloading."""
    # Set thread context
    set_thread_script_context(script_path)
    
    # Register thread
    register_thread('download', threading.current_thread())
    
    # Create download queue if not exists
    download_queue = get_download_queue()
    if not download_queue:
        download_queue = queue.Queue()
        set_download_queue(download_queue)
    
    try:
        while not should_stop_threads():
            try:
                # Check for videos to download
                video_info = download_queue.get(timeout=1)
                
                # TODO: Implement actual video downloading
                log(f"Download requested for video: {video_info.get('id', 'unknown')}")
                
                # Mark task as done
                download_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                log(f"Error in download worker: {e}")
    
    finally:
        # Unregister thread
        unregister_thread('download')
        log("Download thread exiting")

def start_video_processing_thread():
    """Start the video processing thread."""
    # Get current script path from thread context
    import threading
    script_path = getattr(threading.local(), 'script_path', None)
    
    thread = threading.Thread(
        target=download_video_worker,
        args=(script_path,),
        daemon=True
    )
    thread.start()
