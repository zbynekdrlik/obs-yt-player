"""
Main module containing all OBS script interface logic.
This module is imported by the minimal main script to achieve <5KB size target.
"""

import obspython as obs
import os
from pathlib import Path

from config import (
    SCRIPT_VERSION, SCENE_CHECK_DELAY,
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, DEFAULT_PLAYBACK_MODE,
    DEFAULT_AUDIO_ONLY_MODE, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
)
from logger import log, cleanup_logging
from state import (
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
    get_script_name
)

# Store timer references
_verify_scene_timer = None
_warning_update_timer = None

# Global settings reference for warnings update
_global_settings = None

# Track script unload state
_is_unloading = False

# Script path will be set by the main script
_script_path = None
_script_name = None
_script_dir = None

def init_script_context(script_path):
    """Initialize the script context. Called by the minimal main script."""
    global _script_path, _script_name, _script_dir
    
    _script_path = script_path
    _script_dir = os.path.dirname(script_path)
    _script_name = os.path.splitext(os.path.basename(script_path))[0]
    
    # Initialize script-specific state
    initialize_script_context(_script_path)
    
    # Set script identification in state module
    set_script_name(_script_name)
    set_script_dir(_script_dir)

# ===== OBS SCRIPT INTERFACE =====
def script_description():
    """Return script description for OBS."""
    return """OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads."""

def check_configuration_warnings():
    """Check for configuration issues and return warning messages."""
    # Ensure correct script context is set before checking warnings
    set_current_script_path(_script_path)
    
    warnings = []
    
    # Check for missing scene
    scene_source = obs.obs_get_source_by_name(_script_name)
    if not scene_source:
        warnings.append(f"Scene '{_script_name}' not found")
    else:
        # Get scene from source before releasing
        scene = obs.obs_scene_from_source(scene_source)
        obs.obs_source_release(scene_source)
        
        # Check for missing sources within the scene
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
    
    # Check for missing playlist URL - use state from current script instance
    playlist_url = get_playlist_url()
    if not playlist_url or playlist_url.strip() == "":
        warnings.append("No playlist URL")
    
    # Check if tools are ready
    if not is_tools_ready():
        warnings.append("Tools not ready")
    
    return warnings

def update_warning_visibility(props, prop, settings):
    """Update the visibility and content of warning label."""
    # Safety check - don't access properties during unload
    if _is_unloading or not props:
        return False
    
    # Ensure correct script context is set
    set_current_script_path(_script_path)
    
    try:
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
    except Exception as e:
        # Catch any exceptions to prevent crashes
        log(f"Error updating warnings: {e}")
        return False
    
    return True

def script_properties(settings):
    """Define script properties shown in OBS UI."""
    # Ensure correct script context is set
    set_current_script_path(_script_path)
    
    props = obs.obs_properties_create()
    
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
    global _global_settings
    if _global_settings and not _is_unloading:
        update_warning_visibility(props, None, _global_settings)
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    # Ensure correct script context is set
    set_current_script_path(_script_path)
    
    # Default playlist URL is now empty - user must set it
    obs.obs_data_set_default_string(settings, "playlist_url", "")
    
    # Default cache directory based on script name
    default_cache_dir = os.path.join(_script_dir, f"{_script_name}-cache")
    obs.obs_data_set_default_string(settings, "cache_dir", default_cache_dir)
    
    obs.obs_data_set_default_string(settings, "playback_mode", DEFAULT_PLAYBACK_MODE)
    obs.obs_data_set_default_int(settings, "audio_only_mode", 0 if not DEFAULT_AUDIO_ONLY_MODE else 1)
    obs.obs_data_set_default_string(settings, "gemini_api_key", "")

def script_update(settings):
    """Called when script properties are updated."""
    # Ensure correct script context is set
    set_current_script_path(_script_path)
    
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
            # Import playback here to avoid circular import
            from playback import get_current_video_from_media_source
            
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

def warnings_update_timer():
    """Timer callback to periodically update warnings."""
    # Do not store reference to properties - create fresh each time
    # This ensures we're always working with valid properties
    if _global_settings:
        # Get fresh property ID and update warnings through OBS
        # This is safer than storing and reusing properties objects
        obs.timer_remove(warnings_update_timer)
        obs.timer_add(warnings_update_timer, 5000)

def verify_scene_timer():
    """Timer callback for scene verification with proper script context."""
    # Use set_current_script_path for main thread context
    set_current_script_path(_script_path)
    
    # Import here to avoid circular imports
    from scene import verify_scene_setup
    
    # Verify scene setup
    verify_scene_setup()
    
    # Remove this timer - only run once
    obs.timer_remove(verify_scene_timer)

def on_frontend_event_wrapper(event):
    """Wrapper for frontend event handler that sets proper script context."""
    # Set script context before handling event
    set_current_script_path(_script_path)
    
    # Import and call the actual handler from scene module
    from scene import on_frontend_event
    on_frontend_event(event)

def script_load(settings):
    """Called when script is loaded."""
    global _verify_scene_timer, _warning_update_timer, _global_settings, _is_unloading
    _global_settings = settings
    _is_unloading = False
    
    # Ensure script context is properly initialized
    initialize_script_context(_script_path)
    
    set_stop_threads(False)
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    
    # Log Gemini failure