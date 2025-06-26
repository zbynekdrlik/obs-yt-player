"""
UI module for OBS YouTube Player.
Handles property definitions and configuration warnings.
"""

import obspython as obs
import os

from .config import (
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, 
    DEFAULT_PLAYBACK_MODE, DEFAULT_AUDIO_ONLY_MODE, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
)
from .state import (
    get_playlist_url, is_tools_ready, get_script_name, get_script_dir,
    set_current_script_path
)
from .logger import log

def check_configuration_warnings(script_path):
    """Check for configuration issues and return warning messages."""
    set_current_script_path(script_path)
    
    warnings = []
    
    script_name = get_script_name()
    
    # Check for missing scene
    scene_source = obs.obs_get_source_by_name(script_name)
    if not scene_source:
        warnings.append(f"Scene '{script_name}' not found")
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
    
    # Check for missing playlist URL
    playlist_url = get_playlist_url()
    if not playlist_url or playlist_url.strip() == "":
        warnings.append("No playlist URL")
    
    # Check if tools are ready
    if not is_tools_ready():
        warnings.append("Tools not ready")
    
    return warnings

def update_warning_visibility(props, prop, settings):
    """Update the visibility and content of warning label."""
    # Extract script path from props
    script_path = getattr(props, '_script_path', None)
    if not script_path:
        return False
    
    # Get script data
    script_data = getattr(props, '_script_data', {})
    
    # Safety check - don't access properties during unload
    if script_data.get('is_unloading') or not props:
        return False
    
    set_current_script_path(script_path)
    
    try:
        warnings = check_configuration_warnings(script_path)
        
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

def create_properties(script_path, script_data):
    """Create properties for the script UI."""
    set_current_script_path(script_path)
    
    props = obs.obs_properties_create()
    
    # Store script context in props for callbacks
    props._script_path = script_path
    props._script_data = script_data
    
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
    def sync_now_callback_wrapper(props, prop):
        # Import here to avoid circular dependency
        from .main import sync_now_callback
        # Set script path in props for the callback
        props._script_path = script_path
        return sync_now_callback(props, prop)
    
    sync_button = obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback_wrapper
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
    settings = script_data.get('settings')
    if settings and not script_data.get('is_unloading'):
        update_warning_visibility(props, None, settings)
    
    return props
