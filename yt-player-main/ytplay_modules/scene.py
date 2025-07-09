"""
Scene management for OBS YouTube Player.
Handles scene verification and frontend events with transition awareness.
Supports nested scene detection for scenes used as sources.
"""

import obspython as obs
import time
from .config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME, PLAYBACK_MODE_SINGLE
from .logger import log
from .state import (
    set_scene_active, is_scene_active, is_playing, 
    set_stop_threads, get_playback_mode, is_first_video_played,
    set_first_video_played
)

# Module-level variables for transition tracking
_last_scene_change_time = 0
_pending_deactivation = False
_deactivation_timer = None

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

def is_scene_visible_nested(scene_name, check_scene_source=None):
    """
    Check if a scene is visible as a nested source in the current program scene.
    
    Args:
        scene_name: The name of the scene to check for
        check_scene_source: Optional scene source to check within (defaults to current program scene)
    
    Returns:
        bool: True if the scene is visible as a nested source
    """
    # Get the scene to check within (default to current program scene)
    if check_scene_source is None:
        check_scene_source = obs.obs_frontend_get_current_scene()
        if not check_scene_source:
            return False
        need_release = True
    else:
        need_release = False
    
    try:
        # Get the scene object
        scene = obs.obs_scene_from_source(check_scene_source)
        if not scene:
            return False
        
        # Enumerate all scene items
        scene_items = obs.obs_scene_enum_items(scene)
        if not scene_items:
            return False
        
        found = False
        for scene_item in scene_items:
            # Check if item is visible
            if not obs.obs_sceneitem_visible(scene_item):
                continue
            
            # Get the source for this scene item
            source = obs.obs_sceneitem_get_source(scene_item)
            if not source:
                continue
            
            source_name = obs.obs_source_get_name(source)
            source_id = obs.obs_source_get_id(source)
            
            # Check if this is a scene source
            if source_id == "scene":
                if source_name == scene_name:
                    # Found our scene as a nested source
                    found = True
                    break
                else:
                    # This is another scene, check recursively for nested scenes
                    # But avoid infinite recursion by not checking the same scene
                    if source_name != obs.obs_source_get_name(check_scene_source):
                        if is_scene_visible_nested(scene_name, source):
                            found = True
                            break
        
        # Release the scene items
        obs.sceneitem_list_release(scene_items)
        
        return found
        
    finally:
        if need_release:
            obs.obs_source_release(check_scene_source)

def is_scene_active_or_nested():
    """
    Check if our scene is active either directly in program or as a nested source.
    
    Returns:
        bool: True if scene is active in any way
    """
    # First check if we're the direct program scene
    current_scene = obs.obs_frontend_get_current_scene()
    if current_scene:
        scene_name = obs.obs_source_get_name(current_scene)
        obs.obs_source_release(current_scene)
        if scene_name == SCENE_NAME:
            return True
    
    # Then check if we're nested in the current program scene
    return is_scene_visible_nested(SCENE_NAME)

def verify_initial_state():
    """Verify initial state when OBS finishes loading."""
    is_active = is_scene_active_or_nested()
    set_scene_active(is_active)
    log(f"Initial scene check: {SCENE_NAME} (active or nested: {is_active})")

def get_preview_scene_name():
    """Get the name of the scene in preview (for Studio Mode)."""
    preview_scene = obs.obs_frontend_get_current_preview_scene()
    if preview_scene:
        name = obs.obs_source_get_name(preview_scene)
        obs.obs_source_release(preview_scene)
        return name
    return None

def is_studio_mode_active():
    """Check if Studio Mode (preview/program) is active."""
    return obs.obs_frontend_preview_program_mode_active()

def delayed_deactivation():
    """Handle delayed deactivation after transition."""
    global _deactivation_timer, _pending_deactivation
    
    # Clear the timer reference
    obs.timer_remove(delayed_deactivation)
    _deactivation_timer = None
    
    # Now actually deactivate, but only if scene is not nested
    if _pending_deactivation and not is_scene_active_or_nested():
        log("Deactivating scene after transition delay")
        set_scene_active(False)
        # Playback controller will handle stopping when scene is inactive
        _pending_deactivation = False

def on_frontend_event(event):
    """Handle OBS frontend events."""
    try:
        if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
            handle_scene_change()
        elif event == obs.OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED:
            handle_preview_change()
        elif event == obs.OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED:
            handle_transition_duration_changed()
        elif event == obs.OBS_FRONTEND_EVENT_EXIT:
            handle_obs_exit()
        elif event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
            log("OBS finished loading")
            verify_initial_state()
    except Exception as e:
        log(f"ERROR in frontend event handler: {e}")

def handle_preview_change():
    """
    Handle preview scene change in Studio Mode.
    This lets us prepare for upcoming transitions.
    """
    if not is_studio_mode_active():
        return
    
    preview_scene_name = get_preview_scene_name()
    if preview_scene_name:
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            current_scene_name = obs.obs_source_get_name(current_scene)
            obs.obs_source_release(current_scene)
            
            # If our scene is now in preview and not in program, it might go live soon
            if preview_scene_name == SCENE_NAME and current_scene_name != SCENE_NAME:
                log(f"Scene '{SCENE_NAME}' loaded in preview, ready to transition")

def handle_transition_duration_changed():
    """Handle transition duration change event."""
    # Get the new transition duration when user changes it
    duration = obs.obs_frontend_get_transition_duration()
    log(f"Transition duration changed to: {duration}ms")

def handle_scene_change():
    """
    Handle scene change events with transition awareness.
    Now supports nested scene detection.
    """
    global _last_scene_change_time, _pending_deactivation, _deactivation_timer
    
    current_time = time.time() * 1000  # Convert to milliseconds
    time_since_last_change = current_time - _last_scene_change_time
    _last_scene_change_time = current_time
    
    was_active = is_scene_active()
    is_active = is_scene_active_or_nested()
    
    # Only act on actual changes
    if is_active == was_active:
        return
    
    # Cancel any pending deactivation if scene is becoming active
    if is_active and _deactivation_timer:
        obs.timer_remove(delayed_deactivation)
        _deactivation_timer = None
        _pending_deactivation = False
    
    # Get transition duration
    transition_duration = obs.obs_frontend_get_transition_duration()
    
    # Check if this is likely a transition (rapid scene changes or Studio Mode)
    is_likely_transition = (time_since_last_change < 100) or is_studio_mode_active()
    
    current_scene = obs.obs_frontend_get_current_scene()
    current_scene_name = "Unknown"
    if current_scene:
        current_scene_name = obs.obs_source_get_name(current_scene)
        obs.obs_source_release(current_scene)
    
    if is_active:
        # Scene becoming active - start immediately
        if current_scene_name == SCENE_NAME:
            log(f"Scene activated directly: {SCENE_NAME}")
        else:
            log(f"Scene activated as nested source in: {current_scene_name}")
        set_scene_active(True)
        
        # If in single mode and first video was already played, reset it
        # This allows playing one video each time the scene is activated
        if get_playback_mode() == PLAYBACK_MODE_SINGLE and is_first_video_played():
            log("Single mode: Resetting first video played flag for new scene activation")
            set_first_video_played(False)
        
        # Playback controller will handle starting
        
    else:
        # Scene becoming inactive
        if is_likely_transition and transition_duration > 300:
            # This is likely a transition - delay the deactivation
            log(f"Scene transitioning out, delaying stop for {transition_duration}ms")
            _pending_deactivation = True
            
            # Set timer for deactivation after transition completes
            if _deactivation_timer:
                obs.timer_remove(delayed_deactivation)
            _deactivation_timer = delayed_deactivation
            obs.timer_add(_deactivation_timer, int(transition_duration))
        else:
            # Instant scene change or very short transition
            log(f"Scene deactivated (no longer visible in: {current_scene_name})")
            set_scene_active(False)
            # Playback controller will handle stopping

def handle_obs_exit():
    """Handle OBS exit event."""
    global _deactivation_timer
    
    log("OBS exiting - initiating cleanup")
    
    # Cancel any pending timers
    if _deactivation_timer:
        obs.timer_remove(delayed_deactivation)
        _deactivation_timer = None
    
    # Signal all threads to stop
    set_stop_threads(True)
    
    # Allow brief time for cleanup
    time.sleep(0.1)
