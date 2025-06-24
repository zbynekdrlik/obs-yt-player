"""
Playback control for OBS YouTube Player.
Implements random playback with auto-advance and scene management.
"""

import obspython as obs
import random
import os
from pathlib import Path

from config import (
    PLAYBACK_CHECK_INTERVAL, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME,
    SCENE_NAME, TITLE_FADE_DURATION, TITLE_FADE_STEPS, TITLE_FADE_INTERVAL,
    OPACITY_FILTER_NAME, PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP
)
from logger import log
from state import (
    is_playing, set_playing,
    get_current_video_path, set_current_video_path,
    get_current_playback_video_id, set_current_playback_video_id,
    get_cached_videos, get_cached_video_info,
    get_played_videos, add_played_video, clear_played_videos,
    is_scene_active, should_stop_threads,
    get_playback_mode, is_first_video_played, set_first_video_played,
    get_loop_video_id, set_loop_video_id
)
from utils import format_duration

# Module-level variables
_playback_timer = None
_last_progress_log = {}
_playback_retry_count = 0
_max_retry_attempts = 3
_waiting_for_videos_logged = False
_last_cached_count = 0
_first_run = True
_sources_verified = False
_initial_state_checked = False
_title_clear_timer = None
_title_show_timer = None
_pending_title_info = None
_title_clear_scheduled = False  # Track if title clear is already scheduled
_duration_check_timer = None  # Timer for delayed duration check
_preloaded_video_handled = False  # Track if we've handled pre-loaded video
_is_preloaded_video = False  # Track if current video is pre-loaded
_last_playback_time = 0  # Track last playback position for seek detection
_loop_restart_timer = None  # Timer reference for loop restart
_loop_restart_pending = False  # Track if we're waiting to restart loop
_loop_restart_video_id = None  # Track which video we're restarting
_media_reload_timer = None  # Timer for delayed media reload

# Opacity transition variables
_opacity_timer = None
_current_opacity = 100.0
_target_opacity = 100.0
_opacity_step = 0.0
_fade_direction = None  # 'in' or 'out'
_pending_text = None
_opacity_filter_created = False

# Title timing constants (in seconds)
TITLE_CLEAR_BEFORE_END = 3.5  # Clear title 3.5 seconds before song ends
TITLE_SHOW_AFTER_START = 1.5  # Show title 1.5 seconds after song starts
SEEK_THRESHOLD = 5000  # 5 seconds - consider it a seek if position jumps by more than this

def get_current_video_from_media_source():
    """
    Try to determine the current video ID from the media source file path.
    Returns video_id if found, None otherwise.
    """
    try:
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if not source:
            return None
        
        settings = obs.obs_source_get_settings(source)
        file_path = obs.obs_data_get_string(settings, "local_file")
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        
        if not file_path:
            return None
        
        # Extract video ID from filename
        # Expected format: <song>_<artist>_<id>_normalized.mp4
        filename = os.path.basename(file_path)
        if filename.endswith("_normalized.mp4"):
            parts = filename[:-15].rsplit('_', 1)  # Remove _normalized.mp4 and split from right
            if len(parts) >= 2:
                video_id = parts[-1]
                # Verify this video is in our cache
                if get_cached_video_info(video_id):
                    return video_id
        
        return None
        
    except Exception as e:
        log(f"ERROR getting current video from media source: {e}")
        return None

def force_disable_media_loop():
    """Force disable loop setting on media source."""
    try:
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            settings = obs.obs_source_get_settings(source)
            current_loop = obs.obs_data_get_bool(settings, "looping")
            
            if current_loop:
                log("Disabling OBS loop checkbox on media source")
                obs.obs_data_set_bool(settings, "looping", False)
                obs.obs_source_update(source, settings)
            
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
    except Exception as e:
        log(f"ERROR forcing disable media loop: {e}")

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

def ensure_opacity_filter():
    """Ensure the opacity filter exists on the text source."""
    global _opacity_filter_created
    
    if _opacity_filter_created:
        return True
    
    # Get the text source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not text_source:
        return False
    
    # Check if filter already exists
    existing_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
    if existing_filter:
        obs.obs_source_release(existing_filter)
        obs.obs_source_release(text_source)
        _opacity_filter_created = True
        return True
    
    # Create color correction filter for opacity control
    filter_settings = obs.obs_data_create()
    obs.obs_data_set_int(filter_settings, "opacity", 100)
    
    opacity_filter = obs.obs_source_create_private(
        "color_filter", 
        OPACITY_FILTER_NAME, 
        filter_settings
    )
    
    if opacity_filter:
        obs.obs_source_filter_add(text_source, opacity_filter)
        obs.obs_source_release(opacity_filter)
        _opacity_filter_created = True
        log(f"Created opacity filter for text source")
    
    obs.obs_data_release(filter_settings)
    obs.obs_source_release(text_source)
    
    return _opacity_filter_created

def update_text_opacity(opacity):
    """Update the opacity of the text source using color filter."""
    try:
        # Get the text source
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        if not text_source:
            return
        
        # Get the opacity filter
        opacity_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
        if not opacity_filter:
            obs.obs_source_release(text_source)
            # Try to create the filter
            if ensure_opacity_filter():
                # Try again
                opacity_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
                if not opacity_filter:
                    return
            else:
                return
        
        # Update the opacity value
        filter_settings = obs.obs_source_get_settings(opacity_filter)
        obs.obs_data_set_int(filter_settings, "opacity", int(opacity))
        obs.obs_source_update(opacity_filter, filter_settings)
        
        # Clean up
        obs.obs_data_release(filter_settings)
        obs.obs_source_release(opacity_filter)
        obs.obs_source_release(text_source)
        
    except Exception as e:
        log(f"ERROR updating text opacity: {e}")

def opacity_transition_callback():
    """Callback for opacity transition timer."""
    global _opacity_timer, _current_opacity, _target_opacity, _opacity_step, _fade_direction, _pending_text
    
    # Update current opacity
    _current_opacity += _opacity_step
    
    # Clamp opacity to valid range
    if _fade_direction == 'in':
        _current_opacity = min(_current_opacity, _target_opacity)
    else:
        _current_opacity = max(_current_opacity, _target_opacity)
    
    # Update the actual opacity
    update_text_opacity(_current_opacity)
    
    # Check if we've reached the target
    if abs(_current_opacity - _target_opacity) < 0.1:
        # Remove timer
        if _opacity_timer:
            obs.timer_remove(_opacity_timer)
            _opacity_timer = None
        
        _current_opacity = _target_opacity
        update_text_opacity(_current_opacity)
        
        # If fading out and reached 0, update the text
        if _fade_direction == 'out' and _current_opacity == 0 and _pending_text is not None:
            update_text_source_content(_pending_text['song'], _pending_text['artist'], _pending_text.get('gemini_failed', False))
            _pending_text = None
            # Now fade in
            fade_in_text()
        
        log(f"Title fade {_fade_direction} complete (opacity: {_current_opacity}%)")

def start_opacity_transition(target, direction):
    """Start an opacity transition."""
    global _opacity_timer, _target_opacity, _opacity_step, _fade_direction, _current_opacity
    
    # Cancel any existing transition
    if _opacity_timer:
        obs.timer_remove(_opacity_timer)
        _opacity_timer = None
    
    _target_opacity = target
    _fade_direction = direction
    
    # Calculate step size
    opacity_range = abs(_target_opacity - _current_opacity)
    if opacity_range > 0:
        _opacity_step = opacity_range / TITLE_FADE_STEPS
        if direction == 'out':
            _opacity_step = -_opacity_step
        
        # Start the timer
        _opacity_timer = opacity_transition_callback
        obs.timer_add(_opacity_timer, TITLE_FADE_INTERVAL)
        log(f"Starting title fade {direction} (current: {_current_opacity}% -> target: {_target_opacity}%)")

def fade_in_text():
    """Fade in the text source."""
    start_opacity_transition(100.0, 'in')

def fade_out_text():
    """Fade out the text source."""
    global _current_opacity
    # Don't start a new fade if we're already at 0 or fading out
    if _current_opacity <= 0 or (_fade_direction == 'out' and _opacity_timer is not None):
        return
    start_opacity_transition(0.0, 'out')

def clear_title_before_end_callback():
    """Callback to clear title before song ends."""
    global _title_clear_timer, _title_clear_scheduled
    # Remove the timer to prevent it from firing again
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
    _title_clear_scheduled = False
    log("Fading out title before song end")
    fade_out_text()

def show_title_after_start_callback():
    """Callback to show title after song starts."""
    global _title_show_timer, _pending_title_info
    # Remove the timer to prevent it from firing again
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None
    
    if _pending_title_info:
        song = _pending_title_info.get('song', 'Unknown Song')
        artist = _pending_title_info.get('artist', 'Unknown Artist')
        gemini_failed = _pending_title_info.get('gemini_failed', False)
        log(f"Showing title after delay: {song} - {artist}")
        update_text_source_content(song, artist, gemini_failed)
        fade_in_text()
        _pending_title_info = None

def cancel_title_timers():
    """Cancel any pending title timers."""
    global _title_clear_timer, _title_show_timer, _pending_title_info, _title_clear_scheduled
    global _opacity_timer, _duration_check_timer, _loop_restart_timer, _media_reload_timer
    
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
        
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None
    
    if _opacity_timer:
        obs.timer_remove(_opacity_timer)
        _opacity_timer = None
    
    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None
    
    if _loop_restart_timer:
        obs.timer_remove(_loop_restart_timer)
        _loop_restart_timer = None
    
    if _media_reload_timer:
        obs.timer_remove(_media_reload_timer)
        _media_reload_timer = None
        
    _pending_title_info = None
    _title_clear_scheduled = False

def schedule_title_clear(duration_ms):
    """Schedule clearing of title before song ends."""
    global _title_clear_timer, _title_clear_scheduled
    
    # Cancel any existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        
    # Calculate when to clear (duration - 3.5 seconds)
    clear_time_ms = duration_ms - (TITLE_CLEAR_BEFORE_END * 1000)
    
    if clear_time_ms > 0:
        # Schedule the clear
        _title_clear_timer = clear_title_before_end_callback
        obs.timer_add(_title_clear_timer, int(clear_time_ms))
        _title_clear_scheduled = True
        log(f"Scheduled title fade out in {clear_time_ms/1000:.1f} seconds")

def schedule_title_show(video_info):
    """Schedule showing of title after song starts."""
    global _title_show_timer, _pending_title_info, _current_opacity
    
    # Cancel any existing timer
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
    
    # Store the title info for later
    _pending_title_info = video_info
    
    # Set opacity to 0 immediately (no fade needed as it's a new video)
    _current_opacity = 0.0
    update_text_opacity(0.0)
    
    # Clear text immediately
    update_text_source_content("", "", False)
    
    # Schedule the show
    _title_show_timer = show_title_after_start_callback
    obs.timer_add(_title_show_timer, int(TITLE_SHOW_AFTER_START * 1000))
    log(f"Scheduled title show in {TITLE_SHOW_AFTER_START} seconds")

def playback_controller():
    """
    Main playback controller - runs on main thread via timer.
    Manages video playback state and transitions.
    """
    global _waiting_for_videos_logged, _last_cached_count, _first_run, _initial_state_checked
    global _preloaded_video_handled, _is_preloaded_video, _loop_restart_pending, _loop_restart_video_id
    
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
        if not is_scene_active():
            if is_playing():
                log("Scene inactive, stopping playback")
                stop_current_playback()
            # Reset waiting flag when scene is inactive
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
            log(f"DEBUG: Media state = {state_name}, is_playing = {is_playing()}, scene_active = {is_scene_active()}")
        
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
                _preloaded_video_handled = False
                _is_preloaded_video = True
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
                current_time = get_media_time(MEDIA_SOURCE_NAME)
                if duration > 0 and current_time > 0:
                    remaining_ms = duration - current_time
                    # If we're already close to the end, schedule fade out
                    if remaining_ms > 0 and remaining_ms < ((TITLE_CLEAR_BEFORE_END + 10) * 1000):
                        schedule_title_clear_from_current(remaining_ms)
                return  # Let it play out
        
        # Handle different states
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

def handle_playing_state():
    """Handle currently playing video state."""
    global _is_preloaded_video, _last_playback_time, _title_clear_scheduled, _title_clear_timer
    global _loop_restart_pending, _loop_restart_video_id
    
    # Check if we were waiting for a loop restart
    if _loop_restart_pending and _loop_restart_video_id:
        current_video_id = get_current_playback_video_id()
        if current_video_id == _loop_restart_video_id:
            # The loop video is now playing, clear the pending flag
            log("Loop restart completed successfully")
            _loop_restart_pending = False
            _loop_restart_video_id = None
    
    # If media is playing but we don't think we're playing, sync the state
    if not is_playing():
        log("Media playing but state out of sync - updating state")
        # Check if this is a valid video or just empty media source
        duration = get_media_duration(MEDIA_SOURCE_NAME)
        if duration <= 0:
            # No valid media loaded, start fresh
            log("No valid media loaded, starting playback")
            start_next_video()
            return
        # Valid media is playing, sync the state
        set_playing(True)
        
        # Try to identify the current video if not already set
        if not get_current_playback_video_id():
            current_video_id = get_current_video_from_media_source()
            if current_video_id:
                set_current_playback_video_id(current_video_id)
                log(f"Identified current video: {current_video_id}")
                
                # If we're in loop mode and no loop video set, set this one
                if get_playback_mode() == PLAYBACK_MODE_LOOP and not get_loop_video_id():
                    set_loop_video_id(current_video_id)
                    log(f"Loop mode - Set current video as loop video: {current_video_id}")
        
        return
    
    duration = get_media_duration(MEDIA_SOURCE_NAME)
    current_time = get_media_time(MEDIA_SOURCE_NAME)
    
    if duration > 0 and current_time > 0:
        # Check for seek (large jump in playback position)
        if _last_playback_time > 0:
            time_diff = current_time - _last_playback_time
            # If time jumped forward by more than threshold, it's likely a seek
            if time_diff > SEEK_THRESHOLD:
                log(f"Seek detected: jumped from {_last_playback_time/1000:.1f}s to {current_time/1000:.1f}s")
                # Cancel existing timer and allow rescheduling
                if _title_clear_timer:
                    obs.timer_remove(_title_clear_timer)
                    _title_clear_timer = None
                _title_clear_scheduled = False
        
        _last_playback_time = current_time
        
        # Log progress without spamming
        video_id = get_current_playback_video_id()
        if video_id:
            log_playback_progress(video_id, current_time, duration)
        
        # Check if we need to schedule or reschedule title clear
        remaining_ms = duration - current_time
        
        # Schedule fade out for both pre-loaded and regular videos when close to end
        if remaining_ms > 0 and remaining_ms < ((TITLE_CLEAR_BEFORE_END + 5) * 1000):
            if not _title_clear_scheduled or _title_clear_timer is None:
                # Schedule the fade out based on current remaining time
                schedule_title_clear_from_current(remaining_ms)

def schedule_title_clear_from_current(remaining_ms):
    """Schedule title clear based on remaining time."""
    global _title_clear_timer, _title_clear_scheduled
    
    # Cancel any existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
    
    # Calculate when to clear
    clear_in_ms = remaining_ms - (TITLE_CLEAR_BEFORE_END * 1000)
    
    if clear_in_ms > 0:
        _title_clear_timer = clear_title_before_end_callback
        obs.timer_add(_title_clear_timer, int(clear_in_ms))
        _title_clear_scheduled = True
        log(f"Scheduled title fade out in {clear_in_ms/1000:.1f} seconds (remaining: {remaining_ms/1000:.1f}s)")
    elif _current_opacity > 0:
        # Should fade out immediately
        log("Time to fade out has passed, fading immediately")
        _title_clear_scheduled = False  # Don't schedule, just do it
        fade_out_text()

def handle_ended_state():
    """Handle video ended state."""
    global _preloaded_video_handled, _is_preloaded_video, _last_playback_time, _loop_restart_pending
    
    # Reset playback tracking
    _last_playback_time = 0
    
    playback_mode = get_playback_mode()
    
    if is_playing():
        # Prevent loop mode from firing multiple times
        if playback_mode == PLAYBACK_MODE_LOOP and _loop_restart_pending:
            return  # Already scheduled a restart
        
        # Check if we need to loop
        if playback_mode == PLAYBACK_MODE_LOOP:
            # Get the video that just ended
            current_video_id = get_current_playback_video_id()
            if not current_video_id and _is_preloaded_video:
                # Try to identify the pre-loaded video
                current_video_id = get_current_video_from_media_source()
            
            if current_video_id:
                # Make sure it's set as the loop video
                if not get_loop_video_id():
                    set_loop_video_id(current_video_id)
                    log(f"Loop mode - Set ended video as loop video: {current_video_id}")
                
                log("Loop mode: Replaying the same video")
                _loop_restart_pending = True
                # Mark pre-loaded video as handled if it was one
                if _is_preloaded_video:
                    _preloaded_video_handled = True
                    _is_preloaded_video = False
                # Schedule restart with a single timer
                schedule_loop_restart(current_video_id)
                return
            else:
                log("Loop mode: Could not identify video to loop, selecting next")
        
        # Handle non-loop modes
        if not _preloaded_video_handled and _is_preloaded_video:
            log("Pre-loaded video ended")
            _preloaded_video_handled = True
            _is_preloaded_video = False
            
            # Check if we're in single mode
            if playback_mode == PLAYBACK_MODE_SINGLE:
                log("Single mode: Pre-loaded video counted as first video, stopping playback")
                # Mark that first video has been played
                set_first_video_played(True)
                stop_current_playback()
                return
            else:
                log("Starting playlist after pre-loaded video")
        else:
            # Regular video ended (not pre-loaded)
            # Check playback mode to determine what to do next
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                log("Single mode: First video ended, stopping playback")
                stop_current_playback()
                return
            else:
                # Continuous mode or first video not played yet
                log("Playback ended, starting next video")
        
        start_next_video()
    elif is_scene_active() and get_cached_videos():
        # Not playing but scene is active and we have videos - start playback
        log("Scene active and videos available, starting playback")
        start_next_video()

def schedule_loop_restart(video_id):
    """Schedule a single restart of the loop video."""
    global _loop_restart_timer, _loop_restart_video_id
    
    # Store the video ID we're restarting
    _loop_restart_video_id = video_id
    
    # Cancel any existing timer
    if _loop_restart_timer:
        obs.timer_remove(_loop_restart_timer)
        _loop_restart_timer = None
    
    # Create a closure that captures the video_id
    def restart_callback():
        global _loop_restart_timer
        # Remove the timer reference
        if _loop_restart_timer:
            obs.timer_remove(_loop_restart_timer)
            _loop_restart_timer = None
        # Don't clear _loop_restart_pending here - wait until video is actually playing
        start_specific_video(video_id)
    
    # Schedule the restart with a longer delay to ensure media source is ready
    _loop_restart_timer = restart_callback
    obs.timer_add(_loop_restart_timer, 1000)  # Increased to 1 second for better stability

def handle_stopped_state():
    """Handle video stopped state."""
    if is_playing():
        log("Playback stopped, attempting to resume or skip")
        # Try to resume or skip to next
        global _playback_retry_count
        if _playback_retry_count < _max_retry_attempts:
            _playback_retry_count += 1
            log(f"Retry attempt {_playback_retry_count}")
            start_next_video()
        else:
            log("Max retries reached, stopping playback")
            stop_current_playback()

def handle_none_state():
    """Handle no media loaded state."""
    if is_scene_active() and not is_playing():
        # Only start if we have videos available
        if get_cached_videos():
            log("Scene active and videos available, starting playback")
            start_next_video()
    elif is_scene_active() and is_playing():
        # This shouldn't happen - playing but no media?
        log("WARNING: Playing state but no media loaded - resetting state")
        set_playing(False)

def get_media_state(source_name):
    """
    Get current state of media source.
    Returns one of: OBS_MEDIA_STATE_NONE, OBS_MEDIA_STATE_PLAYING,
                    OBS_MEDIA_STATE_STOPPED, OBS_MEDIA_STATE_ENDED
    """
    source = obs.obs_get_source_by_name(source_name)
    if source:
        state = obs.obs_source_media_get_state(source)
        obs.obs_source_release(source)
        return state
    return obs.OBS_MEDIA_STATE_NONE

def get_media_duration(source_name):
    """Get duration of current media in milliseconds."""
    source = obs.obs_get_source_by_name(source_name)
    if source:
        duration = obs.obs_source_media_get_duration(source)
        obs.obs_source_release(source)
        return duration
    return 0

def get_media_time(source_name):
    """Get current playback time in milliseconds."""
    source = obs.obs_get_source_by_name(source_name)
    if source:
        time = obs.obs_source_media_get_time(source)
        obs.obs_source_release(source)
        return time
    return 0

def is_video_near_end(duration, current_time, threshold_percent=95):
    """Check if video is near end using percentage threshold."""
    if duration <= 0:
        return False
    percent_complete = (current_time / duration) * 100
    return percent_complete >= threshold_percent

def log_playback_progress(video_id, current_time, duration):
    """Log playback progress at intervals without spamming."""
    global _last_progress_log
    
    # Log every 30 seconds
    progress_key = f"{video_id}_{int(current_time/30000)}"
    if progress_key not in _last_progress_log:
        _last_progress_log[progress_key] = True
        percent = int((current_time/duration) * 100)
        
        # Get video info for better logging
        video_info = get_cached_video_info(video_id)
        if video_info:
            # Convert milliseconds to seconds and format
            current_time_formatted = format_duration(current_time / 1000)
            duration_formatted = format_duration(duration / 1000)
            
            log(f"Playing: {video_info['song']} - {video_info['artist']} "
                f"[{percent}% - {current_time_formatted} / {duration_formatted}]")

def select_next_video():
    """
    Select next video for playback using random no-repeat logic.
    Returns video_id or None if no videos available.
    """
    cached_videos = get_cached_videos()
    playback_mode = get_playback_mode()
    
    if not cached_videos:
        log("No videos available for playback")
        return None
    
    # In loop mode, return the loop video if set
    if playback_mode == PLAYBACK_MODE_LOOP:
        loop_video_id = get_loop_video_id()
        if loop_video_id and loop_video_id in cached_videos:
            video_info = cached_videos[loop_video_id]
            log(f"Loop mode - Selected: {video_info['song']} - {video_info['artist']}")
            return loop_video_id
        # If no loop video set, continue to select one and set it
    
    available_videos = list(cached_videos.keys())
    played_videos = get_played_videos()
    
    # If we only have one video, always play it
    if len(available_videos) == 1:
        selected = available_videos[0]
        # Don't add to played list if it's the only video
        video_info = cached_videos[selected]
        log(f"Selected (only video): {video_info['song']} - {video_info['artist']}")
        
        # Set as loop video if in loop mode
        if playback_mode == PLAYBACK_MODE_LOOP and not get_loop_video_id():
            set_loop_video_id(selected)
            log(f"Loop mode - Set loop video: {selected}")
        
        return selected
    
    # If all videos have been played, reset the played list
    if len(played_videos) >= len(available_videos):
        clear_played_videos()
        played_videos = []
        log("Reset played videos list")
    
    # Find unplayed videos
    unplayed = [vid for vid in available_videos if vid not in played_videos]
    
    if not unplayed:
        # This shouldn't happen due to reset above, but just in case
        clear_played_videos()
        unplayed = available_videos
    
    # Select random video from unplayed
    selected = random.choice(unplayed)
    add_played_video(selected)
    
    video_info = cached_videos[selected]
    log(f"Selected: {video_info['song']} - {video_info['artist']}")
    
    # Set as loop video if in loop mode and not set
    if playback_mode == PLAYBACK_MODE_LOOP and not get_loop_video_id():
        set_loop_video_id(selected)
        log(f"Loop mode - Set loop video: {selected}")
    
    return selected

def update_media_source(video_path, force_reload=False):
    """
    Update OBS Media Source with new video.
    Must be called from main thread.
    
    Args:
        video_path: Path to the video file
        force_reload: If True, clears the source first to force a reload
    """
    try:
        # Validate file exists
        if not os.path.exists(video_path):
            log(f"ERROR: Video file not found: {video_path}")
            return False
        
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            # Get current file path
            current_settings = obs.obs_source_get_settings(source)
            current_file = obs.obs_data_get_string(current_settings, "local_file")
            obs.obs_data_release(current_settings)
            
            # Check if we're trying to load the same file
            is_same_file = current_file == video_path
            
            # If it's the same file or force_reload is True, we need a multi-step reload
            if is_same_file or force_reload:
                log(f"{'Force reloading' if force_reload else 'Same file detected, performing multi-step reload:'} {os.path.basename(video_path)}")
                
                # Step 1: Stop the media completely
                obs.obs_source_media_stop(source)
                
                # Step 2: Clear the source
                clear_settings = obs.obs_data_create()
                obs.obs_data_set_string(clear_settings, "local_file", "")
                obs.obs_source_update(source, clear_settings)
                obs.obs_data_release(clear_settings)
                
                # Release the source to apply changes
                obs.obs_source_release(source)
                
                # Step 3: Schedule the reload after a delay
                global _media_reload_timer
                if _media_reload_timer:
                    obs.timer_remove(_media_reload_timer)
                    _media_reload_timer = None
                
                def reload_media():
                    global _media_reload_timer
                    if _media_reload_timer:
                        obs.timer_remove(_media_reload_timer)
                        _media_reload_timer = None
                    
                    reload_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
                    if reload_source:
                        settings = obs.obs_data_create()
                        obs.obs_data_set_string(settings, "local_file", video_path)
                        obs.obs_data_set_bool(settings, "restart_on_activate", True)
                        obs.obs_data_set_bool(settings, "close_when_inactive", True)
                        obs.obs_data_set_bool(settings, "hw_decode", True)
                        obs.obs_data_set_bool(settings, "looping", False)
                        
                        obs.obs_source_update(reload_source, settings)
                        obs.obs_data_release(settings)
                        
                        # Force restart the media
                        obs.obs_source_media_restart(reload_source)
                        obs.obs_source_release(reload_source)
                        
                        log(f"Media source reloaded: {os.path.basename(video_path)}")
                
                _media_reload_timer = reload_media
                obs.timer_add(_media_reload_timer, 500)  # Wait 500ms before reloading
                return True
            
            # Normal update (different file)
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", video_path)
            obs.obs_data_set_bool(settings, "restart_on_activate", True)
            obs.obs_data_set_bool(settings, "close_when_inactive", True)
            obs.obs_data_set_bool(settings, "hw_decode", True)
            
            # IMPORTANT: Disable OBS's built-in loop to prevent conflicts
            # with our script's playback behavior modes
            obs.obs_data_set_bool(settings, "looping", False)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
            
            log(f"Updated media source: {os.path.basename(video_path)}")
            return True
        else:
            log(f"ERROR: Media source '{MEDIA_SOURCE_NAME}' not found")
            return False
            
    except Exception as e:
        log(f"ERROR updating media source: {e}")
        return False

def update_text_source_content(song, artist, gemini_failed=False):
    """
    Update OBS Text Source content only (not opacity).
    Must be called from main thread.
    Format: Song - Artist
    If gemini_failed is True, adds a marker to indicate Gemini extraction failed.
    """
    try:
        source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        if source:
            # Never pass empty text, always have something
            if song and artist:
                text = f"{song} - {artist}"
            elif song:
                text = song
            elif artist:
                text = artist
            else:
                text = ""  # Allow empty when clearing
            
            # Add indicator if Gemini failed
            if text and gemini_failed:
                text += " ⚠"  # Warning symbol to indicate Gemini failure
                
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
            
            if text:
                log(f"Updated text content: {text}")
            return True
        else:
            log(f"WARNING: Text source '{TEXT_SOURCE_NAME}' not found")
            return False
            
    except Exception as e:
        log(f"ERROR updating text source: {e}")
        return False

def update_text_source(song, artist, gemini_failed=False):
    """
    Update text and trigger fade effect.
    This is called when we want to change the text with a transition.
    """
    global _pending_text
    
    # If opacity is not 0, fade out first then update
    if _current_opacity > 0:
        _pending_text = {'song': song, 'artist': artist, 'gemini_failed': gemini_failed}
        fade_out_text()
    else:
        # Already at 0, just update and fade in
        update_text_source_content(song, artist, gemini_failed)
        if song or artist:  # Only fade in if there's content
            fade_in_text()

def delayed_duration_check_callback():
    """Callback that runs once to check duration and schedule title clear."""
    global _duration_check_timer
    
    # Remove the timer reference so it doesn't get called again
    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None
    
    duration = get_media_duration(MEDIA_SOURCE_NAME)
    if duration > 0:
        schedule_title_clear(duration)
        log(f"Got duration after delay: {duration/1000:.1f}s")
    else:
        # Try again after another delay
        log("No duration yet, trying again...")
        _duration_check_timer = delayed_duration_check_callback
        obs.timer_add(_duration_check_timer, 500)

def schedule_title_clear_with_delay():
    """Schedule title clear after a short delay to ensure accurate duration."""
    global _duration_check_timer
    
    # Cancel any existing timer
    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None
    
    # Schedule the duration check after 200ms
    _duration_check_timer = delayed_duration_check_callback
    obs.timer_add(_duration_check_timer, 200)

def start_specific_video(video_id):
    """
    Start playing a specific video by ID.
    Used for loop mode to replay the same video.
    """
    global _playback_retry_count, _last_progress_log, _last_playback_time
    
    log(f"start_specific_video called for ID: {video_id}")
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Reset retry count on successful transition
    _playback_retry_count = 0
    
    # Clear progress log for new video
    _last_progress_log.clear()
    _last_playback_time = 0
    
    # Get video info
    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return
    
    # Validate video file exists
    if not os.path.exists(video_info['path']):
        log(f"ERROR: Video file missing: {video_info['path']}")
        return
    
    # Extract metadata with fallbacks
    song = video_info.get('song', 'Unknown Song')
    artist = video_info.get('artist', 'Unknown Artist')
    
    # Update media source with force reload for loop mode
    if update_media_source(video_info['path'], force_reload=True):
        # Schedule title display
        schedule_title_show(video_info)
        
        # Update playback state
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        log(f"Started playback (loop): {song} - {artist}")
        
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
    global _playback_retry_count, _last_progress_log, _last_playback_time
    
    log("start_next_video called")
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Reset retry count on successful transition
    _playback_retry_count = 0
    
    # Clear progress log for new video
    _last_progress_log.clear()
    _last_playback_time = 0
    
    # Check playback mode
    playback_mode = get_playback_mode()
    
    # If in single or loop mode and first video has been played
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
    if not os.path.exists(video_info['path']):
        log(f"ERROR: Video file missing: {video_info['path']}")
        # Try another video
        start_next_video()
        return
    
    # Extract metadata with fallbacks
    song = video_info.get('song', 'Unknown Song')
    artist = video_info.get('artist', 'Unknown Artist')
    
    # Log if metadata is missing
    if song == 'Unknown Song' or artist == 'Unknown Artist':
        log(f"WARNING: Missing metadata for video {video_id} - Song: '{song}', Artist: '{artist}'")
    
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
                log(f"Single mode - Started first and only playback: {song} - {artist}")
            elif playback_mode == PLAYBACK_MODE_LOOP:
                log(f"Loop mode - Started first playback: {song} - {artist}")
            else:
                log(f"Started playback: {song} - {artist}")
        else:
            log(f"Started playback: {song} - {artist}")
        
        # Schedule title clear with a delay to ensure accurate duration
        schedule_title_clear_with_delay()
    else:
        # Failed to update media source, try another video
        log("Failed to start video, trying another...")
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
    global _last_progress_log, _playback_retry_count, _current_opacity, _last_playback_time
    global _loop_restart_pending, _loop_restart_video_id
    
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Clear loop restart state
    _loop_restart_pending = False
    _loop_restart_video_id = None
    
    if not is_playing():
        log("No active playback to stop")
        return
    
    try:
        # Clear media source completely
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            # Stop playback
            obs.obs_source_media_stop(source)
            
            # Clear the file path - THIS IS IMPORTANT
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", "")
            obs.obs_data_set_bool(settings, "unload_when_not_showing", True)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
        
        # Fade out text before clearing
        if _current_opacity > 0:
            fade_out_text()
        
        # Clear text source content
        update_text_source_content("", "", False)
        
        # Update state
        set_playing(False)
        set_current_video_path(None)
        set_current_playback_video_id(None)
        
        # Clear tracking
        _last_progress_log.clear()
        _playback_retry_count = 0
        _last_playback_time = 0
        
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
        
        if _playback_timer:
            obs.timer_remove(_playback_timer)
            _playback_timer = None
            log("Playback controller stopped")
            
    except Exception as e:
        log(f"ERROR stopping playback controller: {e}")
