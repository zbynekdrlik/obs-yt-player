"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads.
"""

import obspython as obs
import sys
import os
from pathlib import Path

# Script identification based on filename
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# IMPORTANT: All scripts share the same modules directory
MODULES_DIR = os.path.join(SCRIPT_DIR, "ytplay_modules")

# Create shared modules directory if it doesn't exist
Path(MODULES_DIR).mkdir(exist_ok=True)

# Add to Python path
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# Import modules after path is set
from config import (
    SCRIPT_VERSION, SCENE_CHECK_DELAY,
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, DEFAULT_PLAYBACK_MODE,
    DEFAULT_AUDIO_ONLY_MODE, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
)
from logger import log, cleanup_logging
from state import (
    get_playlist_url, set_playlist_url, 
    get_cache_dir, set_cache_dir,
    is_tools_ready, set_stop_threads,
    set_gemini_api_key,
    get_playback_mode, set_playback_mode,
    set_first_video_played, set_loop_video_id,
    get_current_playback_video_id, is_playing,
    is_audio_only_mode, set_audio_only_mode,
    set_script_name, set_script_dir
)

# Initialize script identification in state module
set_script_name(SCRIPT_NAME)
set_script_dir(SCRIPT_DIR)

from tools import start_tools_thread
from playlist import start_playlist_sync_thread, trigger_manual_sync
from download import start_video_processing_thread
from scene import verify_scene_setup, on_frontend_event, reset_scene_error_flag
from playback import start_playback_controller, stop_playback_controller, get_current_video_from_media_source
from metadata import clear_gemini_failures
from reprocess import start_reprocess_thread

# Store timer references
_verify_scene_timer = None
_warning_update_timer = None

# Global settings reference for warnings update
_global_settings = None
_global_props = None

# ===== OBS SCRIPT INTERFACE =====
def script_description():
    """Return script description for OBS."""
    return __doc__.strip()

def check_configuration_warnings():
    """Check for configuration issues and return warning messages."""
    warnings = []
    
    # Check for missing scene
    scene_source = obs.obs_get_source_by_name(SCRIPT_NAME)
    if not scene_source:
        warnings.append(f"Scene '{SCRIPT_NAME}' not found")
    else:
        obs.obs_source_release(scene_source)
        
        # Check for missing sources within the scene
        scene = obs.obs_scene_from_source(scene_source) if scene_source else None
        if scene:
            media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
            if not media_source:
                warnings.append(f"Media Source '{MEDIA_SOURCE_NAME}' not found")
            else:
                obs.obs_source_release(media_source)
                
            text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
            if not text_source:
                warnings.append(f"Text Source '{TEXT_SOURCE_NAME}' not found")
            else:
                obs.obs_source_release(text_source)
    
    # Check for missing playlist URL
    if not get_playlist_url():
        warnings.append("No playlist URL")
    
    # Check if tools are ready
    if not is_tools_ready():
        warnings.append("Tools not ready")
    
    return warnings

def update_warning_visibility(props, prop, settings):
    """Update the visibility and content of warning label."""
    if not props:
        return
        
    warnings = check_configuration_warnings()
    
    # Update warning label
    warning_prop = obs.obs_properties_get(props, "warnings")
    if warning_prop:
        if warnings:
            # Join all warnings with " | " separator
            warning_text = "⚠️ " + " | ".join(warnings)
            obs.obs_property_set_description(warning_prop, warning_text)
            obs.obs_property_set_visible(warning_prop, True)
        else:
            obs.obs_property_set_visible(warning_prop, False)
    
    return True

def script_properties():
    """Define script properties shown in OBS UI."""
    global _global_props
    props = obs.obs_properties_create()
    _global_props = props
    
    # Playlist URL text field
    playlist_prop = obs.obs_properties_add_text(
        props, 
        "playlist_url", 
        "YT Playlist URL", 
        obs.OBS_TEXT_DEFAULT
    )
    obs.obs_property_set_modified_callback(playlist_prop, update_warning_visibility)
    
    # Playback mode dropdown
    playback_mode = obs.obs_properties_add_list(
        props,
        "playback_mode",
        "Playback Mode",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    
    obs.obs_property_list_add_string(playback_mode, "Continuous (Play all videos)", PLAYBACK_MODE_CONTINUOUS)
    obs.obs_property_list_add_string(playback_mode, "Single (Play one video and stop)", PLAYBACK_MODE_SINGLE)
    obs.obs_property_list_add_string(playback_mode, "Loop (Repeat current video)", PLAYBACK_MODE_LOOP)
    
    # Audio-only mode dropdown
    audio_mode = obs.obs_properties_add_list(
        props,
        "audio_only_mode",
        "Audio Only Mode",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_INT
    )
    
    obs.obs_property_list_add_int(audio_mode, "Disabled (Full video quality)", 0)
    obs.obs_property_list_add_int(audio_mode, "Enabled (Minimal video, high audio)", 1)
    
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
    
    # Cache directory text field - moved to last position before sync button
    cache_prop = obs.obs_properties_add_text(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_TEXT_DEFAULT
    )
    
    # Add separator before sync button
    obs.obs_properties_add_text(
        props,
        "separator",
        "─────────────────────────────",
        obs.OBS_TEXT_INFO
    )
    
    # Sync Now button
    sync_button = obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # Warning text at the bottom (hidden by default)
    warning_prop = obs.obs_properties_add_text(
        props,
        "warnings",
        "",  # Content will be set dynamically
        obs.OBS_TEXT_INFO
    )
    obs.obs_property_set_visible(warning_prop, False)
    
    # Force initial warning check
    if _global_settings:
        update_warning_visibility(props, None, _global_settings)
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    # Default playlist URL is now empty - user must set it
    obs.obs_data_set_default_string(settings, "playlist_url", "")
    
    # Default cache directory based on script name
    default_cache_dir = os.path.join(SCRIPT_DIR, f"{SCRIPT_NAME}-cache")
    obs.obs_data_set_default_string(settings, "cache_dir", default_cache_dir)
    
    obs.obs_data_set_default_string(settings, "playback_mode", DEFAULT_PLAYBACK_MODE)
    obs.obs_data_set_default_int(settings, "audio_only_mode", 0 if not DEFAULT_AUDIO_ONLY_MODE else 1)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings):
    """Called when script properties are updated."""
    global _global_settings
    _global_settings = settings
    
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    playback_mode = obs.obs_data_get_string(settings, "playback_mode")
    audio_only_mode = obs.obs_data_get_int(settings, "audio_only_mode") == 1
    gemini_key = obs.obs_data_get_string(settings, "gemini_api_key")
    
    # Check if playback mode changed
    old_mode = get_playback_mode()
    
    set_playlist_url(playlist_url)
    set_cache_dir(cache_dir)
    set_playback_mode(playback_mode)
    set_audio_only_mode(audio_only_mode)
    
    # Reset playback state if mode changed
    if old_mode != playback_mode:
        log(f"Playback mode changed to: {playback_mode}")
        
        # If changing to single mode while a video is playing, mark it as first video played
        if playback_mode == PLAYBACK_MODE_SINGLE and is_playing():
            set_first_video_played(True)
            log("Single mode enabled - current video counts as first video")
        else:
            set_first_video_played(False)
        
        # If changing to loop mode and a video is currently playing, set it as the loop video
        if playback_mode == PLAYBACK_MODE_LOOP and is_playing():
            # First try to get the current video ID from state
            current_video_id = get_current_playback_video_id()
            
            # If not available, try to get it from the media source
            if not current_video_id:
                current_video_id = get_current_video_from_media_source()
            
            if current_video_id:
                set_loop_video_id(current_video_id)
                log(f"Loop mode enabled - will loop current video (ID: {current_video_id})")
            else:
                # Clear loop video ID so next video will be set as loop video
                set_loop_video_id(None)
                log("Loop mode enabled - will loop next video that plays")
        else:
            # Clear loop video ID when switching away from loop mode
            set_loop_video_id(None)
    
    # Store Gemini API key in state if provided
    if gemini_key:
        set_gemini_api_key(gemini_key)
        log("Gemini API key configured")
    else:
        set_gemini_api_key(None)
    
    # Update warnings whenever settings change
    if _global_props:
        update_warning_visibility(_global_props, None, settings)
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Mode: {playback_mode}, Audio-only: {audio_only_mode}")

def warnings_update_timer():
    """Timer callback to periodically update warnings."""
    if _global_props and _global_settings:
        update_warning_visibility(_global_props, None, _global_settings)

def script_load(settings):
    """Called when script is loaded."""
    global _verify_scene_timer, _warning_update_timer, _global_settings
    _global_settings = settings
    
    set_stop_threads(False)
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    
    # Reset scene error flag
    reset_scene_error_flag()
    
    # Clear Gemini failure cache on script restart
    clear_gemini_failures()
    
    # Apply initial settings
    script_update(settings)
    
    # Schedule scene verification after delay
    _verify_scene_timer = verify_scene_setup
    obs.timer_add(_verify_scene_timer, SCENE_CHECK_DELAY)
    
    # Start periodic warning updates (every 5 seconds)
    _warning_update_timer = warnings_update_timer
    obs.timer_add(_warning_update_timer, 5000)
    
    # Start worker threads
    start_worker_threads()
    
    # Register frontend event callbacks
    obs.obs_frontend_add_event_callback(on_frontend_event)
    
    log("Script loaded successfully")

def script_unload():
    """Called when script is unloaded."""
    global _verify_scene_timer, _warning_update_timer
    
    log("Script unloading...")
    
    # Signal threads to stop
    set_stop_threads(True)
    
    # Stop all worker threads
    stop_worker_threads()
    
    # Remove timers
    if _verify_scene_timer:
        obs.timer_remove(_verify_scene_timer)
    
    if _warning_update_timer:
        obs.timer_remove(_warning_update_timer)
    
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
    
    # Check if playlist URL is set
    if not get_playlist_url():
        log("Cannot sync - no playlist URL configured")
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