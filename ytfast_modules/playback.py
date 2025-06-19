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
    SCENE_NAME
)
from logger import log
from state import (
    is_playing, set_playing,
    get_current_video_path, set_current_video_path,
    get_current_playback_video_id, set_current_playback_video_id,
    get_cached_videos, get_cached_video_info,
    get_played_videos, add_played_video, clear_played_videos,
    is_scene_active
)

# Module-level variables
_playback_timer = None
_last_progress_log = {}
_playback_retry_count = 0
_max_retry_attempts = 3
_waiting_for_videos_logged = False
_last_cached_count = 0
_first_run = True
_sources_verified = False

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
        log("==========================")
        _sources_verified = True
    
    return scene_exists and media_exists and text_exists

def playback_controller():
    """
    Main playback controller - runs on main thread via timer.
    Manages video playback state and transitions.
    """
    global _waiting_for_videos_logged, _last_cached_count, _first_run
    
    try:
        # Verify sources exist
        if not verify_sources():
            return
        
        # Check if scene is active
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
    duration = get_media_duration(MEDIA_SOURCE_NAME)
    current_time = get_media_time(MEDIA_SOURCE_NAME)
    
    if duration > 0 and current_time > 0:
        # Log progress without spamming
        video_id = get_current_playback_video_id()
        if video_id:
            log_playback_progress(video_id, current_time, duration)
        
        # Check if video is near end (95% complete)
        if is_video_near_end(duration, current_time, 95):
            log("Video near end, preparing next...")
            start_next_video()

def handle_ended_state():
    """Handle video ended state."""
    if is_playing():
        log("Playback ended, starting next video")
        start_next_video()

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
        log("WARNING: Playing state but no media loaded")
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
            log(f"Playing: {video_info['artist']} - {video_info['song']} "
                f"[{percent}% - {int(current_time/1000)}s / {int(duration/1000)}s]")

def select_next_video():
    """
    Select next video for playback using random no-repeat logic.
    Returns video_id or None if no videos available.
    """
    cached_videos = get_cached_videos()
    
    if not cached_videos:
        log("No videos available for playback")
        return None
    
    available_videos = list(cached_videos.keys())
    played_videos = get_played_videos()
    
    # If we only have one video, always play it
    if len(available_videos) == 1:
        selected = available_videos[0]
        # Don't add to played list if it's the only video
        video_info = cached_videos[selected]
        log(f"Selected (only video): {video_info['artist']} - {video_info['song']}")
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
    log(f"Selected: {video_info['artist']} - {video_info['song']}")
    
    return selected

def update_media_source(video_path):
    """
    Update OBS Media Source with new video.
    Must be called from main thread.
    """
    try:
        # Validate file exists
        if not os.path.exists(video_path):
            log(f"ERROR: Video file not found: {video_path}")
            return False
        
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", video_path)
            obs.obs_data_set_bool(settings, "restart_on_activate", True)
            obs.obs_data_set_bool(settings, "close_when_inactive", True)
            obs.obs_data_set_bool(settings, "hw_decode", True)
            
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

def update_text_source(artist, song):
    """
    Update OBS Text Source with metadata.
    Must be called from main thread.
    """
    try:
        source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        if source:
            text = f"{artist} - {song}" if artist and song else ""
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
            
            if text:
                log(f"Updated text source: {text}")
            return True
        else:
            log(f"WARNING: Text source '{TEXT_SOURCE_NAME}' not found")
            return False
            
    except Exception as e:
        log(f"ERROR updating text source: {e}")
        return False

def start_next_video():
    """
    Start playing the next video.
    Must be called from main thread.
    """
    global _playback_retry_count, _last_progress_log
    
    log("start_next_video called")
    
    # Reset retry count on successful transition
    _playback_retry_count = 0
    
    # Clear progress log for new video
    _last_progress_log.clear()
    
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
    
    # Update sources
    if update_media_source(video_info['path']):
        update_text_source(video_info['artist'], video_info['song'])
        
        # Update playback state
        set_playing(True)
        set_current_video_path(video_info['path'])
        set_current_playback_video_id(video_id)
        
        log(f"Started playback: {video_info['artist']} - {video_info['song']}")
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
    Stop current playback and clear sources.
    Must be called from main thread.
    """
    global _last_progress_log
    
    try:
        # Stop media source
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            obs.obs_source_media_stop(source)
            obs.obs_source_release(source)
        
        # Clear text
        update_text_source("", "")
        
        # Update state
        set_playing(False)
        set_current_video_path(None)
        set_current_playback_video_id(None)
        
        # Clear progress tracking
        _last_progress_log.clear()
        
        log("Playback stopped")
        
    except Exception as e:
        log(f"ERROR stopping playback: {e}")

def start_playback_controller():
    """Start the playback controller timer."""
    global _playback_timer
    
    try:
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
        if _playback_timer:
            obs.timer_remove(_playback_timer)
            _playback_timer = None
            log("Playback controller stopped")
            
    except Exception as e:
        log(f"ERROR stopping playback controller: {e}")
