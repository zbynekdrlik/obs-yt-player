"""
Thread-aware logging system for OBS YouTube Player.
Handles logging differently based on thread context to ensure proper script identification.
"""

import threading
import datetime
import os
from pathlib import Path
from typing import Optional

from state import get_current_script_path, get_state

# Store current log file handles per script
_log_files = {}
_log_lock = threading.Lock()

def log(message: str):
    """
    Thread-aware logging function.
    
    Formats messages differently based on thread context:
    - Main thread: [timestamp] message
    - Background thread: [timestamp] [script_name] message
    
    This ensures script identification even when OBS shows [Unknown Script] for background threads.
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Get script context
    script_path = get_current_script_path()
    if not script_path:
        # Fallback if no context set
        print(f"[{timestamp}] [NO_CONTEXT] {message}")
        return
    
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    
    # Check if we're on the main thread
    if threading.current_thread() is threading.main_thread():
        # Main thread - OBS will prepend script name
        formatted_message = f"[{timestamp}] {message}"
    else:
        # Background thread - include script name in message
        formatted_message = f"[{timestamp}] [{script_name}] {message}"
    
    # Print to console
    print(formatted_message)
    
    # Also write to log file if enabled
    _write_to_file(script_path, formatted_message)

def _write_to_file(script_path: str, message: str):
    """Write log message to file."""
    try:
        state = get_state()
        cache_dir = state.get('cache_dir')
        if not cache_dir:
            return
        
        # Create logs directory
        logs_dir = Path(cache_dir) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session log file
        session_id = state.get('session_id')
        if not session_id:
            # Generate session ID if not exists
            session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            state['session_id'] = session_id
        
        log_file = logs_dir / f"session_{session_id}.log"
        
        # Write message
        with _log_lock:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
                
    except Exception:
        # Silently ignore logging errors to avoid recursion
        pass

def cleanup_logging():
    """Clean up logging resources for the current script."""
    script_path = get_current_script_path()
    if not script_path:
        return
    
    # Clean up old log files
    try:
        state = get_state()
        cache_dir = state.get('cache_dir')
        if not cache_dir:
            return
        
        logs_dir = Path(cache_dir) / "logs"
        if not logs_dir.exists():
            return
        
        # Keep only last 10 log files
        log_files = sorted(logs_dir.glob("session_*.log"))
        if len(log_files) > 10:
            for old_log in log_files[:-10]:
                try:
                    old_log.unlink()
                except Exception:
                    pass
                    
    except Exception:
        # Silently ignore cleanup errors
        pass

def log_error(message: str, exception: Optional[Exception] = None):
    """Log an error message with optional exception details."""
    if exception:
        log(f"ERROR: {message} - {type(exception).__name__}: {str(exception)}")
    else:
        log(f"ERROR: {message}")

def log_warning(message: str):
    """Log a warning message."""
    log(f"WARNING: {message}")

def log_info(message: str):
    """Log an info message (alias for log)."""
    log(message)

def log_debug(message: str):
    """Log a debug message (currently same as regular log)."""
    log(f"DEBUG: {message}")
