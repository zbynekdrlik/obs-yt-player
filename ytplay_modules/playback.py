"""
Playback control module for OBS YouTube Player.
Manages video playback through OBS Media Source.
"""

import obspython as obs
import threading
import time

from logger import log
from state import (
    should_stop_threads, is_playing, set_playing,
    set_thread_script_context, register_thread, unregister_thread
)

# Playback controller reference
_playback_timer = None

def playback_check_timer():
    """Timer callback to check playback status."""
    # TODO: Implement actual playback checking
    pass

def start_playback_controller():
    """Start the playback controller."""
    global _playback_timer
    
    if not _playback_timer:
        _playback_timer = playback_check_timer
        obs.timer_add(_playback_timer, 1000)  # Check every second
        log("Playback controller started")

def stop_playback_controller():
    """Stop the playback controller."""
    global _playback_timer
    
    if _playback_timer:
        obs.timer_remove(_playback_timer)
        _playback_timer = None
        log("Playback controller stopped")

def get_current_video_from_media_source():
    """Get current video ID from media source."""
    # TODO: Implement getting current video from OBS media source
    return None

def play_video(video_info):
    """Play a video through OBS Media Source."""
    # TODO: Implement video playback
    log(f"Playing video: {video_info.get('id', 'unknown')}")
    set_playing(True)

def stop_playback():
    """Stop current playback."""
    set_playing(False)
    log("Playback stopped")
