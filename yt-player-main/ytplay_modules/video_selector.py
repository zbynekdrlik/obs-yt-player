"""Video selection logic for OBS YouTube Player.
Handles choosing next video based on playback mode.
"""

import random
import os

from .logger import log
from .state import (
    get_cached_videos, get_played_videos, add_played_video,
    clear_played_videos, get_playback_mode, get_loop_video_id
)
from .cache import validate_video_file
from .config import PLAYBACK_MODE_LOOP

def select_next_video():
    """Select next video to play based on current mode."""
    cached_videos = get_cached_videos()
    if not cached_videos:
        log("No videos available to play")
        return None
    
    playback_mode = get_playback_mode()
    
    # In loop mode, check if we have a loop video set
    if playback_mode == PLAYBACK_MODE_LOOP:
        loop_video_id = get_loop_video_id()
        if loop_video_id and loop_video_id in cached_videos:
            log(f"Loop mode: Selecting loop video {loop_video_id}")
            return loop_video_id
        else:
            log("Loop mode: No loop video set, selecting random video")
    
    # For continuous mode or when no loop video is set
    played_videos = get_played_videos()
    
    # Find unplayed videos
    unplayed = [vid for vid in cached_videos if vid not in played_videos]
    
    if not unplayed:
        # All videos played, reset history
        log("All videos played, resetting play history")
        clear_played_videos()
        unplayed = list(cached_videos.keys())
    
    # Select random video from unplayed
    if unplayed:
        selected = random.choice(unplayed)
        add_played_video(selected)
        
        # If in loop mode and no loop video set, set this as the loop video
        if playback_mode == PLAYBACK_MODE_LOOP and not get_loop_video_id():
            from .state import set_loop_video_id
            set_loop_video_id(selected)
            log(f"Loop mode: Set {selected} as loop video")
        
        return selected
    
    return None

def get_video_display_info(video_id):
    """Get display information for a video."""
    from .state import get_cached_video_info
    video_info = get_cached_video_info(video_id)
    
    if not video_info:
        return {
            'song': 'Unknown Song',
            'artist': 'Unknown Artist',
            'gemini_failed': False
        }
    
    return {
        'song': video_info.get('song', 'Unknown Song'),
        'artist': video_info.get('artist', 'Unknown Artist'),
        'gemini_failed': video_info.get('gemini_failed', False)
    }

def validate_video_file(video_id):
    """Validate that video file exists and is playable."""
    from .state import get_cached_video_info, remove_cached_video
    
    video_info = get_cached_video_info(video_id)
    if not video_info:
        return False
    
    video_path = video_info.get('path')
    if not video_path:
        return False
    
    # Check if file exists and is valid
    from .cache import validate_video_file as validate_file
    if not validate_file(video_path):
        log(f"Video file missing or invalid: {video_path}")
        # Remove from cache
        remove_cached_video(video_id)
        return False
    
    return True