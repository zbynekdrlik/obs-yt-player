"""
Playback state handlers.
Handles different media states: playing, ended, stopped, none.
"""

import obspython as obs

from .config import MEDIA_SOURCE_NAME, PLAYBACK_MODE_LOOP, PLAYBACK_MODE_SINGLE
from .logger import log
from .media_control import get_current_video_from_media_source, get_media_duration, get_media_time
from .state import (
    get_cached_video_info,
    get_cached_videos,
    get_current_playback_video_id,
    get_loop_video_id,
    get_playback_mode,
    is_first_video_played,
    is_playing,
    is_scene_active,
    set_current_playback_video_id,
    set_first_video_played,
    set_loop_video_id,
    set_playing,
)
from .title_manager import (
    SEEK_THRESHOLD,
    is_title_clear_scheduled,
    schedule_title_clear_from_current,
)
from .utils import format_duration

# Module-level variables
_last_playback_time = 0  # Track last playback position for seek detection
_loop_restart_timer = None  # Timer reference for loop restart
_loop_restart_pending = False  # Track if we're waiting to restart loop
_loop_restart_video_id = None  # Track which video we're restarting
_manual_stop_detected = False  # Track if user manually stopped playback
_last_progress_log = {}
_playback_retry_count = 0
_max_retry_attempts = 3
_preloaded_video_handled = False  # Track if we've handled pre-loaded video
_is_preloaded_video = False  # Track if current video is pre-loaded
_title_clear_rescheduled = False  # Track if we've rescheduled after seek


def reset_playback_tracking():
    """Reset playback tracking variables."""
    global _last_playback_time, _last_progress_log, _playback_retry_count, _title_clear_rescheduled
    _last_playback_time = 0
    _last_progress_log.clear()
    _playback_retry_count = 0
    _title_clear_rescheduled = False


def log_playback_progress(video_id, current_time, duration):
    """Log playback progress at intervals without spamming."""
    global _last_progress_log

    # Log every 30 seconds
    progress_key = f"{video_id}_{int(current_time / 30000)}"
    if progress_key not in _last_progress_log:
        _last_progress_log[progress_key] = True
        percent = int((current_time / duration) * 100)

        # Get video info for better logging
        video_info = get_cached_video_info(video_id)
        if video_info:
            # Convert milliseconds to seconds and format
            current_time_formatted = format_duration(current_time / 1000)
            duration_formatted = format_duration(duration / 1000)

            log(
                f"Playing: {video_info['song']} - {video_info['artist']} "
                f"[{percent}% - {current_time_formatted} / {duration_formatted}]"
            )


def handle_playing_state():
    """Handle currently playing video state."""
    global _is_preloaded_video, _last_playback_time, _manual_stop_detected
    global _loop_restart_pending, _loop_restart_video_id, _title_clear_rescheduled

    # Clear manual stop flag when playing
    _manual_stop_detected = False

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
            # Import here to avoid circular dependency
            from .playback_controller import start_next_video

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
                log(f"Seek detected: jumped from {_last_playback_time / 1000:.1f}s to {current_time / 1000:.1f}s")
                # Reset the rescheduled flag to allow rescheduling
                _title_clear_rescheduled = False

        _last_playback_time = current_time

        # Log progress without spamming
        video_id = get_current_playback_video_id()
        if video_id:
            log_playback_progress(video_id, current_time, duration)

        # Check if we need to schedule or reschedule title clear
        remaining_ms = duration - current_time

        # Import here to avoid circular dependency
        from .title_manager import TITLE_CLEAR_BEFORE_END

        # Schedule fade out when we're close to the end
        # We check for (TITLE_CLEAR_BEFORE_END + 5) seconds to give enough time for scheduling
        if remaining_ms > 0 and remaining_ms < ((TITLE_CLEAR_BEFORE_END + 5) * 1000):
            # Only reschedule if we haven't already done so after a seek
            # or if no timer is currently scheduled
            if not _title_clear_rescheduled or not is_title_clear_scheduled():
                # Schedule the fade out based on current remaining time
                schedule_title_clear_from_current(remaining_ms)
                _title_clear_rescheduled = True
                log(f"Title fade rescheduled for remaining time: {remaining_ms / 1000:.1f}s")


def handle_ended_state():
    """Handle video ended state."""
    global _preloaded_video_handled, _is_preloaded_video, _loop_restart_pending

    # Reset playback tracking
    reset_playback_tracking()

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
                # Import here to avoid circular dependency
                from .playback_controller import stop_current_playback

                stop_current_playback()
                return
            else:
                log("Starting playlist after pre-loaded video")
        else:
            # Regular video ended (not pre-loaded)
            # Check playback mode to determine what to do next
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                log("Single mode: First video ended, stopping playback")
                # Import here to avoid circular dependency
                from .playback_controller import stop_current_playback

                stop_current_playback()
                return
            else:
                # Continuous mode or first video not played yet
                log("Playback ended, starting next video")

        # Import here to avoid circular dependency
        from .playback_controller import start_next_video

        start_next_video()
    elif is_scene_active() and get_cached_videos():
        # Check if we're in single mode and already played first video
        if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
            # Don't start new playback in single mode after first video
            return
        # Not playing but scene is active and we have videos - start playback
        log("Scene active and videos available, starting playback")
        # Import here to avoid circular dependency
        from .playback_controller import start_next_video

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
        # Import here to avoid circular dependency
        from .playback_controller import start_specific_video

        start_specific_video(video_id)

    # Schedule the restart with a longer delay to ensure media source is ready
    _loop_restart_timer = restart_callback
    obs.timer_add(_loop_restart_timer, 1000)  # Increased to 1 second for better stability


def handle_stopped_state():
    """Handle video stopped state."""
    global _manual_stop_detected, _playback_retry_count

    if is_playing():
        # Check if this was a manual stop (we didn't initiate it)
        if not _manual_stop_detected:
            _manual_stop_detected = True
            log("Manual stop detected - user clicked stop button")

            # Clear loop video if in loop mode
            if get_playback_mode() == PLAYBACK_MODE_LOOP:
                log("Clearing loop video due to manual stop")
                set_loop_video_id(None)

            # Stop playback cleanly
            # Import here to avoid circular dependency
            from .playback_controller import stop_current_playback

            stop_current_playback()
            return

        log("Playback stopped, attempting to resume or skip")
        # Try to resume or skip to next
        if _playback_retry_count < _max_retry_attempts:
            _playback_retry_count += 1
            log(f"Retry attempt {_playback_retry_count}")
            # Import here to avoid circular dependency
            from .playback_controller import start_next_video

            start_next_video()
        else:
            log("Max retries reached, stopping playback")
            # Import here to avoid circular dependency
            from .playback_controller import stop_current_playback

            stop_current_playback()


def handle_none_state():
    """Handle no media loaded state."""
    if is_scene_active() and not is_playing():
        # Only start if we have videos available
        if get_cached_videos():
            playback_mode = get_playback_mode()

            # Check restrictions based on mode
            if playback_mode == PLAYBACK_MODE_SINGLE and is_first_video_played():
                # Don't start new playback in single mode after first video
                return
            elif playback_mode == PLAYBACK_MODE_LOOP:
                # In loop mode, clear the loop video when scene becomes active
                # This ensures a new random video is selected
                if get_loop_video_id():
                    log("Loop mode: Clearing previous loop video to select new random video")
                    set_loop_video_id(None)

            log("Scene active and videos available, starting playback")
            # Import here to avoid circular dependency
            from .playback_controller import start_next_video

            start_next_video()
    elif is_scene_active() and is_playing():
        # This shouldn't happen - playing but no media?
        log("WARNING: Playing state but no media loaded - resetting state")
        set_playing(False)


def cancel_loop_restart_timer():
    """Cancel any pending loop restart timer."""
    global _loop_restart_timer
    if _loop_restart_timer:
        obs.timer_remove(_loop_restart_timer)
        _loop_restart_timer = None


def set_preloaded_video_state(handled, is_preloaded):
    """Set pre-loaded video state."""
    global _preloaded_video_handled, _is_preloaded_video
    _preloaded_video_handled = handled
    _is_preloaded_video = is_preloaded


def set_manual_stop_detected(detected):
    """Set manual stop detected flag."""
    global _manual_stop_detected
    _manual_stop_detected = detected


def clear_loop_restart_state():
    """Clear loop restart state."""
    global _loop_restart_pending, _loop_restart_video_id
    _loop_restart_pending = False
    _loop_restart_video_id = None
