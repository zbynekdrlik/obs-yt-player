"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source with metadata display. All processing runs in background threads.
"""

import obspython as obs
import threading
import queue
import os
import time
import logging
import subprocess
from pathlib import Path

# ===== MODULE-LEVEL CONSTANTS =====
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLrAl6rYJWZ7J5XKz9nZQ9J8Z9J8Z9J8Z9"
DEFAULT_CACHE_DIR = os.path.expanduser("~/obs_ytfast_cache")
SCENE_NAME = "ytfast"  # Scene name matches script filename
MEDIA_SOURCE_NAME = "video"
TEXT_SOURCE_NAME = "title"
TOOLS_SUBDIR = "tools"
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
SYNC_INTERVAL = 3600  # 1 hour in seconds
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second in milliseconds
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
MAX_RESOLUTION = "1440"

# ===== GLOBAL VARIABLES =====
# Threading infrastructure
playlist_sync_thread = None
download_worker_thread = None
normalization_worker_thread = None
metadata_worker_thread = None

# Synchronization primitives
state_lock = threading.Lock()
download_queue = queue.Queue()
normalization_queue = queue.Queue()
metadata_queue = queue.Queue()

# State flags
tools_ready = False
scene_active = False
is_playing = False
current_video_path = None

# Data structures
cached_videos = {}  # {video_id: {"path": str, "song": str, "artist": str, "normalized": bool}}
played_videos = []  # List of video IDs to avoid repeats
playlist_video_ids = set()  # Current playlist video IDs

# Script properties
playlist_url = DEFAULT_PLAYLIST_URL
cache_dir = DEFAULT_CACHE_DIR
debug_enabled = True

# ===== LOGGING HELPER =====
def log(message, level="NORMAL"):
    """Log messages with timestamp and level."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if level == "DEBUG" and not debug_enabled:
        return
    
    formatted_message = f"[{timestamp}] [{level}] {message}"
    
    if level == "DEBUG":
        print(f"[ytfast DEBUG] {formatted_message}")
    else:
        print(f"[ytfast] {formatted_message}")

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
    
    # Cache directory path field
    obs.obs_properties_add_path(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_PATH_DIRECTORY,
        None,
        DEFAULT_CACHE_DIR
    )
    
    # Sync Now button
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # DEBUG level checkbox
    obs.obs_properties_add_bool(
        props,
        "debug_enabled",
        "Enable Debug Logging"
    )
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    obs.obs_data_set_default_string(settings, "playlist_url", DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", DEFAULT_CACHE_DIR)
    obs.obs_data_set_default_bool(settings, "debug_enabled", True)

def script_update(settings):
    """Called when script properties are updated."""
    global playlist_url, cache_dir, debug_enabled
    
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    debug_enabled = obs.obs_data_get_bool(settings, "debug_enabled")
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Debug: {debug_enabled}", "DEBUG")

def script_load(settings):
    """Called when script is loaded."""
    log("Script loading...")
    
    # Apply initial settings
    script_update(settings)
    
    # Schedule scene verification after 3 seconds
    obs.timer_add(verify_scene_setup, SCENE_CHECK_DELAY)
    
    # Start worker threads
    start_worker_threads()
    
    # Register frontend event callbacks
    obs.obs_frontend_add_event_callback(on_frontend_event)
    
    log("Script loaded successfully")

def script_unload():
    """Called when script is unloaded."""
    log("Script unloading...")
    
    # Stop all worker threads
    stop_worker_threads()
    
    # Remove timers
    obs.timer_remove(verify_scene_setup)
    obs.timer_remove(playback_controller)
    
    log("Script unloaded")

# ===== CALLBACK FUNCTIONS =====
def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    log("Manual sync requested")
    # TODO: Trigger playlist sync
    return True

def on_frontend_event(event):
    """Handle OBS frontend events."""
    global scene_active
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        # Check if our scene is active
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            scene_name = obs.obs_source_get_name(current_scene)
            scene_active = (scene_name == SCENE_NAME)
            log(f"Scene changed to: {scene_name}, Active: {scene_active}", "DEBUG")
            obs.obs_source_release(current_scene)

def verify_scene_setup():
    """Verify that required scene and sources exist."""
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    if not scene_source:
        log(f"ERROR: Required scene '{SCENE_NAME}' not found! Please create it.", "NORMAL")
        return
    
    scene = obs.obs_scene_from_source(scene_source)
    if scene:
        # Check for required sources
        media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        
        if not media_source:
            log(f"WARNING: Media Source '{MEDIA_SOURCE_NAME}' not found in scene", "NORMAL")
        else:
            obs.obs_source_release(media_source)
            
        if not text_source:
            log(f"WARNING: Text Source '{TEXT_SOURCE_NAME}' not found in scene", "NORMAL")
        else:
            obs.obs_source_release(text_source)
    
    obs.obs_source_release(scene_source)
    
    # Remove this timer - only run once
    obs.timer_remove(verify_scene_setup)

def playback_controller():
    """Main playback controller - runs on main thread."""
    # TODO: Implement playback logic
    pass

# ===== WORKER THREAD STARTERS =====
def start_worker_threads():
    """Start all background worker threads."""
    global playlist_sync_thread, download_worker_thread
    global normalization_worker_thread, metadata_worker_thread
    
    log("Starting worker threads...")
    
    # TODO: Start actual worker threads
    # playlist_sync_thread = threading.Thread(target=playlist_sync_worker, daemon=True)
    # download_worker_thread = threading.Thread(target=download_worker, daemon=True)
    # normalization_worker_thread = threading.Thread(target=normalization_worker, daemon=True)
    # metadata_worker_thread = threading.Thread(target=metadata_worker, daemon=True)
    
    # For now, just log placeholders
    log("Worker thread starters ready (placeholders)", "DEBUG")

def stop_worker_threads():
    """Stop all background worker threads."""
    log("Stopping worker threads...")
    # TODO: Implement proper thread stopping
    log("Worker threads stopped", "DEBUG")

# ===== WORKER THREAD PLACEHOLDERS =====
def playlist_sync_worker():
    """Background thread for playlist synchronization."""
    # TODO: Implement in Phase 2
    pass

def download_worker():
    """Background thread for video downloads."""
    # TODO: Implement in Phase 3
    pass

def normalization_worker():
    """Background thread for audio normalization."""
    # TODO: Implement in Phase 4
    pass

def metadata_worker():
    """Background thread for metadata retrieval."""
    # TODO: Implement in Phase 6
    pass

# ===== UTILITY FUNCTIONS =====
def ensure_cache_directory():
    """Ensure cache directory exists."""
    try:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(cache_dir, TOOLS_SUBDIR)).mkdir(exist_ok=True)
        log(f"Cache directory ready: {cache_dir}", "DEBUG")
        return True
    except Exception as e:
        log(f"Failed to create cache directory: {e}", "NORMAL")
        return False

def get_tools_path():
    """Get path to tools directory."""
    return os.path.join(cache_dir, TOOLS_SUBDIR)

def get_ytdlp_path():
    """Get path to yt-dlp executable."""
    return os.path.join(get_tools_path(), YTDLP_FILENAME)

def get_ffmpeg_path():
    """Get path to ffmpeg executable."""
    return os.path.join(get_tools_path(), FFMPEG_FILENAME)
