"""Playback control module for OBS YouTube Player.
Manages video playback through OBS Media Source.
"""

import obspython as obs
import threading
import time
import os
import random

# Use absolute imports to fix module loading issue
from ytplay_modules.logger import log
from ytplay_modules.config import (
    MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME,
    PLAYBACK_CHECK_INTERVAL, TITLE_SHOW_DELAY, TITLE_CLEAR_BEFORE_END,
    PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP
)
from ytplay_modules.state import (
    should_stop_threads, is_playing, set_playing,
    set_thread_script_context, register_thread, unregister_thread,
    get_script_name, set_current_file_path, set_current_playback_video_id,
    get_playback_mode, is_first_video_played, set_first_video_played,
    get_loop_video_id, set_loop_video_id, get_current_playback_video_id,
    set_last_played_video, get_last_played_video,
    get_cached_videos, get_cached_video_info,
    is_scene_active, set_scene_active
)

# Playback controller reference
_playback_timer = None

# Module state
_waiting_for_videos_logged = False
_last_cached_count = 0
_sources_verified = False
_initial_state_checked = False

# Title display timers
_title_show_timer = None
_title_clear_timer = None

# Opacity animation
_opacity_timer = None
_current_opacity = 0.0
_target_opacity = 0.0
_opacity_step = 0.05


def check_scene_active():
    """Check if the script's scene is currently active."""
    script_name = get_script_name()
    current_scene = obs.obs_frontend_get_current_scene()
    
    if not current_scene:
        return False
    
    scene_name = obs.obs_source_get_name(current_scene)
    obs.obs_source_release(current_scene)
    
    is_active = scene_name == script_name
    set_scene_active(is_active)
    return is_active


def start_playback_controller():
    """Start the playback controller."""
    global _playback_timer, _initial_state_checked
    
    # Reset initial state check
    _initial_state_checked = False
    
    # Remove existing timer if any
    if _playback_timer:
        obs.timer_remove(_playback_timer)
    
    # Add new timer
    _playback_timer = playback_check_timer
    obs.timer_add(_playback_timer, PLAYBACK_CHECK_INTERVAL)
    log("Playback controller started")


def stop_playback_controller():
    """Stop the playback controller."""
    global _playback_timer
    
    # Cancel all timers
    cancel_title_timers()
    cancel_opacity_timer()
    
    if _playback_timer:
        obs.timer_remove(_playback_timer)
        _playback_timer = None
        log("Playback controller stopped")


def playback_check_timer():
    """Timer callback to check playback status."""
    global _waiting_for_videos_logged, _last_cached_count, _initial_state_checked
    
    try:
        # Check if we're shutting down
        if should_stop_threads():
            if is_playing():
                stop_playback()
            return
        
        # Verify sources exist
        if not verify_sources():
            return
        
        # Ensure opacity filter exists
        ensure_opacity_filter()
        
        # Check if scene is active
        if not check_scene_active():
            if is_playing():
                playback_mode = get_playback_mode()
                log(f"Scene inactive in {playback_mode} mode, stopping playback")
                if playback_mode == PLAYBACK_MODE_LOOP:
                    set_loop_video_id(None)
                    set_first_video_played(False)
                stop_playback()
            _waiting_for_videos_logged = False
            return
        
        # Check if we have videos to play
        cached_videos = get_cached_videos()
        current_count = len(cached_videos)
        
        # Track changes in video count
        if current_count != _last_cached_count:
            if _last_cached_count == 0 and current_count > 0:
                log(f"First video available! Starting playback with {current_count} video(s)")
            elif current_count > _last_cached_count:
                log(f"New video added to cache. Total videos: {current_count}")
            _last_cached_count = current_count
            _waiting_for_videos_logged = False
        
        if not cached_videos:
            if not _waiting_for_videos_logged:
                log("Waiting for videos to be downloaded and processed...")
                _waiting_for_videos_logged = True
            return
        
        # Reset waiting flag since we have videos
        _waiting_for_videos_logged = False
        
        # Get current media state
        media_state = get_media_state()
        
        # Handle initial state check
        if not _initial_state_checked:
            _initial_state_checked = True
            force_disable_media_loop()
            
            if media_state == obs.OBS_MEDIA_STATE_PLAYING and not is_playing():
                duration = get_media_duration()
                if duration <= 0:
                    log("No valid media in source, starting fresh playback")
                    start_next_video()
                    return
                
                log("Media source is already playing - syncing state")
                set_playing(True)
                
                # Try to identify the current video
                current_video_id = get_current_video_from_media_source()
                if current_video_id:
                    set_current_playback_video_id(current_video_id)
                    log(f"Identified pre-loaded video: {current_video_id}")
                    
                    if get_playback_mode() == PLAYBACK_MODE_LOOP and not get_loop_video_id():
                        set_loop_video_id(current_video_id)
                        log(f"Loop mode - Set pre-loaded video as loop video")
                return
        
        # Start playback if scene is active but not playing
        if is_scene_active() and not is_playing() and cached_videos:
            playback_mode = get_playback_mode()
            
            # Check mode restrictions
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                pass  # Don't start new playback in single mode
            else:
                if media_state in [obs.OBS_MEDIA_STATE_NONE, obs.OBS_MEDIA_STATE_STOPPED, obs.OBS_MEDIA_STATE_ENDED]:
                    log(f"Scene active but not playing, starting playback")
                    
                    if playback_mode == PLAYBACK_MODE_LOOP and get_loop_video_id():
                        log("Loop mode: Clearing previous loop video to select new random video")
                        set_loop_video_id(None)
                    
                    start_next_video()
                    return
        
        # Handle different media states
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


def verify_sources():
    """Verify that required sources exist."""
    global _sources_verified
    
    # Get dynamic scene name from script name
    scene_name = get_script_name()
    
    # Check scene
    scene_source = obs.obs_get_source_by_name(scene_name)
    scene_exists = scene_source is not None
    if scene_source:
        obs.obs_source_release(scene_source)
    
    # Check media source
    media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    media_exists = media_source is not None
    if media_source:
        obs.obs_source_release(media_source)
    
    # Check text source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    text_exists = text_source is not None
    if text_source:
        obs.obs_source_release(text_source)
    
    # Log verification results
    if not _sources_verified or not (scene_exists and media_exists and text_exists):
        log("=== SOURCE VERIFICATION ===")
        log(f"Scene '{scene_name}': {'✓ EXISTS' if scene_exists else '✗ MISSING'}")
        log(f"Media Source '{MEDIA_SOURCE_NAME}': {'✓ EXISTS' if media_exists else '✗ MISSING'}")
        log(f"Text Source '{TEXT_SOURCE_NAME}': {'✓ EXISTS' if text_exists else '✗ MISSING'}")
        log("==========================")
        _sources_verified = True
    
    return scene_exists and media_exists and text_exists


def get_media_state():
    """Get current media source state."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        return obs.OBS_MEDIA_STATE_NONE
    
    state = obs.obs_source_media_get_state(source)
    obs.obs_source_release(source)
    return state


def get_media_duration():
    """Get media source duration in milliseconds."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        return 0
    
    duration = obs.obs_source_media_get_duration(source)
    obs.obs_source_release(source)
    return duration


def get_media_time():
    """Get current media playback time in milliseconds."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        return 0
    
    time_ms = obs.obs_source_media_get_time(source)
    obs.obs_source_release(source)
    return time_ms


def get_current_video_from_media_source():
    """Get current video ID from media source settings."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        return None
    
    settings = obs.obs_source_get_settings(source)
    current_file = obs.obs_data_get_string(settings, "local_file")
    obs.obs_data_release(settings)
    obs.obs_source_release(source)
    
    if not current_file:
        return None
    
    # Extract video ID from filename
    filename = os.path.basename(current_file)
    if filename.endswith('.mp4'):
        return filename[:-4]  # Remove .mp4 extension
    
    return None


def force_disable_media_loop():
    """Force disable the loop setting on media source."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        return
    
    settings = obs.obs_source_get_settings(source)
    is_looping = obs.obs_data_get_bool(settings, "looping")
    
    if is_looping:
        obs.obs_data_set_bool(settings, "looping", False)
        obs.obs_source_update(source, settings)
        log("Disabled OBS loop checkbox on media source")
    
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


def update_media_source(file_path, force_reload=False):
    """Update media source with new file."""
    source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
    if not source:
        log(f"ERROR: Media source '{MEDIA_SOURCE_NAME}' not found")
        return False
    
    try:
        settings = obs.obs_source_get_settings(source)
        current_file = obs.obs_data_get_string(settings, "local_file")
        
        # Update if different file or force reload
        if current_file != file_path or force_reload:
            obs.obs_data_set_string(settings, "local_file", file_path)
            obs.obs_data_set_bool(settings, "looping", False)
            obs.obs_source_update(source, settings)
            log(f"Updated media source: {os.path.basename(file_path)}")
        
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        return True
        
    except Exception as e:
        log(f"ERROR updating media source: {e}")
        obs.obs_source_release(source)
        return False


def ensure_opacity_filter():
    """Ensure opacity filter exists on text source."""
    source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not source:
        return
    
    # Check if color correction filter exists
    filter_source = obs.obs_source_get_filter_by_name(source, "Opacity")
    
    if not filter_source:
        # Create opacity filter
        filter_settings = obs.obs_data_create()
        obs.obs_data_set_double(filter_settings, "opacity", 0.0)
        
        filter_source = obs.obs_source_create("color_filter", "Opacity", filter_settings, None)
        obs.obs_source_filter_add(source, filter_source)
        
        obs.obs_data_release(filter_settings)
        log("Created opacity filter on text source")
    
    obs.obs_source_release(filter_source)
    obs.obs_source_release(source)


def update_text_opacity(opacity):
    """Update text source opacity."""
    source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not source:
        return
    
    filter_source = obs.obs_source_get_filter_by_name(source, "Opacity")
    if filter_source:
        settings = obs.obs_data_create()
        obs.obs_data_set_double(settings, "opacity", opacity)
        obs.obs_source_update(filter_source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(filter_source)
    
    obs.obs_source_release(source)


def opacity_animation_timer():
    """Timer callback for opacity animation."""
    global _current_opacity, _target_opacity, _opacity_timer
    
    if abs(_current_opacity - _target_opacity) < 0.01:
        _current_opacity = _target_opacity
        update_text_opacity(_current_opacity)
        
        # Stop timer when target reached
        if _opacity_timer:
            obs.timer_remove(_opacity_timer)
            _opacity_timer = None
        return
    
    # Move towards target
    if _current_opacity < _target_opacity:
        _current_opacity = min(_current_opacity + _opacity_step, _target_opacity)
    else:
        _current_opacity = max(_current_opacity - _opacity_step, _target_opacity)
    
    update_text_opacity(_current_opacity)


def fade_in_text():
    """Fade in text opacity."""
    global _target_opacity, _opacity_timer
    
    _target_opacity = 1.0
    
    if not _opacity_timer:
        _opacity_timer = opacity_animation_timer
        obs.timer_add(_opacity_timer, 50)  # 20 FPS animation


def fade_out_text():
    """Fade out text opacity."""
    global _target_opacity, _opacity_timer
    
    _target_opacity = 0.0
    
    if not _opacity_timer:
        _opacity_timer = opacity_animation_timer
        obs.timer_add(_opacity_timer, 50)  # 20 FPS animation


def cancel_opacity_timer():
    """Cancel opacity animation timer."""
    global _opacity_timer
    
    if _opacity_timer:
        obs.timer_remove(_opacity_timer)
        _opacity_timer = None


def update_text_source(artist, song):
    """Update text source with formatted content."""
    source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not source:
        return
    
    # Format text
    text = f"{song} - {artist}" if song and artist else ""
    
    settings = obs.obs_source_get_settings(source)
    obs.obs_data_set_string(settings, "text", text)
    obs.obs_source_update(source, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


def title_show_timer():
    """Timer callback to show title."""
    global _title_show_timer
    
    # Get current video info
    video_id = get_current_playback_video_id()
    if not video_id:
        return
    
    video_info = get_cached_video_info(video_id)
    if not video_info:
        return
    
    # Update text and fade in
    update_text_source(video_info.get('artist', ''), video_info.get('song', ''))
    fade_in_text()
    
    # Clear timer reference
    _title_show_timer = None


def title_clear_timer():
    """Timer callback to clear title."""
    global _title_clear_timer
    
    # Fade out text
    fade_out_text()
    
    # Clear timer reference
    _title_clear_timer = None


def schedule_title_show(video_info):
    """Schedule title to show after delay."""
    global _title_show_timer
    
    # Cancel existing timer
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
    
    # Clear text immediately
    update_text_source("", "")
    
    # Schedule show
    _title_show_timer = title_show_timer
    obs.timer_add(_title_show_timer, TITLE_SHOW_DELAY * 1000)


def schedule_title_clear():
    """Schedule title to clear before video ends."""
    global _title_clear_timer
    
    # Cancel existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
    
    # Get duration
    duration = get_media_duration()
    if duration <= 0:
        return
    
    # Calculate when to clear (before end)
    clear_time = max(0, duration - (TITLE_CLEAR_BEFORE_END * 1000))
    
    if clear_time > 0:
        _title_clear_timer = title_clear_timer
        obs.timer_add(_title_clear_timer, int(clear_time))


def cancel_title_timers():
    """Cancel all title timers."""
    global _title_show_timer, _title_clear_timer
    
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None
    
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None


def select_next_video():
    """Select the next video to play."""
    cached_videos = get_cached_videos()
    if not cached_videos:
        return None
    
    playback_mode = get_playback_mode()
    
    # In loop mode, return the loop video if set
    if playback_mode == PLAYBACK_MODE_LOOP:
        loop_video_id = get_loop_video_id()
        if loop_video_id and loop_video_id in cached_videos:
            return loop_video_id
    
    # Get last played to avoid immediate repeat
    last_played = get_last_played_video()
    
    # If only one video, play it
    if len(cached_videos) == 1:
        return list(cached_videos)[0]
    
    # Filter out last played
    available_videos = [v for v in cached_videos if v != last_played]
    
    # If all videos were filtered, use all
    if not available_videos:
        available_videos = list(cached_videos)
    
    # Select random video
    return random.choice(available_videos)


def start_next_video():
    """Start playing the next video."""
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Check playback mode
    playback_mode = get_playback_mode()
    
    # If in single mode and first video has been played
    if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
        log("Single mode: Already played first video, stopping")
        stop_playback()
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
        log(f"ERROR: Video file not found: {video_info['path']}")
        # Try another video
        start_next_video()
        return
    
    # Update media source
    if update_media_source(video_info['path']):
        # Schedule title display
        schedule_title_show(video_info)
        
        # Update playback state
        set_playing(True)
        set_current_file_path(video_info['path'])
        set_current_playback_video_id(video_id)
        set_last_played_video(video_id)
        
        # Mark first video as played
        if not is_first_video_played():
            set_first_video_played(True)
            
            # Set loop video if in loop mode
            if playback_mode == PLAYBACK_MODE_LOOP:
                set_loop_video_id(video_id)
                log(f"Loop mode - Set first video as loop video: {video_id}")
        
        # Log playback start
        song = video_info.get('song', 'Unknown')
        artist = video_info.get('artist', 'Unknown')
        log(f"Started playback: {song} - {artist}")
        
        # Schedule title clear
        schedule_title_clear()
    else:
        log("Failed to start video")
        set_playing(False)


def start_specific_video(video_id):
    """Start playing a specific video (for loop mode)."""
    # Cancel any pending title timers
    cancel_title_timers()
    
    # Get video info
    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return
    
    # Validate video file exists
    if not os.path.exists(video_info['path']):
        log(f"ERROR: Video file not found: {video_info['path']}")
        return
    
    # Update media source with force reload
    if update_media_source(video_info['path'], force_reload=True):
        # Schedule title display
        schedule_title_show(video_info)
        
        # Update playback state
        set_playing(True)
        set_current_file_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        # Log playback start
        song = video_info.get('song', 'Unknown')
        artist = video_info.get('artist', 'Unknown')
        log(f"Started playback (loop): {song} - {artist}")
        
        # Schedule title clear
        schedule_title_clear()
    else:
        log("Failed to start video")
        set_playing(False)


def stop_playback():
    """Stop current playback."""
    # Cancel any pending title timers
    cancel_title_timers()
    
    if not is_playing():
        return
    
    try:
        # Clear media source
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            settings = obs.obs_source_get_settings(source)
            obs.obs_data_set_string(settings, "local_file", "")
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
        
        # Fade out and clear text
        fade_out_text()
        update_text_source("", "")
        
        # Update state
        set_playing(False)
        set_current_file_path(None)
        set_current_playback_video_id(None)
        
        log("Playback stopped")
        
    except Exception as e:
        log(f"ERROR stopping playback: {e}")


def handle_playing_state():
    """Handle media playing state."""
    # Check if near end for continuous mode
    if get_playback_mode() == PLAYBACK_MODE_CONTINUOUS:
        duration = get_media_duration()
        current_time = get_media_time()
        
        if duration > 0 and current_time > 0:
            remaining = duration - current_time
            # If less than 1 second remaining, prepare next video
            if remaining < 1000 and remaining > 0:
                log("Near end of video, preparing next...")


def handle_ended_state():
    """Handle media ended state."""
    log("Video ended")
    
    playback_mode = get_playback_mode()
    
    if playback_mode == PLAYBACK_MODE_SINGLE:
        log("Single mode - stopping after first video")
        stop_playback()
    elif playback_mode == PLAYBACK_MODE_LOOP:
        loop_video_id = get_loop_video_id()
        if loop_video_id:
            log(f"Loop mode - restarting video: {loop_video_id}")
            start_specific_video(loop_video_id)
        else:
            log("Loop mode - no video set, selecting new one")
            start_next_video()
    else:  # PLAYBACK_MODE_CONTINUOUS
        log("Continuous mode - starting next video")
        start_next_video()


def handle_stopped_state():
    """Handle media stopped state."""
    if is_playing():
        log("Media stopped unexpectedly")
        set_playing(False)


def handle_none_state():
    """Handle media none state."""
    # Scene is active but no media - start playback if we have videos
    if is_scene_active() and not is_playing():
        cached_videos = get_cached_videos()
        if cached_videos:
            playback_mode = get_playback_mode()
            
            # Check mode restrictions
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                return  # Don't start in single mode after first video
            
            log("Starting playback - no media loaded")
            start_next_video()