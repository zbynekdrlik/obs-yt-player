"""
Thread-aware logging system for OBS YouTube Player with file output.
Logs to both OBS console and individual files per run.
"""

import time
import threading
import os
from pathlib import Path
from datetime import datetime

# Global variables for file logging per script
_script_loggers = {}
_log_lock = threading.Lock()

class ScriptLogger:
    """Logger instance for a specific script."""
    
    def __init__(self, script_name, cache_dir):
        self.script_name = script_name
        self.cache_dir = cache_dir
        self.log_file_handle = None
        self.log_file_path = None
        self.log_initialized = False
        self.first_log_time = None
        self.log_buffer = []
    
    def initialize_file_logging(self):
        """Initialize file logging for this run."""
        if self.log_initialized:
            return
        
        try:
            # Create logs directory
            logs_dir = Path(self.cache_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{self.script_name}_{timestamp}.log"
            self.log_file_path = logs_dir / log_filename
            
            # Open log file for writing
            self.log_file_handle = open(self.log_file_path, 'w', encoding='utf-8')
            self.log_initialized = True
            
            # Write header
            self.log_file_handle.write(f"=== {self.script_name} Log Session ===\n")
            self.log_file_handle.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log_file_handle.write("=" * 40 + "\n\n")
            
            # Write buffered messages
            for msg in self.log_buffer:
                self.log_file_handle.write(msg + "\n")
            self.log_buffer.clear()
            
            self.log_file_handle.flush()
            
            # Log successful initialization to console
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] File logging initialized: {self.log_file_path}")
            
        except Exception as e:
            # If file logging fails, we'll just use console
            print(f"[WARNING] Failed to initialize file logging: {e}")
            self.log_initialized = True  # Prevent repeated attempts
    
    def write_to_file(self, formatted_message):
        """Write message to log file if available."""
        if self.log_file_handle:
            try:
                self.log_file_handle.write(formatted_message + "\n")
                self.log_file_handle.flush()
            except Exception:
                # Silently fail if file write fails
                pass
        elif not self.log_initialized:
            # Buffer messages until file is ready
            self.log_buffer.append(formatted_message)
    
    def cleanup(self):
        """Clean up logging resources."""
        if self.log_file_handle:
            try:
                # Write footer
                self.log_file_handle.write("\n" + "=" * 40 + "\n")
                self.log_file_handle.write(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.log_file_handle.write("=" * 40 + "\n")
                self.log_file_handle.close()
            except Exception:
                pass
            finally:
                self.log_file_handle = None
        
        # Reset state
        self.log_initialized = False
        self.first_log_time = None
        self.log_buffer.clear()

def get_logger():
    """Get logger for current script context."""
    # Use absolute imports to fix module loading issue
    from ytplay_modules.state import get_script_name, get_cache_dir, get_script_dir
    
    script_name = get_script_name()
    if not script_name:
        # Fallback for early initialization
        return None
    
    with _log_lock:
        if script_name not in _script_loggers:
            cache_dir = get_cache_dir()
            if not cache_dir:
                # Use default if cache dir not set yet
                script_dir = get_script_dir()
                cache_dir = os.path.join(script_dir, f"{script_name}-cache")
            
            _script_loggers[script_name] = ScriptLogger(script_name, cache_dir)
        
        return _script_loggers[script_name]

def log(message):
    """
    Log messages with timestamp and script identifier.
    Outputs to both OBS console and log file.
    """
    logger = get_logger()
    if not logger:
        # Early logging before script context is set
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        return
    
    # Track when first log was called
    if logger.first_log_time is None:
        logger.first_log_time = time.time()
    
    # Initialize file logging after a short delay (to avoid multiple files from quick reload)
    # But only if we've been running for more than 1 second
    if not logger.log_initialized and (time.time() - logger.first_log_time) > 1.0:
        logger.initialize_file_logging()
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    thread_name = threading.current_thread().name
    
    # Format message based on thread context
    if thread_name != "MainThread":
        # For background threads, include script name in message
        console_msg = f"[{timestamp}] [{logger.script_name}] {message}"
        file_msg = f"[{timestamp}] [Thread: {thread_name}] {message}"
    else:
        # For main thread, OBS already shows script name
        console_msg = f"[{timestamp}] {message}"
        file_msg = f"[{timestamp}] [MainThread] {message}"
    
    # Output to console (OBS)
    print(console_msg)
    
    # Output to file (or buffer if not ready)
    with _log_lock:
        logger.write_to_file(file_msg)

def cleanup_logging():
    """Clean up logging resources for current script. Call when script unloads."""
    logger = get_logger()
    if logger:
        with _log_lock:
            logger.cleanup()
            # Remove logger instance
            from ytplay_modules.state import get_script_name
            script_name = get_script_name()
            if script_name in _script_loggers:
                del _script_loggers[script_name]

def get_current_log_path():
    """Get the path of the current log file."""
    logger = get_logger()
    return str(logger.log_file_path) if logger and logger.log_file_path else None
