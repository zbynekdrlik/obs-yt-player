"""
Playback control for OBS YouTube Player.
This module now acts as a facade that imports functionality from specialized modules.
"""

# Re-export all public functions and variables from the sub-modules
# This maintains backward compatibility with existing code

# From playback_controller
from .playback_controller import (
    start_playback_controller,
    stop_playback_controller,
    start_next_video,
    start_specific_video,
    stop_current_playback,
    playback_controller,
    verify_sources
)

# From media_control  
from .media_control import (
    get_current_video_from_media_source,
    force_disable_media_loop,
    get_media_state,
    get_media_duration,
    get_media_time,
    update_media_source,
    update_text_source_content,
    is_video_near_end
)

# From opacity_control
from .opacity_control import (
    ensure_opacity_filter,
    update_text_opacity,
    fade_in_text,
    fade_out_text
)

# From title_manager
from .title_manager import (
    schedule_title_clear,
    schedule_title_show,
    cancel_title_timers,
    update_text_source
)

# From video_selector
from .video_selector import (
    select_next_video
)

# From state_handlers
from .state_handlers import (
    handle_playing_state,
    handle_ended_state,
    handle_stopped_state,
    handle_none_state,
    log_playback_progress
)

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
