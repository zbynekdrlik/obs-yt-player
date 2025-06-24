#!/usr/bin/env python3
"""
OBS YouTube Player - Main script file.
See docs/01-overview.md for project documentation.
"""

import obspython as obs
import os
import sys
import threading
from pathlib import Path

# Add the script directory to Python path so we can import modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Now import our modules
from ytfast_modules.logger import log, init_logger, close_logger
from ytfast_modules.config import (
    SCRIPT_VERSION, SCRIPT_NAME, SCENE_CHECK_DELAY, DEFAULT_PLAYLIST_URL, 
    DEFAULT_CACHE_DIR, GEMINI_API_KEY_PROPERTY, PLAYBACK_MODE_CONTINUOUS,
    PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, DEFAULT_PLAYBACK_MODE
)
from ytfast_modules.state import (
    get_playlist_url, set_playlist_url, get_cache_dir, set_cache_dir,
    set_stop_threads, set_sync_on_startup_done, get_gemini_api_key,
    set_gemini_api_key, sync_event, get_playback_mode, set_playback_mode,
    is_playing, set_first_video_played
)
from ytfast_modules.scene_monitor import start_scene_check_timer, stop_scene_check_timer
from ytfast_modules.tools import start_tools_thread, cleanup_tools_thread
from ytfast_modules.sync import start_sync_thread, cleanup_sync_thread
from ytfast_modules.process_videos import start_process_videos_thread, cleanup_process_videos_thread
from ytfast_modules.playback_controller import (
    start_playback_controller, stop_playback_controller, stop_current_playback
)
from ytfast_modules.cache_registry import load_cache_registry
from ytfast_modules.gemini_reprocess import start_gemini_reprocess_thread, cleanup_gemini_reprocess_thread

# Module variables
_properties = None
_startup_timer_handle = None


def sync_playlist_callback(props, prop):
    """
    Handle manual playlist sync button press.
    """
    log("Manual playlist sync requested")
    sync_event.set()


def on_playback_mode_changed(props, prop, settings):
    """
    Handle playback mode changes.
    Called when user changes the playback mode dropdown.
    """
    mode = obs.obs_data_get_string(settings, "playback_mode")
    previous_mode = get_playback_mode()
    
    if mode != previous_mode:
        log(f"Playback mode changed to: {mode}")
        set_playback_mode(mode)
        
        # If switching to single mode while a video is playing,
        # mark it as the first (and only) video
        if mode == PLAYBACK_MODE_SINGLE and is_playing():
            set_first_video_played(True)
            log("Single mode: Current video will be the only video played")
        
        # Reset first video played flag when switching away from single mode
        if previous_mode == PLAYBACK_MODE_SINGLE and mode != PLAYBACK_MODE_SINGLE:
            set_first_video_played(False)
            log("Exiting single mode: Reset first video played flag")


def delayed_startup():
    """
    Delayed startup to ensure OBS is fully initialized.
    """
    global _startup_timer_handle
    
    # Remove the timer
    if _startup_timer_handle:
        obs.timer_remove(_startup_timer_handle)
        _startup_timer_handle = None
    
    log("=== STARTING DELAYED INITIALIZATION ===")
    
    # Load cache registry to restore video metadata
    load_cache_registry()
    
    # Start scene monitoring
    start_scene_check_timer()
    
    # Start background threads
    start_tools_thread()
    start_sync_thread()
    start_process_videos_thread()
    
    # Start Gemini reprocess thread if API key is configured
    if get_gemini_api_key():
        start_gemini_reprocess_thread()
    else:
        log("Gemini API key not configured - skipping metadata reprocessing")
    
    # Start playback controller
    start_playback_controller()
    
    log("=== DELAYED INITIALIZATION COMPLETE ===")


def script_load(settings):
    """
    Called when script is loaded by OBS.
    """
    global _startup_timer_handle
    
    # Initialize logger first
    init_logger()
    
    log(f"=== {SCRIPT_NAME.upper()} LOADING (v{SCRIPT_VERSION}) ===")
    
    # Load saved settings
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    if playlist_url:
        set_playlist_url(playlist_url)
    
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    if cache_dir:
        set_cache_dir(cache_dir)
    
    # Load Gemini API key
    api_key = obs.obs_data_get_string(settings, GEMINI_API_KEY_PROPERTY)
    if api_key:
        set_gemini_api_key(api_key)
        log("Gemini API key configured")
    
    # Load playback mode
    playback_mode = obs.obs_data_get_string(settings, "playback_mode")
    if playback_mode:
        set_playback_mode(playback_mode)
        log(f"Loaded playback mode: {playback_mode}")
    
    # Schedule delayed startup
    _startup_timer_handle = delayed_startup
    obs.timer_add(_startup_timer_handle, SCENE_CHECK_DELAY)
    log(f"Scheduled startup in {SCENE_CHECK_DELAY/1000:.1f} seconds")


def script_unload():
    """
    Called when script is unloaded by OBS.
    """
    log(f"=== {SCRIPT_NAME.upper()} UNLOADING ===")
    
    # Cancel startup timer if still pending
    global _startup_timer_handle
    if _startup_timer_handle:
        obs.timer_remove(_startup_timer_handle)
        _startup_timer_handle = None
    
    # Signal threads to stop
    set_stop_threads(True)
    
    # Stop playback
    if is_playing():
        stop_current_playback()
    
    # Stop timers and controllers
    stop_scene_check_timer()
    stop_playback_controller()
    
    # Cleanup threads
    cleanup_tools_thread()
    cleanup_sync_thread() 
    cleanup_process_videos_thread()
    cleanup_gemini_reprocess_thread()
    
    log(f"=== {SCRIPT_NAME.upper()} UNLOADED ===")
    
    # Close logger last
    close_logger()


def script_defaults(settings):
    """
    Set default values for script properties.
    """
    obs.obs_data_set_default_string(settings, "playlist_url", DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", DEFAULT_CACHE_DIR)
    obs.obs_data_set_default_string(settings, GEMINI_API_KEY_PROPERTY, "")
    obs.obs_data_set_default_string(settings, "playback_mode", DEFAULT_PLAYBACK_MODE)


def script_update(settings):
    """
    Called when script settings are updated.
    """
    # Update playlist URL
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    if playlist_url != get_playlist_url():
        set_playlist_url(playlist_url)
        log(f"Playlist URL updated: {playlist_url}")
    
    # Update cache directory
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    if cache_dir != get_cache_dir():
        set_cache_dir(cache_dir)
        log(f"Cache directory updated: {cache_dir}")
    
    # Update Gemini API key
    api_key = obs.obs_data_get_string(settings, GEMINI_API_KEY_PROPERTY)
    if api_key != get_gemini_api_key():
        set_gemini_api_key(api_key)
        if api_key:
            log("Gemini API key configured")
            # Start reprocess thread if not already running
            if not set_sync_on_startup_done(False):  # Check if startup is done
                start_gemini_reprocess_thread()
        else:
            log("Gemini API key removed")
    
    # Update playback mode
    playback_mode = obs.obs_data_get_string(settings, "playback_mode")
    if playback_mode != get_playback_mode():
        on_playback_mode_changed(None, None, settings)
    
    # Log the combined settings update
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Mode: {playback_mode}")


def script_properties():
    """
    Define script properties for OBS settings UI.
    """
    global _properties
    
    if _properties is None:
        _properties = obs.obs_properties_create()
        
        # Playlist URL
        obs.obs_properties_add_text(
            _properties, "playlist_url", "YouTube Playlist URL",
            obs.OBS_TEXT_DEFAULT
        )
        
        # Cache directory
        obs.obs_properties_add_path(
            _properties, "cache_dir", "Cache Directory",
            obs.OBS_PATH_DIRECTORY, "", DEFAULT_CACHE_DIR
        )
        
        # Gemini API key
        obs.obs_properties_add_text(
            _properties, GEMINI_API_KEY_PROPERTY, "Gemini API Key (for metadata)",
            obs.OBS_TEXT_PASSWORD
        )
        
        # Playback mode dropdown
        mode_list = obs.obs_properties_add_list(
            _properties, "playback_mode", "Playback Mode",
            obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING
        )
        obs.obs_property_list_add_string(mode_list, "Continuous (Play all videos)", PLAYBACK_MODE_CONTINUOUS)
        obs.obs_property_list_add_string(mode_list, "Single (Play one video and stop)", PLAYBACK_MODE_SINGLE)
        obs.obs_property_list_add_string(mode_list, "Loop (Repeat current video)", PLAYBACK_MODE_LOOP)
        
        # Manual sync button
        obs.obs_properties_add_button(
            _properties, "sync_button", "Sync Playlist Now",
            sync_playlist_callback
        )
    
    return _properties


def script_description():
    """
    Return script description for OBS.
    """
    return (
        f"<b>{SCRIPT_NAME} v{SCRIPT_VERSION}</b><br><br>"
        "Plays YouTube videos in OBS with automatic caching and normalization.<br><br>"
        "<b>Requirements:</b><br>"
        f"• Scene named '<b>{SCRIPT_NAME}</b>'<br>"
        "• Media Source named '<b>video</b>' in the scene<br>"
        "• Text (GDI+) Source named '<b>title</b>' in the scene<br>"
        "• Gemini API key for accurate metadata extraction<br><br>"
        "<b>Features:</b><br>"
        "• Downloads and caches videos locally<br>"
        "• AI-powered artist/song detection via Gemini<br>"
        "• Audio normalization for consistent volume<br>"
        "• Smooth title fade in/out effects<br>"
        "• Three playback modes: Continuous, Single, Loop<br>"
        "• Random playback without repeats<br><br>"
        "<b>Note:</b> Videos are synced on startup and via 'Sync Playlist Now' button."
    )