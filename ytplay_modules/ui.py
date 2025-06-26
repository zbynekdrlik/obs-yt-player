"""
UI property definitions and configuration warnings for OBS YouTube Player.
Provides user-friendly interface with clear feedback about configuration issues.
"""

import obspython as obs
from typing import List, Dict, Any

from config import (
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP,
    DEFAULT_PLAYBACK_MODE, DEFAULT_AUDIO_ONLY_MODE
)

def create_properties() -> obs.obs_properties_t:
    """Create script properties for OBS UI."""
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
    
    obs.obs_property_list_add_string(playback_mode, "Continuous (Play all videos)", PLAYBACK_MODE_CONTINUOUS)
    obs.obs_property_list_add_string(playback_mode, "Single (Play one video and stop)", PLAYBACK_MODE_SINGLE)
    obs.obs_property_list_add_string(playback_mode, "Loop (Repeat current video)", PLAYBACK_MODE_LOOP)
    
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
        None  # Callback will be set by main module
    )
    
    return props

def show_configuration_warnings(state: Dict[str, Any]) -> List[str]:
    """
    Check configuration and return list of warnings.
    
    Args:
        state: Current script state dictionary
        
    Returns:
        List of warning messages to display
    """
    warnings = []
    
    # Check playlist URL
    if not state.get('playlist_url'):
        warnings.append("No playlist URL configured")
    
    # Check scene setup
    if not state.get('scene_found'):
        import os
        script_path = state.get('script_path', '')
        script_name = os.path.splitext(os.path.basename(script_path))[0] if script_path else 'ytplay'
        warnings.append(f"Scene '{script_name}' not found - please create it")
    
    # Check media source
    if state.get('scene_found') and not state.get('media_source_found'):
        warnings.append("Media Source 'video' not found in scene")
    
    # Check text source
    if state.get('scene_found') and not state.get('text_source_found'):
        warnings.append("Text Source 'title' not found in scene")
    
    # Check tools
    if not state.get('tools_ready'):
        warnings.append("Tools (yt-dlp/FFmpeg) not ready - downloading...")
    
    # Check cache directory
    cache_dir = state.get('cache_dir')
    if cache_dir:
        import os
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception:
                warnings.append(f"Cannot create cache directory: {cache_dir}")
    
    return warnings

def create_warning_properties(props: obs.obs_properties_t, warnings: List[str]):
    """
    Add warning messages to properties.
    
    Args:
        props: OBS properties object
        warnings: List of warning messages
    """
    if not warnings:
        return
    
    # Add separator
    obs.obs_properties_add_text(
        props,
        "warning_separator",
        "─────────────────────────────",
        obs.OBS_TEXT_INFO
    )
    
    # Add warning header
    obs.obs_properties_add_text(
        props,
        "warning_header",
        "⚠️ Configuration Issues:",
        obs.OBS_TEXT_INFO
    )
    
    # Add each warning
    for i, warning in enumerate(warnings):
        obs.obs_properties_add_text(
            props,
            f"warning_{i}",
            f"  • {warning}",
            obs.OBS_TEXT_INFO
        )

def update_button_callback(props: obs.obs_properties_t, callback):
    """
    Update the sync button callback.
    
    Args:
        props: OBS properties object
        callback: Callback function for sync button
    """
    # Find the sync button property and update its callback
    sync_button = obs.obs_properties_get(props, "sync_now")
    if sync_button:
        obs.obs_property_set_modified_callback(sync_button, callback)
