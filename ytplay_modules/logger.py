"""
Thread-aware logging system for OBS YouTube Player with file output.
Logs to both OBS console and individual files per run.
"""

import time
import threading
import os
from pathlib import Path
from datetime import datetime

# Global variables for file logging
_log_file_handle = None
_log_file_path = None
_log_initialized = False
_log_lock = threading.Lock()
_first_log_time = None
_log_buffer = []  # Buffer for messages before file is ready

def _initialize_file_logging():
    """Initialize file logging for this run."""
    global _log_file_handle, _log_file_path, _log_initialized, _log_buffer
    
    if _log_initialized:
        return
    
    try:
        # Get script name and cache dir from state
        from state import get_script_name, get_cache_dir
        script_name = get_script_name() or "ytplay"  # Fallback name
        cache_dir = get_cache_dir()
        
        if not cache_dir:
            # If cache dir not set, use script directory
            from state import get_script_dir
            script_dir = get_script_dir() or os.getcwd()
            cache_dir = os.path.join(script_dir, f"{script_name}-cache")
        
        # Create logs directory
        logs_dir = Path(cache_dir) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{script_name}_{timestamp}.log"
        _log_file_path = logs_dir / log_filename
        
        # Open log file for writing
        _log_file_handle = open(_log_file_path, 'w', encoding='utf-8')
        _log_initialized = True
        
        # Write header
        _log_file_handle.write(f"=== {script_name} Log Session ===\n")
        _log_file_handle.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        _log_file_handle.write("=" * 40 + "\n\n")
        
        # Write buffered messages
        for msg in _log_buffer:
            _log_file_handle.write(msg + "\n")
        _log_buffer.clear()
        
        _log_file_handle.flush()
        
        # Log successful initialization to console
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] File logging initialized: {_log_file_path}")
        
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
        elif not _log_initialized:
            # Buffer messages until file is ready
            _log_buffer.append(formatted_message)

def log(message):
    """
    Log messages with timestamp and script identifier.
    Outputs to both OBS console and log file.
    """
    global _first_log_time
    
    # Track when first log was called
    if _first_log_time is None:
        _first_log_time = time.time()
    
    # Initialize file logging after a short delay (to avoid multiple files from quick reload)
    # But only if we've been running for more than 1 second
    if not _log_initialized and (time.time() - _first_log_time) > 1.0:
        _initialize_file_logging()
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    thread_name = threading.current_thread().name
    
    # Get script name from state
    from state import get_script_name
    script_name = get_script_name() or "ytplay"  # Fallback name
    
    # Format message based on thread context
    if thread_name != "MainThread":
        # For background threads, include script name in message
        console_msg = f"[{timestamp}] [{script_name}] {message}"
        file_msg = f"[{timestamp}] [Thread: {thread_name}] {message}"
    else:
        # For main thread, OBS already shows script name
        console_msg = f"[{timestamp}] {message}"
        file_msg = f"[{timestamp}] [MainThread] {message}"
    
    # Output to console (OBS)
    print(console_msg)
    
    # Output to file (or buffer if not ready)
    _write_to_file(file_msg)

def cleanup_logging():
    """Clean up logging resources. Call when script unloads."""
    global _log_file_handle, _log_initialized, _first_log_time, _log_buffer
    
    with _log_lock:
        # Only write to file if we actually initialized it
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
        
        # Reset all state
        _log_initialized = False
        _first_log_time = None
        _log_buffer.clear()

def get_current_log_path():
    """Get the path of the current log file."""
    return str(_log_file_path) if _log_file_path else None