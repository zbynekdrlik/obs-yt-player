"""
Thread-aware logging system for OBS YouTube Player with file output.
Logs to both OBS console and individual files per run.
"""

import time
import threading
import os
from pathlib import Path
from datetime import datetime
from config import SCRIPT_NAME, DEFAULT_CACHE_DIR

# Global variables for file logging
_log_file_handle = None
_log_file_path = None
_log_initialized = False
_log_lock = threading.Lock()

def _initialize_file_logging():
    """Initialize file logging for this run."""
    global _log_file_handle, _log_file_path, _log_initialized
    
    if _log_initialized:
        return
    
    try:
        # Create logs directory
        logs_dir = Path(DEFAULT_CACHE_DIR) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{SCRIPT_NAME}_{timestamp}.log"
        _log_file_path = logs_dir / log_filename
        
        # Open log file for writing
        _log_file_handle = open(_log_file_path, 'w', encoding='utf-8')
        _log_initialized = True
        
        # Write header
        _log_file_handle.write(f"=== {SCRIPT_NAME} Log Session ===\n")
        _log_file_handle.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        _log_file_handle.write("=" * 40 + "\n\n")
        _log_file_handle.flush()
        
    except Exception as e:
        # If file logging fails, we'll just use console
        print(f"[WARNING] Failed to initialize file logging: {e}")
        _log_initialized = True  # Prevent repeated attempts

def _write_to_file(formatted_message):
    """Write message to log file if available."""
    with _log_lock:
        if _log_file_handle:
            try:
                _log_file_handle.write(formatted_message + "\n")
                _log_file_handle.flush()
            except Exception:
                # Silently fail if file write fails
                pass

def log(message):
    """
    Log messages with timestamp and script identifier.
    Outputs to both OBS console and log file.
    """
    # Initialize file logging on first use
    if not _log_initialized:
        _initialize_file_logging()
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    thread_name = threading.current_thread().name
    
    # Format message based on thread context
    if thread_name != "MainThread":
        # For background threads, include script name in message
        console_msg = f"[{timestamp}] [{SCRIPT_NAME}] {message}"
        file_msg = f"[{timestamp}] [Thread: {thread_name}] {message}"
    else:
        # For main thread, OBS already shows script name
        console_msg = f"[{timestamp}] {message}"
        file_msg = f"[{timestamp}] [MainThread] {message}"
    
    # Output to console (OBS)
    print(console_msg)
    
    # Output to file
    _write_to_file(file_msg)

def cleanup_logging():
    """Clean up logging resources. Call when script unloads."""
    global _log_file_handle, _log_initialized
    
    with _log_lock:
        if _log_file_handle:
            try:
                # Write footer
                _log_file_handle.write("\n" + "=" * 40 + "\n")
                _log_file_handle.write(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                _log_file_handle.write("=" * 40 + "\n")
                _log_file_handle.close()
            except Exception:
                pass
            finally:
                _log_file_handle = None
                _log_initialized = False

def get_current_log_path():
    """Get the path of the current log file."""
    return str(_log_file_path) if _log_file_path else None