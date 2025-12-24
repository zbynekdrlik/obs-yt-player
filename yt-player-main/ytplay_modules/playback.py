"""
Playback control for OBS YouTube Player.
This module now acts as a facade that imports functionality from specialized modules.
"""

# Re-export all public functions and variables from the sub-modules
# This maintains backward compatibility with existing code

# From playback_controller
# From media_control
from .media_control import (
    force_disable_media_loop,
    get_current_video_from_media_source,
    get_media_duration,
    get_media_state,
    get_media_time,
    is_video_near_end,
    update_media_source,
    update_text_source_content,
)

# From opacity_control
from .opacity_control import ensure_opacity_filter, fade_in_text, fade_out_text, update_text_opacity
from .playback_controller import (
    playback_controller,
    start_next_video,
    start_playback_controller,
    start_specific_video,
    stop_current_playback,
    stop_playback_controller,
    verify_sources,
)

# From state_handlers
from .state_handlers import (
    handle_ended_state,
    handle_none_state,
    handle_playing_state,
    handle_stopped_state,
    log_playback_progress,
)

# From title_manager
from .title_manager import cancel_title_timers, schedule_title_clear, schedule_title_show, update_text_source

# From video_selector
from .video_selector import select_next_video

# Make sure all the original functions are available for import
__all__ = [
    # Controller functions
    'start_playback_controller',
    'stop_playback_controller',
    'start_next_video',
    'start_specific_video',
    'stop_current_playback',
    'playback_controller',
    'verify_sources',

    # Media control functions
    'get_current_video_from_media_source',
    'force_disable_media_loop',
    'get_media_state',
    'get_media_duration',
    'get_media_time',
    'update_media_source',
    'update_text_source_content',
    'is_video_near_end',

    # Opacity control functions
    'ensure_opacity_filter',
    'update_text_opacity',
    'fade_in_text',
    'fade_out_text',

    # Title manager functions
    'schedule_title_clear',
    'schedule_title_show',
    'cancel_title_timers',
    'update_text_source',

    # Video selector functions
    'select_next_video',

    # State handler functions
    'handle_playing_state',
    'handle_ended_state',
    'handle_stopped_state',
    'handle_none_state',
    'log_playback_progress'
]
