"""
Main module for OBS YouTube Player.
Provides entry points for OBS script interface.
"""

import obspython as obs
import sys
import os
from pathlib import Path
import threading

# Import all needed modules
from config import (
    SCRIPT_VERSION, SCENE_CHECK_DELAY,
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, DEFAULT_PLAYBACK_MODE,
    DEFAULT_AUDIO_ONLY_MODE
)
from logger import log, cleanup_logging
from state import get_state, set_thread_script_context, clear_script_state
from tools import start_tools_thread
from playlist import start_playlist_sync_thread, trigger_manual_sync
from download import start_video_processing_thread
from scene import verify_scene_setup, on_frontend_event
from playback import start_playback_controller, stop_playback_controller, get_current_video_from_media_source
from metadata import clear_gemini_failures
from reprocess import start_reprocess_thread
from ui import create_properties, show_configuration_warnings
from cache import cleanup_temp_files

# Store timer references per script
_verify_scene_timers = {}

# Thread references per script
_worker_threads = {}

def script_description():
    """Return script description for OBS."""
    return __doc__.strip()

def script_properties(script_path):
    """Define script properties shown in OBS UI."""
    set_thread_script_context(script_path)
    
    props = create_properties()
    
    # Check for configuration warnings
    state = get_state()
    warnings = show_configuration_warnings(state)
    
    # Add warnings to properties
    if warnings:
        # Add separator
        obs.obs_properties_add_text(
            props,
            "warning_separator",
            "─────────────────────────────",
            obs.OBS_TEXT_INFO
        )
        
        # Add each warning
        for i, warning in enumerate(warnings):
            obs.obs_properties_add_text(
                props,
                f"warning_{i}",
                f"⚠️ {warning}",
                obs.OBS_TEXT_INFO
            )
    
    return props

def script_defaults(settings, script_path):
    """Set default values for script properties."""
    set_thread_script_context(script_path)
    
    # Get cache directory based on script name
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    script_dir = os.path.dirname(script_path)
    default_cache_dir = os.path.join(script_dir, f"{script_name}-cache")
    
    obs.obs_data_set_default_string(settings, "playlist_url", "")  # No default URL
    obs.obs_data_set_default_string(settings, "cache_dir", default_cache_dir)
    obs.obs_data_set_default_string(settings, "playback_mode", DEFAULT_PLAYBACK_MODE)
    obs.obs_data_set_default_bool(settings, "audio_only_mode", DEFAULT_AUDIO_ONLY_MODE)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings, script_path):
    """Called when script properties are updated."""
    set_thread_script_context(script_path)
    
    state = get_state()
    
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    playback_mode = obs.obs_data_get_string(settings, "playback_mode")
    audio_only_mode = obs.obs_data_get_bool(settings, "audio_only_mode")
    gemini_key = obs.obs_data_get_string(settings, "gemini_api_key")
    
    # Check if playback mode changed
    old_mode = state.get('playback_mode', DEFAULT_PLAYBACK_MODE)
    
    # Update state
    state['playlist_url'] = playlist_url
    state['cache_dir'] = cache_dir
    state['playback_mode'] = playback_mode
    state['audio_only_mode'] = audio_only_mode
    state['gemini_api_key'] = gemini_key if gemini_key else None
    
    # Reset playback state if mode changed
    if old_mode != playback_mode:
        log(f"Playback mode changed to: {playback_mode}")
        
        # Handle mode-specific state changes
        if playback_mode == PLAYBACK_MODE_SINGLE and state.get('is_playing', False):
            state['first_video_played'] = True
            log("Single mode enabled - current video counts as first video")
        else:
            state['first_video_played'] = False
        
        if playback_mode == PLAYBACK_MODE_LOOP and state.get('is_playing', False):
            current_video_id = state.get('current_video_id')
            if not current_video_id:
                current_video_id = get_current_video_from_media_source()
            
            if current_video_id:
                state['loop_video_id'] = current_video_id
                log(f"Loop mode enabled - will loop current video (ID: {current_video_id})")
            else:
                state['loop_video_id'] = None
                log("Loop mode enabled - will loop next video that plays")
        else:
            state['loop_video_id'] = None
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Mode: {playback_mode}, Audio-only: {audio_only_mode}")
    
    if gemini_key:
        log("Gemini API key configured")

def script_load(settings, script_path):
    """Called when script is loaded."""
    global _verify_scene_timers, _worker_threads
    
    set_thread_script_context(script_path)
    
    state = get_state()
    state['stop_threads'] = False
    state['script_path'] = script_path
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    
    # Clear Gemini failure cache on script restart
    clear_gemini_failures()
    
    # Apply initial settings
    script_update(settings, script_path)
    
    # Schedule scene verification after delay
    def verify_scene_wrapper():
        set_thread_script_context(script_path)
        verify_scene_setup()
    
    _verify_scene_timers[script_path] = verify_scene_wrapper
    obs.timer_add(verify_scene_wrapper, SCENE_CHECK_DELAY)
    
    # Start worker threads
    start_worker_threads(script_path)
    
    # Register frontend event callbacks
    def frontend_event_wrapper(event):
        set_thread_script_context(script_path)
        on_frontend_event(event)
    
    obs.obs_frontend_add_event_callback(frontend_event_wrapper)
    state['frontend_event_callback'] = frontend_event_wrapper
    
    log("Script loaded successfully")

def script_unload(script_path):
    """Called when script is unloaded."""
    global _verify_scene_timers, _worker_threads
    
    set_thread_script_context(script_path)
    
    log("Script unloading...")
    
    state = get_state()
    state['stop_threads'] = True
    
    # Stop all worker threads
    stop_worker_threads(script_path)
    
    # Remove timers
    if script_path in _verify_scene_timers:
        obs.timer_remove(_verify_scene_timers[script_path])
        del _verify_scene_timers[script_path]
    
    stop_playback_controller()
    
    # Remove frontend callback
    if 'frontend_event_callback' in state and state['frontend_event_callback']:
        obs.obs_frontend_remove_event_callback(state['frontend_event_callback'])
    
    # Clean up temp files
    cleanup_temp_files()
    
    # Clean up logging
    cleanup_logging()
    
    # Clear state for this script
    clear_script_state(script_path)
    
    log("Script unloaded")

def script_save(settings, script_path):
    """Called when OBS is saving data."""
    set_thread_script_context(script_path)
    # Currently no special save handling needed

def sync_now_callback(props, prop, script_path):
    """Callback for Sync Now button."""
    set_thread_script_context(script_path)
    
    log("Manual sync requested")
    
    state = get_state()
    if not state.get('tools_ready', False):
        log("Cannot sync - tools not ready yet")
        return True
    
    # Trigger playlist sync
    trigger_manual_sync()
    return True

def start_worker_threads(script_path):
    """Start all background worker threads."""
    global _worker_threads
    
    set_thread_script_context(script_path)
    log("Starting worker threads...")
    
    # Create thread list for this script
    _worker_threads[script_path] = []
    
    # Define thread functions with context
    def tools_thread():
        set_thread_script_context(script_path)
        start_tools_thread()
    
    def playlist_thread():
        set_thread_script_context(script_path)
        start_playlist_sync_thread()
    
    def video_thread():
        set_thread_script_context(script_path)
        start_video_processing_thread()
    
    def playback_thread():
        set_thread_script_context(script_path)
        start_playback_controller()
    
    def reprocess_thread():
        set_thread_script_context(script_path)
        start_reprocess_thread()
    
    # Start threads
    threads = [
        threading.Thread(target=tools_thread, name=f"{script_path}-tools"),
        threading.Thread(target=playlist_thread, name=f"{script_path}-playlist"),
        threading.Thread(target=video_thread, name=f"{script_path}-video"),
        threading.Thread(target=playback_thread, name=f"{script_path}-playback"),
        threading.Thread(target=reprocess_thread, name=f"{script_path}-reprocess")
    ]
    
    for thread in threads:
        thread.daemon = True
        thread.start()
        _worker_threads[script_path].append(thread)
    
    log("Worker threads started")

def stop_worker_threads(script_path):
    """Stop all background worker threads."""
    global _worker_threads
    
    set_thread_script_context(script_path)
    log("Stopping worker threads...")
    
    # Threads will check stop flag and exit
    # Wait for threads to finish
    if script_path in _worker_threads:
        for thread in _worker_threads[script_path]:
            thread.join(timeout=5.0)
        del _worker_threads[script_path]
    
    log("Worker threads stopped")
