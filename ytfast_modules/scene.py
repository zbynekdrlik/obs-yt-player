"""
Scene management for OBS YouTube Player.
Handles scene verification and frontend events.
"""

import obspython as obs
from config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
from logger import log
from state import set_scene_active

def verify_scene_setup():
    """Verify that required scene and sources exist."""
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    if not scene_source:
        log(f"ERROR: Required scene '{SCENE_NAME}' not found! Please create it.")
        return
    
    scene = obs.obs_scene_from_source(scene_source)
    if scene:
        # Check for required sources
        media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        
        if not media_source:
            log(f"WARNING: Media Source '{MEDIA_SOURCE_NAME}' not found in scene")
        else:
            obs.obs_source_release(media_source)
            
        if not text_source:
            log(f"WARNING: Text Source '{TEXT_SOURCE_NAME}' not found in scene")
        else:
            obs.obs_source_release(text_source)
    
    obs.obs_source_release(scene_source)
    
    # Remove this timer - only run once
    obs.timer_remove(verify_scene_setup)

def on_frontend_event(event):
    """Handle OBS frontend events."""
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        # Check if our scene is active
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            scene_name = obs.obs_source_get_name(current_scene)
            scene_active = (scene_name == SCENE_NAME)
            set_scene_active(scene_active)
            log(f"Scene changed to: {scene_name}, Active: {scene_active}")
            obs.obs_source_release(current_scene)
