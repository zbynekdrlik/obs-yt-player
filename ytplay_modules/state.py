"""
State management module with script isolation.
Each script instance gets its own isolated state container.
"""

import threading
from typing import Any, Dict, Optional

# Global state dictionary - keys are script paths
_script_states: Dict[str, Dict[str, Any]] = {}

# Lock for thread-safe state access
_state_lock = threading.Lock()

# Thread-local storage for script context
_thread_local = threading.local()

def initialize_script_context(script_path: str) -> Dict[str, Any]:
    """Initialize state for a specific script instance."""
    with _state_lock:
        if script_path not in _script_states:
            _script_states[script_path] = {
                # Script identification
                'script_name': None,
                'script_dir': None,
                
                # Configuration
                'playlist_url': '',
                'cache_dir': None,
                'gemini_api_key': None,
                'playback_mode': 'continuous',
                'audio_only_mode': False,
                
                # Runtime state
                'tools_ready': False,
                'stop_threads': False,
                'manual_sync_triggered': False,
                
                # Playback state
                'playing': False,
                'paused': False,
                'current_video_id': None,
                'current_file_path': None,
                'last_played_video': None,
                'first_video_played': False,
                'loop_video_id': None,
                'playback_position': 0.0,
                
                # Cache state
                'local_videos': set(),
                'playlist_videos': [],
                'metadata_cache': {},
                'gemini_failures': set(),
                
                # Queue management
                'download_queue': None,
                'normalization_queue': None,
                
                # Scene state
                'scene_verified': False,
                'scene_error_shown': False,
                'scene_active': False,
                
                # Threads
                'threads': {}
            }
        
        # Set thread-local context
        _thread_local.script_path = script_path
        
        return _script_states[script_path]

def cleanup_state(script_path: str):
    """Clean up state for a script instance."""
    with _state_lock:
        if script_path in _script_states:
            del _script_states[script_path]

def get_state() -> Dict[str, Any]:
    """Get the current script's state."""
    script_path = getattr(_thread_local, 'script_path', None)
    if not script_path:
        raise RuntimeError("No script context set for current thread")
    
    with _state_lock:
        if script_path not in _script_states:
            raise RuntimeError(f"Script {script_path} not initialized")
        return _script_states[script_path]

def set_thread_script_context(script_path: str):
    """Set the script context for the current thread."""
    _thread_local.script_path = script_path

def set_current_script_path(script_path: str):
    """Set the script path for the current execution context."""
    _thread_local.script_path = script_path

# ===== SCRIPT IDENTIFICATION =====
def set_script_name(name: str):
    """Set the script name."""
    state = get_state()
    state['script_name'] = name

def get_script_name() -> str:
    """Get the script name."""
    state = get_state()
    return state['script_name']

def set_script_dir(directory: str):
    """Set the script directory."""
    state = get_state()
    state['script_dir'] = directory

def get_script_dir() -> str:
    """Get the script directory."""
    state = get_state()
    return state['script_dir']

# ===== CONFIGURATION =====
def get_playlist_url() -> str:
    """Get the playlist URL."""
    state = get_state()
    return state['playlist_url']

def set_playlist_url(url: str):
    """Set the playlist URL."""
    state = get_state()
    state['playlist_url'] = url

def get_cache_dir() -> Optional[str]:
    """Get the cache directory."""
    state = get_state()
    return state['cache_dir']

def set_cache_dir(directory: Optional[str]):
    """Set the cache directory."""
    state = get_state()
    state['cache_dir'] = directory

def get_gemini_api_key() -> Optional[str]:
    """Get the Gemini API key."""
    state = get_state()
    return state['gemini_api_key']

def set_gemini_api_key(key: Optional[str]):
    """Set the Gemini API key."""
    state = get_state()
    state['gemini_api_key'] = key

def get_playback_mode() -> str:
    """Get the playback mode."""
    state = get_state()
    return state['playback_mode']

def set_playback_mode(mode: str):
    """Set the playback mode."""
    state = get_state()
    state['playback_mode'] = mode

def is_audio_only_mode() -> bool:
    """Check if audio-only mode is enabled."""
    state = get_state()
    return state['audio_only_mode']

def set_audio_only_mode(enabled: bool):
    """Set audio-only mode."""
    state = get_state()
    state['audio_only_mode'] = enabled

# ===== RUNTIME STATE =====
def is_tools_ready() -> bool:
    """Check if tools are ready."""
    state = get_state()
    return state['tools_ready']

def set_tools_ready(ready: bool):
    """Set tools ready state."""
    state = get_state()
    state['tools_ready'] = ready

def should_stop_threads() -> bool:
    """Check if threads should stop."""
    state = get_state()
    return state['stop_threads']

def set_stop_threads(stop: bool):
    """Set stop threads flag."""
    state = get_state()
    state['stop_threads'] = stop

def is_manual_sync_triggered() -> bool:
    """Check if manual sync was triggered."""
    state = get_state()
    return state['manual_sync_triggered']

def set_manual_sync_triggered(triggered: bool):
    """Set manual sync triggered flag."""
    state = get_state()
    state['manual_sync_triggered'] = triggered

# ===== PLAYBACK STATE =====
def is_playing() -> bool:
    """Check if currently playing."""
    state = get_state()
    return state['playing']

def set_playing(playing: bool):
    """Set playing state."""
    state = get_state()
    state['playing'] = playing

def is_paused() -> bool:
    """Check if currently paused."""
    state = get_state()
    return state['paused']

def set_paused(paused: bool):
    """Set paused state."""
    state = get_state()
    state['paused'] = paused

def get_current_playback_video_id() -> Optional[str]:
    """Get current playing video ID."""
    state = get_state()
    return state['current_video_id']

def set_current_playback_video_id(video_id: Optional[str]):
    """Set current playing video ID."""
    state = get_state()
    state['current_video_id'] = video_id

def get_current_file_path() -> Optional[str]:
    """Get current playing file path."""
    state = get_state()
    return state['current_file_path']

def set_current_file_path(path: Optional[str]):
    """Set current playing file path."""
    state = get_state()
    state['current_file_path'] = path

# Additional alias for compatibility
def set_current_video_path(path: Optional[str]):
    """Set current video path (alias for set_current_file_path)."""
    set_current_file_path(path)

def get_last_played_video() -> Optional[str]:
    """Get last played video ID."""
    state = get_state()
    return state['last_played_video']

def set_last_played_video(video_id: Optional[str]):
    """Set last played video ID."""
    state = get_state()
    state['last_played_video'] = video_id

def is_first_video_played() -> bool:
    """Check if first video has been played."""
    state = get_state()
    return state['first_video_played']

def set_first_video_played(played: bool):
    """Set first video played flag."""
    state = get_state()
    state['first_video_played'] = played

def get_loop_video_id() -> Optional[str]:
    """Get the video ID to loop."""
    state = get_state()
    return state['loop_video_id']

def set_loop_video_id(video_id: Optional[str]):
    """Set the video ID to loop."""
    state = get_state()
    state['loop_video_id'] = video_id

def get_playback_position() -> float:
    """Get current playback position."""
    state = get_state()
    return state['playback_position']

def set_playback_position(position: float):
    """Set current playback position."""
    state = get_state()
    state['playback_position'] = position

# ===== CACHE STATE =====
def get_local_videos() -> set:
    """Get set of local video IDs."""
    state = get_state()
    return state['local_videos']

def get_playlist_videos() -> list:
    """Get list of playlist videos."""
    state = get_state()
    return state['playlist_videos']

def set_playlist_videos(videos: list):
    """Set playlist videos."""
    state = get_state()
    state['playlist_videos'] = videos

def get_metadata_cache() -> dict:
    """Get metadata cache."""
    state = get_state()
    return state['metadata_cache']

def get_gemini_failures() -> set:
    """Get set of Gemini failure video IDs."""
    state = get_state()
    return state['gemini_failures']

# ===== QUEUE MANAGEMENT =====
def get_download_queue():
    """Get download queue."""
    state = get_state()
    return state['download_queue']

def set_download_queue(queue):
    """Set download queue."""
    state = get_state()
    state['download_queue'] = queue

def get_normalization_queue():
    """Get normalization queue."""
    state = get_state()
    return state['normalization_queue']

def set_normalization_queue(queue):
    """Set normalization queue."""
    state = get_state()
    state['normalization_queue'] = queue

# ===== SCENE STATE =====
def is_scene_verified() -> bool:
    """Check if scene is verified."""
    state = get_state()
    return state['scene_verified']

def set_scene_verified(verified: bool):
    """Set scene verified state."""
    state = get_state()
    state['scene_verified'] = verified

def is_scene_error_shown() -> bool:
    """Check if scene error was shown."""
    state = get_state()
    return state['scene_error_shown']

def set_scene_error_shown(shown: bool):
    """Set scene error shown flag."""
    state = get_state()
    state['scene_error_shown'] = shown

def reset_scene_error_flag():
    """Reset scene error flag."""
    state = get_state()
    state['scene_error_shown'] = False

def is_scene_active() -> bool:
    """Check if scene is active."""
    state = get_state()
    return state.get('scene_active', False)

def set_scene_active(active: bool):
    """Set scene active state."""
    state = get_state()
    state['scene_active'] = active

# ===== THREAD MANAGEMENT =====
def register_thread(name: str, thread):
    """Register a thread for this script instance."""
    state = get_state()
    state['threads'][name] = thread

def get_thread(name: str):
    """Get a registered thread."""
    state = get_state()
    return state['threads'].get(name)

def unregister_thread(name: str):
    """Unregister a thread."""
    state = get_state()
    if name in state['threads']:
        del state['threads'][name]

# ===== CACHED VIDEO INFO =====
def get_cached_videos() -> set:
    """Get set of cached video IDs."""
    return get_local_videos()

def get_cached_video_info(video_id: str) -> Optional[dict]:
    """Get cached video info."""
    metadata = get_metadata_cache()
    return metadata.get(video_id)
