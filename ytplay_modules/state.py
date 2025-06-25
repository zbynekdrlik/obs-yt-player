"""
Global state management for OBS YouTube Player.
Thread-safe state variables and accessors.
"""

import threading
from config import DEFAULT_PLAYLIST_URL, DEFAULT_PLAYBACK_MODE, DEFAULT_AUDIO_ONLY_MODE

# Threading synchronization
_state_lock = threading.Lock()

# Script identification
_script_name = None  # Set by main script
_script_dir = None   # Set by main script

# Configuration state
_playlist_url = DEFAULT_PLAYLIST_URL
_cache_dir = None  # Will be set based on script name
_gemini_api_key = None  # Add Gemini API key state
_playback_mode = DEFAULT_PLAYBACK_MODE  # Playback behavior mode
_audio_only_mode = DEFAULT_AUDIO_ONLY_MODE  # Audio-only mode flag

# System state flags
_tools_ready = False
_tools_logged_waiting = False
_scene_active = False
_is_playing = False
_stop_threads = False
_sync_on_startup_done = False
_stop_requested = False  # New flag for stop button
_first_video_played = False  # Track if first video has been played (for single/loop modes)

# Playback state
_current_video_path = None
_current_playback_video_id = None
_loop_video_id = None  # Video ID to loop in loop mode

# Data structures
_cached_videos = {}  # {video_id: {"path": str, "song": str, "artist": str, "normalized": bool}}
_played_videos = []  # List of video IDs to avoid repeats
_playlist_video_ids = set()  # Current playlist video IDs

# Synchronization events
sync_event = threading.Event()  # Signal for manual sync
video_queue = None  # Will be initialized as queue.Queue()

# Thread references
tools_thread = None
playlist_sync_thread = None
process_videos_thread = None

# Progress tracking
download_progress_milestones = {}  # Track logged milestones per video

# Initialize queue
import queue
video_queue = queue.Queue()

# ===== SCRIPT IDENTIFICATION ACCESSORS =====
def get_script_name():
    """Get the script name (e.g., 'ytplay', 'yt_worship')."""
    with _state_lock:
        return _script_name

def set_script_name(name):
    """Set the script name. Called by main script on initialization."""
    global _script_name
    with _state_lock:
        _script_name = name

def get_script_dir():
    """Get the script directory path."""
    with _state_lock:
        return _script_dir

def set_script_dir(directory):
    """Set the script directory. Called by main script on initialization."""
    global _script_dir
    with _state_lock:
        _script_dir = directory

# ===== CONFIGURATION ACCESSORS =====
def get_playlist_url():
    with _state_lock:
        return _playlist_url

def set_playlist_url(url):
    global _playlist_url
    with _state_lock:
        _playlist_url = url

def get_cache_dir():
    with _state_lock:
        return _cache_dir

def set_cache_dir(directory):
    global _cache_dir
    with _state_lock:
        _cache_dir = directory

def get_gemini_api_key():
    """Get the Gemini API key."""
    with _state_lock:
        return _gemini_api_key

def set_gemini_api_key(key):
    """Set the Gemini API key."""
    global _gemini_api_key
    with _state_lock:
        _gemini_api_key = key

def get_playback_mode():
    """Get the current playback mode."""
    with _state_lock:
        return _playback_mode

def set_playback_mode(mode):
    """Set the playback mode."""
    global _playback_mode
    with _state_lock:
        _playback_mode = mode

def is_audio_only_mode():
    """Get the audio-only mode setting."""
    with _state_lock:
        return _audio_only_mode

def set_audio_only_mode(enabled):
    """Set the audio-only mode."""
    global _audio_only_mode
    with _state_lock:
        _audio_only_mode = enabled

# ===== STATE FLAG ACCESSORS =====
def is_tools_ready():
    with _state_lock:
        return _tools_ready

def set_tools_ready(ready):
    global _tools_ready
    with _state_lock:
        _tools_ready = ready

def is_tools_logged_waiting():
    with _state_lock:
        return _tools_logged_waiting

def set_tools_logged_waiting(logged):
    global _tools_logged_waiting
    with _state_lock:
        _tools_logged_waiting = logged

def is_scene_active():
    with _state_lock:
        return _scene_active

def set_scene_active(active):
    global _scene_active
    with _state_lock:
        _scene_active = active

def is_playing():
    with _state_lock:
        return _is_playing

def set_playing(playing):
    global _is_playing
    with _state_lock:
        _is_playing = playing

def should_stop_threads():
    with _state_lock:
        return _stop_threads

def set_stop_threads(stop):
    global _stop_threads
    with _state_lock:
        _stop_threads = stop

def is_sync_on_startup_done():
    with _state_lock:
        return _sync_on_startup_done

def set_sync_on_startup_done(done):
    global _sync_on_startup_done
    with _state_lock:
        _sync_on_startup_done = done

def is_stop_requested():
    """Check if stop has been requested (e.g., via stop button)."""
    with _state_lock:
        return _stop_requested

def set_stop_requested(requested):
    """Set stop request flag."""
    global _stop_requested
    with _state_lock:
        _stop_requested = requested

def clear_stop_request():
    """Clear the stop request flag."""
    global _stop_requested
    with _state_lock:
        _stop_requested = False

def is_first_video_played():
    """Check if the first video has been played (for single/loop modes)."""
    with _state_lock:
        return _first_video_played

def set_first_video_played(played):
    """Set whether the first video has been played."""
    global _first_video_played
    with _state_lock:
        _first_video_played = played

# ===== PLAYBACK STATE ACCESSORS =====
def get_current_video_path():
    with _state_lock:
        return _current_video_path

def set_current_video_path(path):
    global _current_video_path
    with _state_lock:
        _current_video_path = path

def get_current_playback_video_id():
    with _state_lock:
        return _current_playback_video_id

def set_current_playback_video_id(video_id):
    global _current_playback_video_id
    with _state_lock:
        _current_playback_video_id = video_id

def get_loop_video_id():
    """Get the video ID to loop in loop mode."""
    with _state_lock:
        return _loop_video_id

def set_loop_video_id(video_id):
    """Set the video ID to loop in loop mode."""
    global _loop_video_id
    with _state_lock:
        _loop_video_id = video_id

# ===== DATA STRUCTURE ACCESSORS =====
def get_cached_videos():
    """Get a copy of cached videos dict."""
    with _state_lock:
        return _cached_videos.copy()

def add_cached_video(video_id, info):
    """Add or update a cached video."""
    with _state_lock:
        _cached_videos[video_id] = info

def remove_cached_video(video_id):
    """Remove a cached video."""
    with _state_lock:
        if video_id in _cached_videos:
            del _cached_videos[video_id]

def is_video_cached(video_id):
    """Check if video is in cache."""
    with _state_lock:
        return video_id in _cached_videos

def get_cached_video_info(video_id):
    """Get info for a cached video."""
    with _state_lock:
        return _cached_videos.get(video_id)

def get_playlist_video_ids():
    """Get a copy of playlist video IDs."""
    with _state_lock:
        return _playlist_video_ids.copy()

def set_playlist_video_ids(video_ids):
    """Update playlist video IDs."""
    global _playlist_video_ids
    with _state_lock:
        _playlist_video_ids.clear()
        _playlist_video_ids.update(video_ids)

def add_played_video(video_id):
    """Add video to played list."""
    with _state_lock:
        if video_id not in _played_videos:
            _played_videos.append(video_id)

def clear_played_videos():
    """Clear played videos list."""
    with _state_lock:
        _played_videos.clear()

def get_played_videos():
    """Get a copy of played videos list."""
    with _state_lock:
        return _played_videos.copy()

def is_video_being_processed(video_id):
    """Check if video is currently being downloaded/processed."""
    return video_id == get_current_playback_video_id()