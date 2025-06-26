"""
Thread-safe state management for multiple script instances.
Uses script path as unique key for complete isolation between instances.
"""

import threading
from typing import Dict, Any, Optional

# Global state storage - keyed by script path
_global_state: Dict[str, Dict[str, Any]] = {}
_state_lock = threading.Lock()

# Thread-local storage for script context
_thread_local = threading.local()

def set_thread_script_context(script_path: str):
    """Set the script context for the current thread."""
    _thread_local.script_path = script_path

def get_current_script_path() -> Optional[str]:
    """Get the script path for the current thread context."""
    return getattr(_thread_local, 'script_path', None)

def get_state() -> Dict[str, Any]:
    """Get state for the current script context."""
    script_path = get_current_script_path()
    if not script_path:
        raise RuntimeError("No script context set for this thread")
    
    with _state_lock:
        if script_path not in _global_state:
            _global_state[script_path] = _create_initial_state()
        return _global_state[script_path]

def clear_script_state(script_path: str):
    """Clear all state for a specific script."""
    with _state_lock:
        if script_path in _global_state:
            del _global_state[script_path]

def _create_initial_state() -> Dict[str, Any]:
    """Create initial state structure for a script instance."""
    return {
        # Configuration
        'playlist_url': '',
        'cache_dir': '',
        'playback_mode': 'continuous',
        'audio_only_mode': False,
        'gemini_api_key': None,
        
        # Runtime state
        'tools_ready': False,
        'stop_threads': False,
        'sync_requested': False,
        'scene_found': False,
        'media_source_found': False,
        'text_source_found': False,
        
        # Playback state
        'is_playing': False,
        'current_video_id': None,
        'first_video_played': False,
        'loop_video_id': None,
        'last_played_videos': [],
        
        # Processing queues
        'download_queue': [],
        'metadata_queue': [],
        'normalize_queue': [],
        
        # Cache
        'cache_registry': {},
        'cached_video_ids': set(),
        
        # Warnings
        'configuration_warnings': []
    }

# Convenience functions for common state operations
def get_playlist_url() -> str:
    """Get playlist URL from current script state."""
    return get_state().get('playlist_url', '')

def set_playlist_url(url: str):
    """Set playlist URL in current script state."""
    get_state()['playlist_url'] = url

def get_cache_dir() -> str:
    """Get cache directory from current script state."""
    return get_state().get('cache_dir', '')

def set_cache_dir(path: str):
    """Set cache directory in current script state."""
    get_state()['cache_dir'] = path

def is_tools_ready() -> bool:
    """Check if tools are ready in current script state."""
    return get_state().get('tools_ready', False)

def set_tools_ready(ready: bool):
    """Set tools ready status in current script state."""
    get_state()['tools_ready'] = ready

def should_stop_threads() -> bool:
    """Check if threads should stop in current script state."""
    return get_state().get('stop_threads', False)

def set_stop_threads(stop: bool):
    """Set stop threads flag in current script state."""
    get_state()['stop_threads'] = stop

def set_gemini_api_key(key: Optional[str]):
    """Set Gemini API key in current script state."""
    get_state()['gemini_api_key'] = key

def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from current script state."""
    return get_state().get('gemini_api_key')

def get_playback_mode() -> str:
    """Get playback mode from current script state."""
    return get_state().get('playback_mode', 'continuous')

def set_playback_mode(mode: str):
    """Set playback mode in current script state."""
    get_state()['playback_mode'] = mode

def set_first_video_played(played: bool):
    """Set first video played flag in current script state."""
    get_state()['first_video_played'] = played

def is_first_video_played() -> bool:
    """Check if first video has been played in current script state."""
    return get_state().get('first_video_played', False)

def set_loop_video_id(video_id: Optional[str]):
    """Set loop video ID in current script state."""
    get_state()['loop_video_id'] = video_id

def get_loop_video_id() -> Optional[str]:
    """Get loop video ID from current script state."""
    return get_state().get('loop_video_id')

def get_current_playback_video_id() -> Optional[str]:
    """Get current playback video ID from current script state."""
    return get_state().get('current_video_id')

def set_current_playback_video_id(video_id: Optional[str]):
    """Set current playback video ID in current script state."""
    get_state()['current_video_id'] = video_id

def is_playing() -> bool:
    """Check if video is playing in current script state."""
    return get_state().get('is_playing', False)

def set_playing(playing: bool):
    """Set playing status in current script state."""
    get_state()['is_playing'] = playing

def is_audio_only_mode() -> bool:
    """Check if audio only mode is enabled in current script state."""
    return get_state().get('audio_only_mode', False)

def set_audio_only_mode(enabled: bool):
    """Set audio only mode in current script state."""
    get_state()['audio_only_mode'] = enabled

def request_sync():
    """Request playlist sync in current script state."""
    get_state()['sync_requested'] = True

def is_sync_requested() -> bool:
    """Check if sync is requested in current script state."""
    return get_state().get('sync_requested', False)

def clear_sync_request():
    """Clear sync request in current script state."""
    get_state()['sync_requested'] = False

def set_scene_found(found: bool):
    """Set scene found status in current script state."""
    get_state()['scene_found'] = found

def is_scene_found() -> bool:
    """Check if scene is found in current script state."""
    return get_state().get('scene_found', False)

def set_media_source_found(found: bool):
    """Set media source found status in current script state."""
    get_state()['media_source_found'] = found

def is_media_source_found() -> bool:
    """Check if media source is found in current script state."""
    return get_state().get('media_source_found', False)

def set_text_source_found(found: bool):
    """Set text source found status in current script state."""
    get_state()['text_source_found'] = found

def is_text_source_found() -> bool:
    """Check if text source is found in current script state."""
    return get_state().get('text_source_found', False)

def get_download_queue() -> list:
    """Get download queue from current script state."""
    return get_state().get('download_queue', [])

def get_metadata_queue() -> list:
    """Get metadata queue from current script state."""
    return get_state().get('metadata_queue', [])

def get_normalize_queue() -> list:
    """Get normalize queue from current script state."""
    return get_state().get('normalize_queue', [])

def get_cache_registry() -> dict:
    """Get cache registry from current script state."""
    return get_state().get('cache_registry', {})

def get_cached_video_ids() -> set:
    """Get cached video IDs from current script state."""
    return get_state().get('cached_video_ids', set())

def get_last_played_videos() -> list:
    """Get last played videos from current script state."""
    return get_state().get('last_played_videos', [])

def add_configuration_warning(warning: str):
    """Add a configuration warning to current script state."""
    warnings = get_state().get('configuration_warnings', [])
    if warning not in warnings:
        warnings.append(warning)
        get_state()['configuration_warnings'] = warnings

def clear_configuration_warnings():
    """Clear all configuration warnings in current script state."""
    get_state()['configuration_warnings'] = []

def get_configuration_warnings() -> list:
    """Get configuration warnings from current script state."""
    return get_state().get('configuration_warnings', [])
