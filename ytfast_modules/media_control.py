"""
Media source control functions.
Handles OBS media source operations and text source updates.
"""

import obspython as obs
import os
from config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
from logger import log

# Timer for delayed media reload
_media_reload_timer = None


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
                from state import get_cached_video_info
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


def update_media_source(video_path, force_reload=False):
    """
    Update OBS Media Source with new video.
    Must be called from main thread.
    
    Args:
        video_path: Path to the video file
        force_reload: If True, clears the source first to force a reload
    """
    global _media_reload_timer
    
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
                        obs.obs_data_set_bool(settings, "restart_on_activate", False)
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
            obs.obs_data_set_bool(settings, "restart_on_activate", False)
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


def stop_media_source():
    """Stop and clear the media source."""
    try:
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if source:
            # Stop playback
            obs.obs_source_media_stop(source)
            
            # Clear the file path
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "local_file", "")
            obs.obs_data_set_bool(settings, "unload_when_not_showing", True)
            
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)
    except Exception as e:
        log(f"ERROR stopping media source: {e}")


def cancel_media_reload_timer():
    """Cancel any pending media reload timer."""
    global _media_reload_timer
    if _media_reload_timer:
        obs.timer_remove(_media_reload_timer)
        _media_reload_timer = None


def is_video_near_end(duration, current_time, threshold_percent=95):
    """Check if video is near end using percentage threshold."""
    if duration <= 0:
        return False
    percent_complete = (current_time / duration) * 100
    return percent_complete >= threshold_percent
