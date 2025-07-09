"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads.
"""

import obspython as obs
import sys
import os
from pathlib import Path
import importlib

# Setup paths
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]
MODULES_DIR_NAME = f"{SCRIPT_NAME}_modules"
MODULES_DIR = os.path.join(SCRIPT_DIR, MODULES_DIR_NAME)

# Create modules directory if it doesn't exist
Path(MODULES_DIR).mkdir(exist_ok=True)

# Add parent directory to path so we can import the modules package
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Dynamically import the modules package
modules = importlib.import_module(MODULES_DIR_NAME)

# Import from the modules package
config = modules.config
logger = modules.logger
state = modules.state
tools = modules.tools
playlist = modules.playlist
download = modules.download
scene = modules.scene
playback = modules.playback
metadata = modules.metadata
reprocess = modules.reprocess
cache = modules.cache

# Now we can use the imported modules
log = logger.log
cleanup_logging = logger.cleanup_logging

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
    
    # Playback mode dropdown
    playback_mode = obs.obs_properties_add_list(
        props,
        "playback_mode",
        "Playback Mode",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    
    obs.obs_property_list_add_string(playback_mode, "Continuous (Play all videos)", config.PLAYBACK_MODE_CONTINUOUS)
    obs.obs_property_list_add_string(playback_mode, "Single (Play one video and stop)", config.PLAYBACK_MODE_SINGLE)
    obs.obs_property_list_add_string(playback_mode, "Loop (Repeat current video)", config.PLAYBACK_MODE_LOOP)
    
    # Audio-only mode checkbox
    obs.obs_properties_add_bool(
        props,
        "audio_only_mode",
        "Audio Only Mode (Minimal video quality, high audio quality)"
    )
    
    # Gemini API key field (password type for security)
    obs.obs_properties_add_text(
        props, 
        "gemini_api_key", 
        "Gemini API Key", 
        obs.OBS_TEXT_PASSWORD
    )
    
    # Add description text below Gemini API key field
    obs.obs_properties_add_text(
        props,
        "gemini_description",
        "Optional: Provides better artist/song detection than title parsing",
        obs.OBS_TEXT_INFO
    )
    
    # Add separator before sync button
    obs.obs_properties_add_text(
        props,
        "separator",
        "─────────────────────────────",
        obs.OBS_TEXT_INFO
    )
    
    # Sync Now button at the bottom
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    obs.obs_data_set_default_string(settings, "playlist_url", config.DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", config.DEFAULT_CACHE_DIR)
    obs.obs_data_set_default_string(settings, "playback_mode", config.DEFAULT_PLAYBACK_MODE)
    obs.obs_data_set_default_bool(settings, "audio_only_mode", config.DEFAULT_AUDIO_ONLY_MODE)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings):
    """Called when script properties are updated."""
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    playback_mode = obs.obs_data_get_string(settings, "playback_mode")
    audio_only_mode = obs.obs_data_get_bool(settings, "audio_only_mode")
    gemini_key = obs.obs_data_get_string(settings, "gemini_api_key")
    
    # Check if playback mode changed
    old_mode = state.get_playback_mode()
    
    state.set_playlist_url(playlist_url)
    state.set_cache_dir(cache_dir)
    state.set_playback_mode(playback_mode)
    state.set_audio_only_mode(audio_only_mode)
    
    # Reset playback state if mode changed
    if old_mode != playback_mode:
        log(f"Playback mode changed to: {playback_mode}")
        
        # If changing to single mode while a video is playing, mark it as first video played
        if playback_mode == config.PLAYBACK_MODE_SINGLE and state.is_playing():
            state.set_first_video_played(True)
            log("Single mode enabled - current video counts as first video")
        else:
            state.set_first_video_played(False)
        
        # If changing to loop mode and a video is currently playing, set it as the loop video
        if playback_mode == config.PLAYBACK_MODE_LOOP and state.is_playing():
            # First try to get the current video ID from state
            current_video_id = state.get_current_playback_video_id()
            
            # If not available, try to get it from the media source
            if not current_video_id:
                current_video_id = playback.get_current_video_from_media_source()
            
            if current_video_id:
                state.set_loop_video_id(current_video_id)
                log(f"Loop mode enabled - will loop current video (ID: {current_video_id})")
            else:
                # Clear loop video ID so next video will be set as loop video
                state.set_loop_video_id(None)
                log("Loop mode enabled - will loop next video that plays")
        else:
            # Clear loop video ID when switching away from loop mode
            state.set_loop_video_id(None)
    
    # Store Gemini API key in state if provided
    if gemini_key:
        state.set_gemini_api_key(gemini_key)
        log("Gemini API key configured")
    else:
        state.set_gemini_api_key(None)
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Mode: {playback_mode}, Audio-only: {audio_only_mode}")

def script_load(settings):
    """Called when script is loaded."""
    global _verify_scene_timer
    
    state.set_stop_threads(False)
    
    log(f"Script version {config.SCRIPT_VERSION} loaded")
    
    # Clear Gemini failure cache on script restart
    metadata.clear_gemini_failures()
    
    # Apply initial settings
    script_update(settings)
    
    # Schedule scene verification after delay
    _verify_scene_timer = scene.verify_scene_setup
    obs.timer_add(_verify_scene_timer, config.SCENE_CHECK_DELAY)
    
    # Start worker threads
    start_worker_threads()
    
    # Register frontend event callbacks
    obs.obs_frontend_add_event_callback(scene.on_frontend_event)
    
    log("Script loaded successfully")

def script_unload():
    """Called when script is unloaded."""
    global _verify_scene_timer
    
    log("Script unloading...")
    
    # Signal threads to stop
    state.set_stop_threads(True)
    
    # Stop all worker threads
    stop_worker_threads()
    
    # Remove timers
    if _verify_scene_timer:
        obs.timer_remove(_verify_scene_timer)
    
    playback.stop_playback_controller()
    
    # Clean up temp files
    cache.cleanup_temp_files()
    
    # Clean up logging
    cleanup_logging()
    
    log("Script unloaded")

# ===== CALLBACK FUNCTIONS =====
def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    log("Manual sync requested")
    
    # Check if tools are ready
    if not state.is_tools_ready():
        log("Cannot sync - tools not ready yet")
        return True
    
    # Trigger playlist sync
    playlist.trigger_manual_sync()
    return True

# ===== WORKER THREAD MANAGEMENT =====
def start_worker_threads():
    """Start all background worker threads."""
    log("Starting worker threads...")
    
    # Start threads in order
    tools.start_tools_thread()
    playlist.start_playlist_sync_thread()
    download.start_video_processing_thread()
    playback.start_playback_controller()
    reprocess.start_reprocess_thread()  # Start the Gemini reprocess thread
    
    log("Worker threads started")

def stop_worker_threads():
    """Stop all background worker threads."""
    log("Stopping worker threads...")
    
    # Threads will check stop flag and exit
    # Each module handles its own thread cleanup
    
    log("Worker threads stopped")
