"""
Global state management for OBS YouTube Player.
Thread-safe state variables with true multi-instance support.

v3.6.1: Fixed backward compatibility and thread isolation
Each script instance maintains its own isolated state.
"""

import threading
import os
from config import DEFAULT_PLAYLIST_URL, DEFAULT_PLAYBACK_MODE, DEFAULT_AUDIO_ONLY_MODE
import queue

# Master state dictionary - keyed by script path
_script_states = {}
_master_lock = threading.Lock()

class ScriptState:
    """Encapsulates all state for a single script instance."""
    
    def __init__(self, script_path):
        self.script_path = script_path
        self.lock = threading.Lock()
        
        # Script identification
        self.script_name = None  # Set by main script
        self.script_dir = None   # Set by main script

        # Configuration state
        self.playlist_url = DEFAULT_PLAYLIST_URL
        self.cache_dir = None  # Will be set based on script name
        self.gemini_api_key = None  # Add Gemini API key state
        self.playback_mode = DEFAULT_PLAYBACK_MODE  # Playback behavior mode
        self.audio_only_mode = DEFAULT_AUDIO_ONLY_MODE  # Audio-only mode flag

        # System state flags
        self.tools_ready = False
        self.tools_logged_waiting = False
        self.scene_active = False
        self.is_playing = False
        self.stop_threads = False
        self.sync_on_startup_done = False
        self.stop_requested = False  # New flag for stop button
        self.first_video_played = False  # Track if first video has been played (for single/loop modes)

        # Playback state
        self.current_video_path = None
        self.current_playback_video_id = None
        self.loop_video_id = None  # Video ID to loop in loop mode

        # Data structures
        self.cached_videos = {}  # {video_id: {"path": str, "song": str, "artist": str, "normalized": bool}}
        self.played_videos = []  # List of video IDs to avoid repeats
        self.playlist_video_ids = set()  # Current playlist video IDs

        # Synchronization events
        self.sync_event = threading.Event()  # Signal for manual sync
        self.video_queue = queue.Queue()  # Queue for video processing

        # Thread references
        self.tools_thread = None
        self.playlist_sync_thread = None
        self.process_videos_thread = None
        self.reprocess_thread = None  # v3.6.1: Added missing thread reference

        # Progress tracking
        self.download_progress_milestones = {}  # Track logged milestones per video

# Current script path - set by each script instance
_current_script_path = None

def get_current_script_path():
    """Get the current script path from thread-local storage or fallback."""
    # Try to get from thread-local storage first
    thread_local = getattr(threading.current_thread(), '_script_path', None)
    if thread_local:
        return thread_local
    
    # Fallback to global current script path
    return _current_script_path

def set_current_script_path(script_path):
    """Set the current script path for the main thread."""
    global _current_script_path
    _current_script_path = script_path
    
    # Also set in thread-local storage
    threading.current_thread()._script_path = script_path

def set_thread_script_context(script_path):
    """Set script context for the current thread."""
    threading.current_thread()._script_path = script_path

def get_or_create_state(script_path=None):
    """Get or create state for the given script path."""
    if script_path is None:
        script_path = get_current_script_path()
    
    if not script_path:
        raise ValueError("No script path provided and no current script context")
    
    with _master_lock:
        if script_path not in _script_states:
            _script_states[script_path] = ScriptState(script_path)
        return _script_states[script_path]

def cleanup_state(script_path):
    """Clean up state for a script that's being unloaded."""
    with _master_lock:
        if script_path in _script_states:
            del _script_states[script_path]

# ===== CONVENIENCE FUNCTIONS =====
# These functions automatically use the current script's state

def _get_state():
    """Get the current script's state."""
    return get_or_create_state()

# ===== SCRIPT IDENTIFICATION ACCESSORS =====
def get_script_name():
    """Get the script name (e.g., 'ytplay', 'yt_worship')."""
    state = _get_state()
    with state.lock:
        return state.script_name

def set_script_name(name):
    """Set the script name. Called by main script on initialization."""
    state = _get_state()
    with state.lock:
        state.script_name = name

def get_script_dir():
    """Get the script directory path."""
    state = _get_state()
    with state.lock:
        return state.script_dir

def set_script_dir(directory):
    """Set the script directory. Called by main script on initialization."""
    state = _get_state()
    with state.lock:
        state.script_dir = directory

# ===== CONFIGURATION ACCESSORS =====
def get_playlist_url():
    state = _get_state()
    with state.lock:
        return state.playlist_url

def set_playlist_url(url):
    state = _get_state()
    with state.lock:
        state.playlist_url = url

def get_cache_dir():
    state = _get_state()
    with state.lock:
        return state.cache_dir

def set_cache_dir(directory):
    state = _get_state()
    with state.lock:
        state.cache_dir = directory

def get_gemini_api_key():
    """Get the Gemini API key."""
    state = _get_state()
    with state.lock:
        return state.gemini_api_key

def set_gemini_api_key(key):
    """Set the Gemini API key."""
    state = _get_state()
    with state.lock:
        state.gemini_api_key = key

def get_playback_mode():
    """Get the current playback mode."""
    state = _get_state()
    with state.lock:
        return state.playback_mode

def set_playback_mode(mode):
    """Set the playback mode."""
    state = _get_state()
    with state.lock:
        state.playback_mode = mode

def is_audio_only_mode():
    """Get the audio-only mode setting."""
    state = _get_state()
    with state.lock:
        return state.audio_only_mode

def set_audio_only_mode(enabled):
    """Set the audio-only mode."""
    state = _get_state()
    with state.lock:
        state.audio_only_mode = enabled

# ===== STATE FLAG ACCESSORS =====
def is_tools_ready():
    state = _get_state()
    with state.lock:
        return state.tools_ready

def set_tools_ready(ready):
    state = _get_state()
    with state.lock:
        state.tools_ready = ready

def is_tools_logged_waiting():
    state = _get_state()
    with state.lock:
        return state.tools_logged_waiting

def set_tools_logged_waiting(logged):
    state = _get_state()
    with state.lock:
        state.tools_logged_waiting = logged

def is_scene_active():
    state = _get_state()
    with state.lock:
        return state.scene_active

def set_scene_active(active):
    state = _get_state()
    with state.lock:
        state.scene_active = active

def is_playing():
    state = _get_state()
    with state.lock:
        return state.is_playing

def set_playing(playing):
    state = _get_state()
    with state.lock:
        state.is_playing = playing

def should_stop_threads():
    state = _get_state()
    with state.lock:
        return state.stop_threads

def set_stop_threads(stop):
    state = _get_state()
    with state.lock:
        state.stop_threads = stop

def is_sync_on_startup_done():
    state = _get_state()
    with state.lock:
        return state.sync_on_startup_done

def set_sync_on_startup_done(done):
    state = _get_state()
    with state.lock:
        state.sync_on_startup_done = done

def is_stop_requested():
    """Check if stop has been requested (e.g., via stop button)."""
    state = _get_state()
    with state.lock:
        return state.stop_requested

def set_stop_requested(requested):
    """Set stop request flag."""
    state = _get_state()
    with state.lock:
        state.stop_requested = requested

def clear_stop_request():
    """Clear the stop request flag."""
    state = _get_state()
    with state.lock:
        state.stop_requested = False

def is_first_video_played():
    """Check if the first video has been played (for single/loop modes)."""
    state = _get_state()
    with state.lock:
        return state.first_video_played

def set_first_video_played(played):
    """Set whether the first video has been played."""
    state = _get_state()
    with state.lock:
        state.first_video_played = played

# ===== PLAYBACK STATE ACCESSORS =====
def get_current_video_path():
    state = _get_state()
    with state.lock:
        return state.current_video_path

def set_current_video_path(path):
    state = _get_state()
    with state.lock:
        state.current_video_path = path

def get_current_playback_video_id():
    state = _get_state()
    with state.lock:
        return state.current_playback_video_id

def set_current_playback_video_id(video_id):
    state = _get_state()
    with state.lock:
        state.current_playback_video_id = video_id

def get_loop_video_id():
    """Get the video ID to loop in loop mode."""
    state = _get_state()
    with state.lock:
        return state.loop_video_id

def set_loop_video_id(video_id):
    """Set the video ID to loop in loop mode."""
    state = _get_state()
    with state.lock:
        state.loop_video_id = video_id

# ===== DATA STRUCTURE ACCESSORS =====
def get_cached_videos():
    """Get a copy of cached videos dict."""
    state = _get_state()
    with state.lock:
        return state.cached_videos.copy()

def add_cached_video(video_id, info):
    """Add or update a cached video."""
    state = _get_state()
    with state.lock:
        state.cached_videos[video_id] = info

def remove_cached_video(video_id):
    """Remove a cached video."""
    state = _get_state()
    with state.lock:
        if video_id in state.cached_videos:
            del state.cached_videos[video_id]

def is_video_cached(video_id):
    """Check if video is in cache."""
    state = _get_state()
    with state.lock:
        return video_id in state.cached_videos

def get_cached_video_info(video_id):
    """Get info for a cached video."""
    state = _get_state()
    with state.lock:
        return state.cached_videos.get(video_id)

def get_playlist_video_ids():
    """Get a copy of playlist video IDs."""
    state = _get_state()
    with state.lock:
        return state.playlist_video_ids.copy()

def set_playlist_video_ids(video_ids):
    """Update playlist video IDs."""
    state = _get_state()
    with state.lock:
        state.playlist_video_ids.clear()
        state.playlist_video_ids.update(video_ids)

def add_played_video(video_id):
    """Add video to played list."""
    state = _get_state()
    with state.lock:
        if video_id not in state.played_videos:
            state.played_videos.append(video_id)

def clear_played_videos():
    """Clear played videos list."""
    state = _get_state()
    with state.lock:
        state.played_videos.clear()

def get_played_videos():
    """Get a copy of played videos list."""
    state = _get_state()
    with state.lock:
        return state.played_videos.copy()

def is_video_being_processed(video_id):
    """Check if video is currently being downloaded/processed."""
    return video_id == get_current_playback_video_id()

# ===== SYNCHRONIZATION OBJECTS =====
# These need special handling because they can't be copied

@property
def sync_event():
    """Get the sync event for the current script."""
    state = _get_state()
    return state.sync_event

@property  
def video_queue():
    """Get the video queue for the current script."""
    state = _get_state()
    return state.video_queue

# For backward compatibility - create module-level references
# These will be overridden by each script instance
sync_event = None
video_queue = None
tools_thread = None
playlist_sync_thread = None
process_videos_thread = None
reprocess_thread = None  # v3.6.1: Added
download_progress_milestones = {}  # v3.6.1: Fixed - was missing

# This function should be called by each script to set up its context
def initialize_script_context(script_path):
    """Initialize state context for a script instance."""
    set_current_script_path(script_path)
    state = get_or_create_state(script_path)
    
    # Update module-level references for backward compatibility
    global sync_event, video_queue, tools_thread, playlist_sync_thread, process_videos_thread, reprocess_thread, download_progress_milestones
    sync_event = state.sync_event
    video_queue = state.video_queue
    tools_thread = state.tools_thread
    playlist_sync_thread = state.playlist_sync_thread
    process_videos_thread = state.process_videos_thread
    reprocess_thread = state.reprocess_thread
    download_progress_milestones = state.download_progress_milestones
    
    return state
