"""
Reprocessing module for OBS YouTube Player.
Handles reprocessing videos that failed Gemini extraction.
"""

import threading
import time

from logger import log
from state import (
    should_stop_threads, get_gemini_failures, get_gemini_api_key,
    set_thread_script_context, register_thread, unregister_thread
)

def reprocess_gemini_failures():
    """Reprocess videos that failed Gemini extraction."""
    failures = get_gemini_failures()
    api_key = get_gemini_api_key()
    
    if not failures:
        return
    
    if not api_key:
        log("Gemini API key not configured, skipping reprocess")
        return
    
    log(f"Found {len(failures)} videos to reprocess with Gemini")
    
    # TODO: Implement actual reprocessing logic
    # For now, just log
    for video_id in list(failures):
        log(f"Would reprocess video: {video_id}")

def reprocess_worker(script_path):
    """Background thread for reprocessing videos."""
    # Set thread context
    set_thread_script_context(script_path)
    
    # Register thread
    register_thread('reprocess', threading.current_thread())
    
    try:
        # Run once at startup
        time.sleep(5)  # Give system time to initialize
        
        if not should_stop_threads():
            reprocess_gemini_failures()
        
        # Then just wait for shutdown
        while not should_stop_threads():
            time.sleep(1)
    
    finally:
        # Unregister thread
        unregister_thread('reprocess')
        log("Reprocess thread exiting")

def start_reprocess_thread():
    """Start the reprocess thread."""
    # Get current script path from thread context
    import threading
    script_path = getattr(threading.local(), 'script_path', None)
    
    thread = threading.Thread(
        target=reprocess_worker,
        args=(script_path,),
        daemon=True
    )
    thread.start()
