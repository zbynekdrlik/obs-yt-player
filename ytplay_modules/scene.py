"""
Scene management for OBS YouTube Player.
Verifies scene setup and handles frontend events.
"""

import obspython as obs
from config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
from logger import log
from state import (
    get_script_name, is_scene_verified, set_scene_verified,
    is_scene_error_shown, set_scene_error_shown
)

def verify_scene_setup():
    """Verify that the required scene and sources exist."""
    script_name = get_script_name()
    
    # Check if scene exists
    scene_source = obs.obs_get_source_by_name(script_name)
    if not scene_source:
        if not is_scene_error_shown():
            log(f"ERROR: Scene '{script_name}' not found! Please create it.")
            set_scene_error_shown(True)
        return False
    
    # Get scene from source
    scene = obs.obs_scene_from_source(scene_source)
    obs.obs_source_release(scene_source)
    
    if not scene:
        log(f"ERROR: Could not get scene from source '{script_name}'")
        return False
    
    # Check for Media Source
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not media_source:
        if not is_scene_error_shown():
            log(f"ERROR: Media Source '{MEDIA_SOURCE_NAME}' not found in any scene!")
            set_scene_error_shown(True)
        return False
    obs.obs_source_release(media_source)
    
    # Check for Text Source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not text_source:
        if not is_scene_error_shown():
            log(f"ERROR: Text Source '{TEXT_SOURCE_NAME}' not found in any scene!")
            set_scene_error_shown(True)
        return False
    obs.obs_source_release(text_source)
    
    # All good!
    if not is_scene_verified():
        log(f"Scene '{script_name}' verified with required sources")
        set_scene_verified(True)
    
    return True

def on_frontend_event(event):
    """Handle OBS frontend events."""
    # Currently we don't need to handle specific events
    # But this is where scene change detection would go
    pass

def reset_scene_error_flag():
    """Reset the scene error shown flag."""
    set_scene_error_shown(False)
