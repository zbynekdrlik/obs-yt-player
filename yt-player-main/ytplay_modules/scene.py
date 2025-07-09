"""Scene and source management for OBS YouTube Player."""

import obspython as obs
from .logger import log
from .config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME, SCRIPT_NAME
from .state import (
    is_scene_active, set_scene_active, is_playing,
    get_cached_videos, get_loop_video_id, get_playback_mode
)
from .metadata import update_window_title

# Default settings
DEFAULT_TEXT_SETTINGS = {
    "font": {
        "face": "Arial",
        "size": 48,
        "style": "Regular",
        "flags": 0
    },
    "color": 0xFFFFFFFF,  # White
    "opacity": 100,
    "outline": True,
    "outline_color": 0xFF000000,  # Black
    "outline_size": 2,
    "outline_opacity": 100,
    "align": "center",
    "valign": "center"
}

def create_scene_if_needed():
    """Create scene and sources if they don't exist."""
    # Check if scene exists
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    if scene_source:
        obs.obs_source_release(scene_source)
        log(f"Scene '{SCENE_NAME}' already exists")
        return
    
    # Create new scene
    scene_source = obs.obs_source_create("scene", SCENE_NAME, None, None)
    if not scene_source:
        log(f"ERROR: Failed to create scene '{SCENE_NAME}'")
        return
    
    # Get the scene object
    scene = obs.obs_scene_from_source(scene_source)
    
    # Create Media Source
    media_settings = obs.obs_data_create()
    obs.obs_data_set_bool(media_settings, "hw_decode", True)
    obs.obs_data_set_bool(media_settings, "is_local_file", True)
    obs.obs_data_set_bool(media_settings, "restart_on_activate", False)
    obs.obs_data_set_bool(media_settings, "close_when_inactive", False)
    obs.obs_data_set_bool(media_settings, "looping", False)  # We manage looping
    
    media_source = obs.obs_source_create("ffmpeg_source", MEDIA_SOURCE_NAME, media_settings, None)
    if media_source:
        # Add to scene
        scene_item = obs.obs_scene_add(scene, media_source)
        
        # Scale to fit (you might want to adjust this)
        obs.obs_sceneitem_set_scale_filter(scene_item, obs.OBS_SCALE_FILTER_LANCZOS)
        
        # Release source reference
        obs.obs_source_release(media_source)
        log(f"Created Media Source: {MEDIA_SOURCE_NAME}")
    else:
        log(f"ERROR: Failed to create Media Source: {MEDIA_SOURCE_NAME}")
    
    obs.obs_data_release(media_settings)
    
    # Create Text Source
    text_settings = obs.obs_data_create()
    
    # Apply default text settings
    font_obj = obs.obs_data_create()
    obs.obs_data_set_string(font_obj, "face", DEFAULT_TEXT_SETTINGS["font"]["face"])
    obs.obs_data_set_int(font_obj, "size", DEFAULT_TEXT_SETTINGS["font"]["size"])
    obs.obs_data_set_string(font_obj, "style", DEFAULT_TEXT_SETTINGS["font"]["style"])
    obs.obs_data_set_int(font_obj, "flags", DEFAULT_TEXT_SETTINGS["font"]["flags"])
    
    obs.obs_data_set_obj(text_settings, "font", font_obj)
    obs.obs_data_set_int(text_settings, "color", DEFAULT_TEXT_SETTINGS["color"])
    obs.obs_data_set_int(text_settings, "opacity", DEFAULT_TEXT_SETTINGS["opacity"])
    obs.obs_data_set_bool(text_settings, "outline", DEFAULT_TEXT_SETTINGS["outline"])
    obs.obs_data_set_int(text_settings, "outline_color", DEFAULT_TEXT_SETTINGS["outline_color"])
    obs.obs_data_set_int(text_settings, "outline_size", DEFAULT_TEXT_SETTINGS["outline_size"])
    obs.obs_data_set_int(text_settings, "outline_opacity", DEFAULT_TEXT_SETTINGS["outline_opacity"])
    obs.obs_data_set_string(text_settings, "align", DEFAULT_TEXT_SETTINGS["align"])
    obs.obs_data_set_string(text_settings, "valign", DEFAULT_TEXT_SETTINGS["valign"])
    
    obs.obs_data_release(font_obj)
    
    text_source = obs.obs_source_create("text_gdiplus", TEXT_SOURCE_NAME, text_settings, None)
    if text_source:
        # Add to scene
        scene_item = obs.obs_scene_add(scene, text_source)
        
        # Position at bottom of screen (you might want to adjust this)
        pos = obs.vec2()
        pos.x = 960  # Center X for 1920x1080
        pos.y = 900  # Near bottom
        obs.obs_sceneitem_set_pos(scene_item, pos)
        obs.obs_sceneitem_set_alignment(scene_item, 5)  # Center alignment
        
        # Release source reference
        obs.obs_source_release(text_source)
        log(f"Created Text Source: {TEXT_SOURCE_NAME}")
    else:
        log(f"ERROR: Failed to create Text Source: {TEXT_SOURCE_NAME}")
    
    obs.obs_data_release(text_settings)
    
    # Release scene source
    obs.obs_source_release(scene_source)
    
    log(f"Scene '{SCENE_NAME}' created with media and text sources")

def check_scene_active():
    """Check if our scene is currently active."""
    current_scene = obs.obs_frontend_get_current_scene()
    if not current_scene:
        return False
    
    scene_name = obs.obs_source_get_name(current_scene)
    obs.obs_source_release(current_scene)
    
    return scene_name == SCENE_NAME

def on_frontend_event(event):
    """Handle OBS frontend events."""
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        # Check if our scene is now active
        was_active = is_scene_active()
        is_active = check_scene_active()
        
        if is_active != was_active:
            set_scene_active(is_active)
            if is_active:
                log(f"Scene '{SCENE_NAME}' activated")
                update_window_title()
            else:
                log(f"Scene '{SCENE_NAME}' deactivated")
                
                # Check if we're in loop mode
                from .config import PLAYBACK_MODE_LOOP
                if get_playback_mode() == PLAYBACK_MODE_LOOP:
                    # Clear the loop video when scene becomes inactive
                    from .state import set_loop_video_id
                    set_loop_video_id(None)
                    log("Loop mode: Cleared loop video due to scene change")

def on_scene_change(calldata):
    """Legacy callback for scene changes."""
    # This is now handled by frontend events
    pass

def setup_scene_callback():
    """Set up scene change callbacks."""
    # Note: Frontend events are registered in script_load
    # This function kept for compatibility
    pass

def verify_scene_setup():
    """Verify scene exists and is properly configured."""
    log("Verifying scene setup...")
    
    # Create scene if needed
    create_scene_if_needed()
    
    # Check initial scene state
    is_active = check_scene_active()
    set_scene_active(is_active)
    
    if is_active:
        log(f"Scene '{SCENE_NAME}' is currently active")
        update_window_title()
    else:
        log(f"Scene '{SCENE_NAME}' is not active")
    
    # Note about loop checkbox
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if media_source:
        log(f"IMPORTANT: Disable 'Loop' checkbox in {MEDIA_SOURCE_NAME} source properties!")
        log("The script manages looping behavior based on Playback Mode setting.")
        obs.obs_source_release(media_source)
    
    log("Scene verification complete")
    
    # Remove the timer so it only runs once
    obs.timer_remove(verify_scene_setup)