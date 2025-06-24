"""
Main playback controller.
Coordinates playback operations and manages the controller timer.
"""

import obspython as obs
import os
from logger import log
from config import (
    PLAYBACK_CHECK_INTERVAL, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME, 
    SCENE_NAME, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP, PLAYBACK_MODE_CONTINUOUS
)
from state import (
    is_playing, set_playing, set_current_video_path,
    set_current_playback_video_id, get_cached_video_info,
    get_cached_videos, is_scene_active, should_stop_threads,
    get_playback_mode, is_first_video_played, set_first_video_played,
    get_loop_video_id, set_loop_video_id
)
from ytfast_modules.media_control import (
    force_disable_media_loop, get_media_state, get_media_duration,
    get_current_video_from_media_source, update_media_source,
    stop_media_source, update_text_source_content
)
from ytfast_modules.opacity_control import (
    ensure_opacity_filter, cancel_opacity_timer,
    get_current_opacity, fade_out_text, set_current_opacity
)
from ytfast_modules.title_manager import (
    cancel_title_timers, schedule_title_show, schedule_title_clear_with_delay
)
from ytfast_modules.video_selector import (
    select_next_video, validate_video_file, get_video_display_info
)
from ytfast_modules.state_handlers import (
    handle_playing_state, handle_ended_state, handle_stopped_state,
    handle_none_state, cancel_loop_restart_timer, reset_playback_tracking,
    set_preloaded_video_state, set_manual_stop_detected, clear_loop_restart_state
)

# Module-level variables
_playback_timer = None
_waiting_for_videos_logged = False
_last_cached_count = 0
_first_run = True
_sources_verified = False
_initial_state_checked = False


def verify_sources():
    """Verify that required sources exist and log their status."""
    global _sources_verified
    
    # Check scene
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    scene_exists = scene_source is not None
    if scene_source:
        obs.obs_source_release(scene_source)
    
    # Check media source
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    media_exists = media_source is not None
    if media_source:
        # Get source type for debugging
        source_id = obs.obs_source_get_id(media_source)
        obs.obs_source_release(media_source)
    else:
        source_id = "not found"
    
    # Check text source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    text_exists = text_source is not None
    if text_source:
        obs.obs_source_release(text_source)
    
    # Log verification results
    if not _sources_verified or not (scene_exists and media_exists and text_exists):
        log("=== SOURCE VERIFICATION ===")
        log(f"Scene '{SCENE_NAME}': {'✓ EXISTS' if scene_exists else '✗ MISSING'}")
        log(f"Media Source '{MEDIA_SOURCE_NAME}': {'✓ EXISTS' if media_exists else '✗ MISSING'} (type: {source_id})")
        log(f"Text Source '{TEXT_SOURCE_NAME}': {'✓ EXISTS' if text_exists else '✗ MISSING'}")
        
        # Important note about media source configuration
        if media_exists:
            log("NOTE: Script will disable OBS 'Loop' checkbox to manage playback behavior")
            # Force disable loop on first run
            force_disable_media_loop()
        
        log("==========================")
        _sources_verified = True
    
    return scene_exists and media_exists and text_exists


def playback_controller():
    """
    Main playback controller - runs on main thread via timer.
    Manages video playback state and transitions.
    """
    global _waiting_for_videos_logged, _last_cached_count, _first_run, _initial_state_checked
    
    try:
        # Priority 1: Check if we're shutting down
        if should_stop_threads():
            if is_playing():
                stop_current_playback()
            return
        
        # Verify sources exist
        if not verify_sources():
            return
        
        # Ensure opacity filter exists
        ensure_opacity_filter()
        
        # Priority 2: Check if scene is active
        playback_mode = get_playback_mode()
        scene_active = is_scene_active()
        
        # Handle scene inactive state based on playback mode
        if not scene_active:
            if is_playing():
                if playback_mode == PLAYBACK_MODE_SINGLE:
                    log("Scene inactive in single mode, stopping playback")
                    stop_current_playback()
                    return
                elif playback_mode == PLAYBACK_MODE_LOOP:
                    log("Scene inactive in loop mode, stopping playback")
                    # Clear loop video when scene becomes inactive
                    set_loop_video_id(None)
                    # Reset first video played flag so it can start fresh when scene becomes active
                    set_first_video_played(False)
                    stop_current_playback()
                    return
                elif playback_mode == PLAYBACK_MODE_CONTINUOUS:
                    # Don't return! Continue processing in continuous mode
                    log("Scene inactive but continuing playback in continuous mode")
            else:
                # Not playing and scene inactive - nothing to do
                _waiting_for_videos_logged = False
                return
        
        # Check if we have videos to play
        cached_videos = get_cached_videos()
        current_count = len(cached_videos)
        
        # Track changes in video count
        if current_count != _last_cached_count:
            if _last_cached_count == 0 and current_count > 0:
                log(f"First video available! Starting playback with {current_count} video(s)")
                # Don't return here! Continue to process the state
            elif current_count > _last_cached_count:
                log(f"New video added to cache. Total videos: {current_count}")
            _last_cached_count = current_count
            _waiting_for_videos_logged = False
            # Reset first run flag when videos become available
            if current_count > 0:
                _first_run = True
        
        if not cached_videos:
            # Log waiting message only once
            if not _waiting_for_videos_logged:
                log("Waiting for videos to be downloaded and processed...")
                _waiting_for_videos_logged = True
            return
        
        # Reset waiting flag since we have videos
        _waiting_for_videos_logged = False
        
        # Get current media state
        media_state = get_media_state(MEDIA_SOURCE_NAME)
        
        # Debug logging on first run with videos
        if _first_run and cached_videos:
            _first_run = False
            state_names = {
                obs.OBS_MEDIA_STATE_NONE: "NONE",
                obs.OBS_MEDIA_STATE_PLAYING: "PLAYING", 
                obs.OBS_MEDIA_STATE_STOPPED: "STOPPED",
                obs.OBS_MEDIA_STATE_ENDED: "ENDED"
            }
            state_name = state_names.get(media_state, f"UNKNOWN({media_state})")
            log(f"DEBUG: Media state = {state_name}, is_playing = {is_playing()}, scene_active = {scene_active}")
        
        # Handle initial state mismatch (media playing but script thinks it's not)
        if not _initial_state_checked:
            _initial_state_checked = True
            
            # Always force disable loop on startup
            force_disable_media_loop()
            
            if media_state == obs.OBS_MEDIA_STATE_PLAYING and not is_playing():
                # Check if this is valid media or just empty/invalid source
                duration = get_media_duration(MEDIA_SOURCE_NAME)
                if duration <= 0:
                    # No valid media, start fresh
                    log("No valid media in source, starting fresh playback")
                    start_next_video()
                    return
                    
                log("Media source is already playing - letting pre-loaded video play")
                # Mark that we're handling a pre-loaded video
                set_preloaded_video_state(False, True)
                # Update our state to match reality
                set_playing(True)
                
                # Try to identify the current video
                current_video_id = get_current_video_from_media_source()
                if current_video_id:
                    set_current_playback_video_id(current_video_id)
                    log(f"Identified pre-loaded video: {current_video_id}")
                    
                    # If we're in loop mode, set this as the loop video
                    if get_playback_mode() == PLAYBACK_MODE_LOOP and not get_loop_video_id():
                        set_loop_video_id(current_video_id)
                        log(f"Loop mode - Set pre-loaded video as loop video: {current_video_id}")
                
                # Check if we need to fade out the title for pre-loaded video
                from ytfast_modules.media_control import get_media_time
                from ytfast_modules.title_manager import TITLE_CLEAR_BEFORE_END, schedule_title_clear_from_current
                current_time = get_media_time(MEDIA_SOURCE_NAME)
                if duration > 0 and current_time > 0:
                    remaining_ms = duration - current_time
                    # If we're already close to the end, schedule fade out
                    if remaining_ms > 0 and remaining_ms < ((TITLE_CLEAR_BEFORE_END + 10) * 1000):
                        schedule_title_clear_from_current(remaining_ms)
                return  # Let it play out
        
        # NEW: Check if we should start playback when scene is active but not playing
        # This handles the case where scene becomes active but media state isn't NONE
        if scene_active and not is_playing() and cached_videos:
            # Check mode restrictions
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                # Don't start new playback in single mode after first video
                pass
            else:
                # For any media state (NONE, STOPPED, ENDED), if scene is active and we're not playing, start
                if media_state in [obs.OBS_MEDIA_STATE_NONE, obs.OBS_MEDIA_STATE_STOPPED, obs.OBS_MEDIA_STATE_ENDED]:
                    log(f"Scene active but not playing (state: {media_state}), starting playback")
                    
                    # In loop mode, clear the loop video to select a new random one
                    if playback_mode == PLAYBACK_MODE_LOOP and get_loop_video_id():
                        log("Loop mode: Clearing previous loop video to select new random video")
                        set_loop_video_id(None)
                    
                    start_next_video()
                    return
        
        # Handle different states - this now runs for continuous mode even when scene is inactive
        if media_state == obs.OBS_MEDIA_STATE_PLAYING:
            handle_playing_state()
            
        elif media_state == obs.OBS_MEDIA_STATE_ENDED:
            handle_ended_state()
            
        elif media_state == obs.OBS_MEDIA_STATE_STOPPED:
            handle_stopped_state()
            
        elif media_state == obs.OBS_MEDIA_STATE_NONE:
            handle_none_state()
            
    except Exception as e:
        log(f"ERROR in playback controller: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")


def start_specific_video(video_id):
    """
    Start playing a specific video by ID.
    Used for loop mode to replay the same video.
    """
    log(f"start_specific_video called for ID: {video_id}")
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Reset retry count on successful transition
    reset_playback_tracking()
    
    # Get video info
    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return
    
    # Validate video file exists
    if not validate_video_file(video_id):
        return
    
    # Update media source with force reload for loop mode
    if update_media_source(video_info['path'], force_reload=True):
        # Schedule title display
        schedule_title_show(video_info)
        
        # Update playback state
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        # Get display info
        display_info = get_video_display_info(video_id)
        log(f"Started playback (loop): {display_info['song']} - {display_info['artist']}")
        
        # Schedule title clear with a delay to ensure accurate duration
        schedule_title_clear_with_delay()
    else:
        # Failed to update media source
        log("Failed to start video")
        set_playing(False)


def start_next_video():
    """
    Start playing the next video.
    Must be called from main thread.
    """
    log("start_next_video called")
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Reset retry count on successful transition
    reset_playback_tracking()
    
    # Check playback mode
    playback_mode = get_playback_mode()
    
    # If in single mode and first video has been played
    if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
        log("Single mode: Already played first video, stopping")
        stop_current_playback()
        return
    
    # Select next video
    video_id = select_next_video()
    if not video_id:
        set_playing(False)
        return
    
    # Get video info
    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return
    
    # Validate video file exists
    if not validate_video_file(video_id):
        # Try another video
        start_next_video()
        return
    
    # Get display info
    display_info = get_video_display_info(video_id)
    
    # Update media source first
    if update_media_source(video_info['path']):
        # Schedule title display (will clear immediately and show after delay)
        schedule_title_show(video_info)
        
        # Update playback state
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        # Mark first video as played for single/loop modes
        if not is_first_video_played():
            set_first_video_played(True)
            if playback_mode == PLAYBACK_MODE_SINGLE:
                log(f"Single mode - Started first and only playback: {display_info['song']} - {display_info['artist']}")
            elif playback_mode == PLAYBACK_MODE_LOOP:
                log(f"Loop mode - Started first playback: {display_info['song']} - {display_info['artist']}")
            else:
                log(f"Started playback: {display_info['song']} - {display_info['artist']}")
        else:
            log(f"Started playback: {display_info['song']} - {display_info['artist']}")
        
        # Schedule title clear with a delay to ensure accurate duration
        schedule_title_clear_with_delay()
    else:
        # Failed to update media source, try another video
        log("Failed to start video, trying another...")
        from ytfast_modules.state_handlers import _playback_retry_count, _max_retry_attempts
        if _playback_retry_count < _max_retry_attempts:
            _playback_retry_count += 1
            start_next_video()
        else:
            log("Max retries reached, stopping")
            set_playing(False)


def stop_current_playback():
    """
    Enhanced stop with complete cleanup.
    Must be called from main thread.
    """
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Clear loop restart state
    clear_loop_restart_state()
    
    # Mark that we initiated this stop
    set_manual_stop_detected(True)
    
    if not is_playing():
        log("No active playback to stop")
        return
    
    try:
        # Clear media source completely
        stop_media_source()
        
        # Fade out text before clearing
        if get_current_opacity() > 0:
            fade_out_text()
        
        # Clear text source content
        update_text_source_content("", "", False)
        
        # Update state
        set_playing(False)
        set_current_video_path(None)
        set_current_playback_video_id(None)
        
        # Clear tracking
        reset_playback_tracking()
        
        log("Playback stopped and all sources cleared")
        
    except Exception as e:
        log(f"ERROR stopping playback: {e}")


def start_playback_controller():
    """Start the playback controller timer."""
    global _playback_timer, _initial_state_checked
    
    try:
        # Reset initial state check
        _initial_state_checked = False
        
        # Remove existing timer if any
        if _playback_timer:
            obs.timer_remove(_playback_timer)
        
        # Add new timer
        _playback_timer = playback_controller
        obs.timer_add(_playback_timer, PLAYBACK_CHECK_INTERVAL)
        log("Playback controller started")
        
    except Exception as e:
        log(f"ERROR starting playback controller: {e}")


def stop_playback_controller():
    """Stop the playback controller timer."""
    global _playback_timer
    
    try:
        # Cancel any pending title timers
        cancel_title_timers()
        
        # Cancel other timers
        cancel_opacity_timer()
        cancel_loop_restart_timer()
        from ytfast_modules.media_control import cancel_media_reload_timer
        cancel_media_reload_timer()
        
        if _playback_timer:
            obs.timer_remove(_playback_timer)
            _playback_timer = None
            log("Playback controller stopped")
            
    except Exception as e:
        log(f"ERROR stopping playback controller: {e}")
