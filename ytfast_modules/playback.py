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
_is