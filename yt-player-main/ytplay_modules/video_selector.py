"""Video selection logic.
Handles random selection, loop mode, and played video tracking.
"""

import random

from .config import PLAYBACK_MODE_LOOP
from .logger import log
from .state import (
    add_played_video,
    clear_played_videos,
    get_cached_videos,
    get_loop_video_id,
    get_playback_mode,
    get_played_videos,
    set_loop_video_id,
)


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

    # Filter played_videos to only include videos still in cache
    # (handles case where playlist changed between sessions)
    valid_played = [v for v in played_videos if v in available_videos]
    if len(valid_played) != len(played_videos):
        # Clean up stale entries by resetting and re-adding valid ones
        stale_count = len(played_videos) - len(valid_played)
        log(f"Cleaned {stale_count} stale entries from play history")
        clear_played_videos()
        for v in valid_played:
            add_played_video(v)
        played_videos = valid_played

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


def validate_video_file(video_id):
    """
    Validate that a video file exists and is accessible.
    Returns True if valid, False otherwise.
    """
    import os

    from .state import get_cached_video_info

    video_info = get_cached_video_info(video_id)
    if not video_info:
        log(f"ERROR: No info for video {video_id}")
        return False

    # Validate video file exists
    if not os.path.exists(video_info["path"]):
        log(f"ERROR: Video file missing: {video_info['path']}")
        return False

    return True


def get_video_display_info(video_id):
    """
    Get display information for a video (song, artist, etc).
    Returns dict with song, artist, and gemini_failed status.
    """
    from .state import get_cached_video_info

    video_info = get_cached_video_info(video_id)
    if not video_info:
        return {"song": "Unknown Song", "artist": "Unknown Artist", "gemini_failed": False}

    # Extract metadata with fallbacks
    song = video_info.get("song", "Unknown Song")
    artist = video_info.get("artist", "Unknown Artist")
    gemini_failed = video_info.get("gemini_failed", False)

    # Log if metadata is missing
    if song == "Unknown Song" or artist == "Unknown Artist":
        log(f"WARNING: Missing metadata for video {video_id} - Song: '{song}', Artist: '{artist}'")

    return {"song": song, "artist": artist, "gemini_failed": gemini_failed}
