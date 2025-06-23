"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source with metadata display. All processing runs in background threads.
"""

import obspython as obs
import sys
import os
from pathlib import Path

# Add modules directory to Python path
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]
MODULES_DIR = os.path.join(SCRIPT_DIR, f"{SCRIPT_NAME}_modules")

# Create modules directory if it doesn't exist
Path(MODULES_DIR).mkdir(exist_ok=True)

# Add to Python path
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# Import modules after path is set
from config import SCRIPT_VERSION, DEFAULT_PLAYLIST_URL, DEFAULT_CACHE_DIR, SCENE_CHECK_DELAY
from logger import log, cleanup_logging
from state import (
    get_playlist_url, set_playlist_url, 
    get_cache_dir, set_cache_dir,
    is_tools_ready, set_stop_threads,
    set_gemini_api_key  # Use the correct function name
)
from tools import start_tools_thread
from playlist import start_playlist_sync_thread, trigger_manual_sync
from download import start_video_processing_thread
from scene import verify_scene_setup, on_frontend_event
from playback import start_playback_controller, stop_playback_controller
from metadata import clear_gemini_failures
from reprocess import start_reprocess_thread

# Store timer references
_verify_scene_timer = None

# ===== OBS SCRIPT INTERFACE =====
def script_description():
    """Return script description for OBS."""
    return __doc__.strip()

def script_properties():
    """Define script properties shown in OBS UI."""
    props = obs.obs_properties_create()
    
    # Playlist URL text field
    obs.obs_properties_add_text(
        props, 
        "playlist_url", 
        "YouTube Playlist URL", 
        obs.OBS_TEXT_DEFAULT
    )
    
    # Cache directory text field - editable for easy customization
    obs.obs_properties_add_text(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_TEXT_DEFAULT
    )
    
    # Sync Now button
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # Add separator for optional features
    obs.obs_properties_add_text(
        props,
        "separator1",
        "───── Optional Features ─────",
        obs.OBS_TEXT_INFO
    )
    
    # Gemini API key field (password type for security)
    obs.obs_properties_add_text(
        props, 
        "gemini_api_key", 
        "Google Gemini API Key", 
        obs.OBS_TEXT_PASSWORD
    )
    
    # Help text for Gemini
    obs.obs_properties_add_text(
        props,
        "gemini_help",
        "For better metadata extraction. Get your free API key at:\nhttps://makersuite.google.com/app/apikey",
        obs.OBS_TEXT_INFO
    )
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    obs.obs_data_set_default_string(settings, "playlist_url", DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", DEFAULT_CACHE_DIR)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings):
    """Called when script properties are updated."""
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    gemini_key = obs.obs_data_get_string(settings, "gemini_api_key")
    
    set_playlist_url(playlist_url)
    set_cache_dir(cache_dir)
    
    # Store Gemini API key in state if provided
    if gemini_key:
        set_gemini_api_key(gemini_key)
        log("Gemini API key configured")
    else:
        set_gemini_api_key(None)
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}")

def script_load(settings):
    """Called when script is loaded."""
    global _verify_scene_timer
    
    set_stop_threads(False)
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    
    # Clear Gemini failure cache on script restart
    clear_gemini_failures()
    
    # Apply initial settings
    script_update(settings)
    
    # Schedule scene verification after delay
    _verify_scene_timer = verify_scene_setup
    obs.timer_add(_verify_scene_timer, SCENE_CHECK_DELAY)
    
    # Start worker threads
    start_worker_threads()
    
    # Register frontend event callbacks
    obs.obs_frontend_add_event_callback(on_frontend_event)
    
    log("Script loaded successfully")

def script_unload():
    """Called when script is unloaded."""
    global _verify_scene_timer
    
    log("Script unloading...")
    
    # Signal threads to stop
    set_stop_threads(True)
    
    # Stop all worker threads
    stop_worker_threads()
    
    # Remove timers
    if _verify_scene_timer:
        obs.timer_remove(_verify_scene_timer)
    
    stop_playback_controller()
    
    # Clean up temp files
    from cache import cleanup_temp_files
    cleanup_temp_files()
    
    # Clean up logging
    cleanup_logging()
    
    log("Script unloaded")

# ===== CALLBACK FUNCTIONS =====
def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    log("Manual sync requested")
    
    # Check if tools are ready
    if not is_tools_ready():
        log("Cannot sync - tools not ready yet")
        return True
    
    # Trigger playlist sync
    trigger_manual_sync()
    return True

# ===== WORKER THREAD MANAGEMENT =====
def start_worker_threads():
    """Start all background worker threads."""
    log("Starting worker threads...")
    
    # Start threads in order
    start_tools_thread()
    start_playlist_sync_thread()
    start_video_processing_thread()
    start_playback_controller()
    start_reprocess_thread()  # Start the Gemini reprocess thread
    
    log("Worker threads started")

def stop_worker_threads():
    """Stop all background worker threads."""
    log("Stopping worker threads...")
    
    # Threads will check stop flag and exit
    # Each module handles its own thread cleanup
    
    log("Worker threads stopped")