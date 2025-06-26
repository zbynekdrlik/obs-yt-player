"""Reprocess thread for OBS YouTube Player."""

import time
from logger import log
from state import get_state, should_stop_threads

def start_reprocess_thread():
    """Start the reprocess thread."""
    # Thread is started by main.py
    reprocess_worker()

def reprocess_worker():
    """Background thread for reprocessing videos."""
    log("Reprocess thread started")
    
    # Wait a bit before starting reprocessing
    time.sleep(5)
    
    while not should_stop_threads():
        # Check for videos to reprocess (placeholder)
        time.sleep(60)  # Check every minute
    
    log("Reprocess thread exiting")