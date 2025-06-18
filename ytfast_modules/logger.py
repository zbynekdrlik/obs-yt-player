"""
Thread-aware logging system for OBS YouTube Player.
"""

import time
import threading
from config import SCRIPT_NAME

def log(message):
    """
    Log messages with timestamp and script identifier.
    Format depends on thread context to handle OBS behavior.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    thread_name = threading.current_thread().name
    
    if thread_name != "MainThread":
        # For background threads, include script name in message
        print(f"[{timestamp}] [{SCRIPT_NAME}] {message}")
    else:
        # For main thread, OBS already shows script name
        print(f"[{timestamp}] {message}")
