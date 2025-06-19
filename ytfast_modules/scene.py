"""
Scene management for OBS YouTube Player.
Handles scene verification and frontend events.
"""

import obspython as obs
import time
from config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
from logger import log
from state import (
    set_scene_active, is_scene_active, is_playing, 
    set_stop_requested, set_stop_threads
)

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

def verify_initial_state():
    """Verify initial state when OBS finishes loading."""
    current_scene = obs.obs_frontend_get_current_scene()
    if current_scene:
        scene_name = obs.obs_source_get_name(current_scene)
        is_active = (scene_name == SCENE_NAME)
        set_scene_active(is_active)
        log(f"Initial scene check: {scene_name} (active: {is_active})")
        obs.obs_source_release(current_scene)

def on_frontend_event(event):
    """Handle OBS frontend events."""
    try:
        if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
            handle_scene_change()
        elif event == obs.OBS_FRONTEND_EVENT_EXIT:
            handle_obs_exit()
        elif event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
            log("OBS finished loading")
            verify_initial_state()
    except Exception as e:
        log(f"ERROR in frontend event handler: {e}")

def handle_scene_change():
    """Handle scene change events with improved logic."""
    current_scene = obs.obs_frontend_get_current_scene()
    if not current_scene:
        return
    
    try:
        scene_name = obs.obs_source_get_name(current_scene)
        was_active = is_scene_active()
        is_active = (scene_name == SCENE_NAME)
        
        # Only act on actual changes
        if is_active != was_active:
            set_scene_active(is_active)
            
            if is_active:
                log(f"Scene activated: {scene_name}")
                # Playback controller will handle starting
            else:
                log(f"Scene deactivated (was on: {scene_name})")
                # Request stop if playing
                if is_playing():
                    set_stop_requested(True)
                    
    finally:
        obs.obs_source_release(current_scene)

def handle_obs_exit():
    """Handle OBS exit event."""
    log("OBS exiting - initiating cleanup")
    
    # Signal all threads to stop
    set_stop_threads(True)
    
    # Request playback stop
    if is_playing():
        set_stop_requested(True)
    
    # Allow brief time for cleanup
    time.sleep(0.1)
