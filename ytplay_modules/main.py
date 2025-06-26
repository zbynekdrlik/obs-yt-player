"""
Main entry point module for OBS YouTube Player.
Handles all OBS script interface functions with proper state isolation.
"""

import obspython as obs
import os
from pathlib import Path

# Use absolute imports to fix module loading issue
from ytplay_modules.config import (
    SCRIPT_VERSION, SCENE_CHECK_DELAY,
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, DEFAULT_PLAYBACK_MODE,
    DEFAULT_AUDIO_ONLY_MODE, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
)
from ytplay_modules.state import (
    initialize_script_context, cleanup_state,
    get_playlist_url, set_playlist_url, 
    get_cache_dir, set_cache_dir,
    is_tools_ready, set_stop_threads,
    set_gemini_api_key,
    get_playback_mode, set_playback_mode,
    set_first_video_played, set_loop_video_id,
    get_current_playback_video_id, is_playing,
    is_audio_only_mode, set_audio_only_mode,
    set_script_name, set_script_dir,
    set_thread_script_context, set_current_script_path,
    get_script_name, get_script_dir
)
from ytplay_modules.logger import log, cleanup_logging
from ytplay_modules.ui import create_properties, check_configuration_warnings
from ytplay_modules.tools import start_tools_thread
from ytplay_modules.playlist import start_playlist_sync_thread, trigger_manual_sync
from ytplay_modules.download import start_video_processing_thread
from ytplay_modules.scene import verify_scene_setup, reset_scene_error_flag, on_frontend_event as scene_frontend_event
from ytplay_modules.playback import start_playback_controller, stop_playback_controller, get_current_video_from_media_source
from ytplay_modules.metadata import clear_gemini_failures
from ytplay_modules.reprocess import start_reprocess_thread
from ytplay_modules.cache import cleanup_temp_files

# Store timer references and settings per script
_script_data = {}

def script_description():
    """Return script description for OBS."""
    return """OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads."""

def script_load(settings, script_path):
    """Called when script is loaded."""
    # Initialize script-specific state
    state = initialize_script_context(script_path)
    
    # Extract script info
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    script_dir = os.path.dirname(script_path)
    
    # Store in state
    set_script_name(script_name)
    set_script_dir(script_dir)
    
    # Initialize script data
    _script_data[script_path] = {
        'settings': settings,
        'is_unloading': False,
        'verify_scene_timer': None,
        'warning_update_timer': None
    }
    
    set_stop_threads(False)
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    log("Gemini failures are tracked via filename markers (_gf) and retried on restart")
    
    # Reset scene error flag
    reset_scene_error_flag()
    
    # Clear Gemini failure cache on script restart
    clear_gemini_failures()
    
    # Apply initial settings
    script_update(settings, script_path)
    
    # Schedule scene verification
    def verify_scene_timer():
        set_current_script_path(script_path)
        verify_scene_setup()
        obs.timer_remove(verify_scene_timer)
    
    obs.timer_add(verify_scene_timer, SCENE_CHECK_DELAY)
    _script_data[script_path]['verify_scene_timer'] = verify_scene_timer
    
    # Start worker threads
    start_worker_threads(script_path)
    
    # Register frontend event callback
    def frontend_event_wrapper(event):
        set_current_script_path(script_path)
        scene_frontend_event(event)
    
    obs.obs_frontend_add_event_callback(frontend_event_wrapper)
    _script_data[script_path]['frontend_event_callback'] = frontend_event_wrapper
    
    log("Script loaded successfully")

def script_unload(script_path):
    """Called when script is unloaded."""
    set_current_script_path(script_path)
    
    log("Script unloading...")
    
    # Set unloading flag
    if script_path in _script_data:
        _script_data[script_path]['is_unloading'] = True
    
    # Signal threads to stop
    set_stop_threads(True)
    
    # Stop all worker threads
    stop_worker_threads(script_path)
    
    # Remove timers
    if script_path in _script_data:
        data = _script_data[script_path]
        
        if data.get('verify_scene_timer'):
            obs.timer_remove(data['verify_scene_timer'])
        
        if data.get('warning_update_timer'):
            obs.timer_remove(data['warning_update_timer'])
        
        # Remove frontend event callback
        if data.get('frontend_event_callback'):
            obs.obs_frontend_remove_event_callback(data['frontend_event_callback'])
    
    stop_playback_controller()
    
    # Clean up temp files
    cleanup_temp_files()
    
    # Clean up logging
    cleanup_logging()
    
    # Clean up script-specific state
    cleanup_state(script_path)
    
    # Clean up script data
    if script_path in _script_data:
        del _script_data[script_path]
    
    log("Script unloaded")

def script_properties(script_path):
    """Define script properties shown in OBS UI."""
    set_current_script_path(script_path)
    return create_properties(script_path, _script_data.get(script_path, {}))

def script_defaults(settings, script_path):
    """Set default values for script properties."""
    set_current_script_path(script_path)
    
    # Default playlist URL is now empty - user must configure
    obs.obs_data_set_default_string(settings, "playlist_url", "")
    
    # Default cache directory based on script name
    script_name = get_script_name()
    script_dir = get_script_dir()
    default_cache_dir = os.path.join(script_dir, f"{script_name}-cache")
    obs.obs_data_set_default_string(settings, "cache_dir", default_cache_dir)
    
    obs.obs_data_set_default_string(settings, "playback_mode", DEFAULT_PLAYBACK_MODE)
    obs.obs_data_set_default_int(settings, "audio_only_mode", 0 if not DEFAULT_AUDIO_ONLY_MODE else 1)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings, script_path):
    """Called when script properties are updated."""
    set_current_script_path(script_path)
    
    # Store settings reference
    if script_path in _script_data:
        _script_data[script_path]['settings'] = settings
    
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
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Mode: {playback_mode}, Audio-only: {audio_only_mode}")

def script_save(settings, script_path):
    """Called when OBS is saving data."""
    # Currently no special save handling needed
    pass

def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    # Extract script path from props (set by UI module)
    script_path = getattr(props, '_script_path', None)
    if script_path:
        set_current_script_path(script_path)
    
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

def start_worker_threads(script_path):
    """Start all background worker threads."""
    set_current_script_path(script_path)
    
    log("Starting worker threads...")
    
    # Start threads in order
    start_tools_thread()
    start_playlist_sync_thread()
    start_video_processing_thread()
    start_playback_controller()
    start_reprocess_thread()
    
    log("Worker threads started")

def stop_worker_threads(script_path):
    """Stop all background worker threads."""
    set_current_script_path(script_path)
    
    log("Stopping worker threads...")
    
    # Threads will check stop flag and exit
    # Each module handles its own thread cleanup
    
    log("Worker threads stopped")
