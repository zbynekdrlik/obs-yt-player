"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source with metadata display. All processing runs in background threads.
"""

import obspython as obs
import threading
import queue
import os
import time
import logging
import subprocess
from pathlib import Path
import urllib.request
import platform
import stat
import json
import sys

# ===== MODULE-LEVEL CONSTANTS =====
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLrAl6rYJWZ7J5XKz9nZQ9J8Z9J8Z9J8Z9"
DEFAULT_CACHE_DIR = os.path.expanduser("~/obs_ytfast_cache")
SCENE_NAME = "ytfast"  # Scene name matches script filename
MEDIA_SOURCE_NAME = "video"
TEXT_SOURCE_NAME = "title"
TOOLS_SUBDIR = "tools"
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
SYNC_INTERVAL = 3600  # 1 hour in seconds
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second in milliseconds
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
MAX_RESOLUTION = "1440"
TOOLS_CHECK_INTERVAL = 60  # Retry tools download every 60 seconds

# URLs for tool downloads
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_WIN = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# FFmpeg URLs by platform
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# ===== GLOBAL VARIABLES =====
# Threading infrastructure
tools_thread = None
playlist_sync_thread = None
download_worker_thread = None
normalization_worker_thread = None
metadata_worker_thread = None

# Synchronization primitives
state_lock = threading.Lock()
download_queue = queue.Queue()
normalization_queue = queue.Queue()
metadata_queue = queue.Queue()

# State flags
tools_ready = False
tools_logged_waiting = False
scene_active = False
is_playing = False
current_video_path = None
stop_threads = False

# Data structures
cached_videos = {}  # {video_id: {"path": str, "song": str, "artist": str, "normalized": bool}}
played_videos = []  # List of video IDs to avoid repeats
playlist_video_ids = set()  # Current playlist video IDs

# Script properties
playlist_url = DEFAULT_PLAYLIST_URL
cache_dir = DEFAULT_CACHE_DIR
debug_enabled = True

# ===== LOGGING HELPER =====
def log(message, level="NORMAL"):
    """Log messages with timestamp and level."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if level == "DEBUG" and not debug_enabled:
        return
    
    formatted_message = f"[{timestamp}] [{level}] {message}"
    
    if level == "DEBUG":
        print(f"[ytfast DEBUG] {formatted_message}")
    else:
        print(f"[ytfast] {formatted_message}")

# ===== TOOL MANAGEMENT FUNCTIONS =====
def download_file(url, destination, description="file"):
    """Download a file from URL to destination."""
    try:
        log(f"Downloading {description} from {url}", "DEBUG")
        
        # Create parent directory if needed
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download with progress
        def download_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                if block_num % 100 == 0:  # Log every 100 blocks
                    log(f"Downloading {description}: {percent:.1f}%", "DEBUG")
        
        urllib.request.urlretrieve(url, destination, reporthook=download_progress)
        log(f"Successfully downloaded {description}", "DEBUG")
        return True
        
    except Exception as e:
        log(f"Failed to download {description}: {e}", "NORMAL")
        return False

def extract_ffmpeg(archive_path, tools_dir):
    """Extract FFmpeg from downloaded archive."""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: Extract from zip
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Find ffmpeg.exe in the archive
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('ffmpeg.exe'):
                        # Extract to tools directory
                        target_path = os.path.join(tools_dir, FFMPEG_FILENAME)
                        with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                        log("Extracted ffmpeg.exe from archive", "DEBUG")
                        return True
                        
        elif system == "darwin":
            # macOS: Extract from zip
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Extract ffmpeg binary
                zip_ref.extract('ffmpeg', tools_dir)
                
        elif system == "linux":
            # Linux: Extract from tar.xz
            import tarfile
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                # Find ffmpeg in the archive
                for member in tar_ref.getmembers():
                    if member.name.endswith('ffmpeg') and member.isfile():
                        # Extract to tools directory
                        member.name = FFMPEG_FILENAME
                        tar_ref.extract(member, tools_dir)
                        log("Extracted ffmpeg from archive", "DEBUG")
                        return True
                        
        # Make executable on Unix-like systems
        if system in ["darwin", "linux"]:
            ffmpeg_path = os.path.join(tools_dir, FFMPEG_FILENAME)
            os.chmod(ffmpeg_path, os.stat(ffmpeg_path).st_mode | stat.S_IEXEC)
            
        return True
        
    except Exception as e:
        log(f"Failed to extract FFmpeg: {e}", "NORMAL")
        return False

def download_ytdlp(tools_dir):
    """Download yt-dlp executable."""
    ytdlp_path = os.path.join(tools_dir, YTDLP_FILENAME)
    
    # Skip if already exists and works
    if os.path.exists(ytdlp_path) and verify_tool(ytdlp_path, ["--version"]):
        log("yt-dlp already exists and works", "DEBUG")
        return True
    
    # Download appropriate version
    url = YTDLP_URL_WIN if os.name == 'nt' else YTDLP_URL
    
    if download_file(url, ytdlp_path, "yt-dlp"):
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(ytdlp_path, os.stat(ytdlp_path).st_mode | stat.S_IEXEC)
        return True
    
    return False

def download_ffmpeg(tools_dir):
    """Download FFmpeg executable."""
    ffmpeg_path = os.path.join(tools_dir, FFMPEG_FILENAME)
    
    # Skip if already exists and works
    if os.path.exists(ffmpeg_path) and verify_tool(ffmpeg_path, ["-version"]):
        log("FFmpeg already exists and works", "DEBUG")
        return True
    
    # Get platform-specific URL
    system = platform.system().lower()
    if system == "windows":
        system = "win32"
    elif system == "darwin":
        system = "darwin"
    else:
        system = "linux"
    
    if system not in FFMPEG_URLS:
        log(f"Unsupported platform for FFmpeg: {system}", "NORMAL")
        return False
    
    # Download archive
    archive_ext = ".zip" if system in ["win32", "darwin"] else ".tar.xz"
    archive_path = os.path.join(tools_dir, f"ffmpeg_temp{archive_ext}")
    
    if download_file(FFMPEG_URLS[system], archive_path, "FFmpeg"):
        # Extract FFmpeg
        if extract_ffmpeg(archive_path, tools_dir):
            # Clean up archive
            try:
                os.remove(archive_path)
            except:
                pass
            return True
    
    return False

def verify_tool(tool_path, test_args):
    """Verify that a tool works by running it with test arguments."""
    try:
        # Prepare subprocess arguments
        startupinfo = None
        if os.name == 'nt':
            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Run tool with test arguments
        result = subprocess.run(
            [tool_path] + test_args,
            capture_output=True,
            startupinfo=startupinfo,
            timeout=5
        )
        
        success = result.returncode == 0
        if success:
            log(f"Tool verified: {os.path.basename(tool_path)}", "DEBUG")
        else:
            log(f"Tool verification failed: {os.path.basename(tool_path)}", "DEBUG")
            
        return success
        
    except Exception as e:
        log(f"Tool verification error for {tool_path}: {e}", "DEBUG")
        return False

def setup_tools():
    """Download and verify required tools."""
    global tools_ready, tools_logged_waiting
    
    # Log waiting message only once
    if not tools_logged_waiting:
        log("Waiting for tools to be ready. Please be patient, downloading FFmpeg may take several minutes.")
        tools_logged_waiting = True
    
    # Ensure tools directory exists
    tools_dir = get_tools_path()
    os.makedirs(tools_dir, exist_ok=True)
    
    # Download yt-dlp
    ytdlp_success = download_ytdlp(tools_dir)
    if not ytdlp_success:
        log("Failed to setup yt-dlp, will retry in 60 seconds", "DEBUG")
        return False
    
    # Download FFmpeg
    ffmpeg_success = download_ffmpeg(tools_dir)
    if not ffmpeg_success:
        log("Failed to setup FFmpeg, will retry in 60 seconds", "DEBUG")
        return False
    
    # Verify both tools work
    ytdlp_path = get_ytdlp_path()
    ffmpeg_path = get_ffmpeg_path()
    
    if verify_tool(ytdlp_path, ["--version"]) and verify_tool(ffmpeg_path, ["-version"]):
        with state_lock:
            tools_ready = True
        log("All tools are ready and verified!", "NORMAL")
        return True
    else:
        log("Tool verification failed, will retry in 60 seconds", "DEBUG")
        return False

def tools_setup_worker():
    """Background thread for setting up tools."""
    global stop_threads
    
    while not stop_threads:
        try:
            # Ensure cache directory exists
            if not ensure_cache_directory():
                time.sleep(TOOLS_CHECK_INTERVAL)
                continue
            
            # Try to setup tools
            if setup_tools():
                # Tools are ready, exit loop
                break
            
            # Wait before retry
            log(f"Retrying tool setup in {TOOLS_CHECK_INTERVAL} seconds...", "DEBUG")
            
            # Sleep in small increments to check stop_threads
            for _ in range(TOOLS_CHECK_INTERVAL):
                if stop_threads:
                    break
                time.sleep(1)
                
        except Exception as e:
            log(f"Error in tools setup: {e}", "NORMAL")
            time.sleep(TOOLS_CHECK_INTERVAL)
    
    log("Tools setup thread exiting", "DEBUG")

# ===== OBS SCRIPT INTERFACE =====
def script_description():
    """Return script description for OBS."""
    return __doc__.strip()

def script_properties():
    """Define script properties shown in OBS UI."""
    props = obs.obs_properties_create()
    
    # Playlist URL text field
    obs.obs_properties_add_text(
        props, 
        "playlist_url", 
        "YouTube Playlist URL", 
        obs.OBS_TEXT_DEFAULT
    )
    
    # Cache directory path field
    obs.obs_properties_add_path(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_PATH_DIRECTORY,
        None,
        DEFAULT_CACHE_DIR
    )
    
    # Sync Now button
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # DEBUG level checkbox
    obs.obs_properties_add_bool(
        props,
        "debug_enabled",
        "Enable Debug Logging"
    )
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    obs.obs_data_set_default_string(settings, "playlist_url", DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", DEFAULT_CACHE_DIR)
    obs.obs_data_set_default_bool(settings, "debug_enabled", True)

def script_update(settings):
    """Called when script properties are updated."""
    global playlist_url, cache_dir, debug_enabled
    
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    debug_enabled = obs.obs_data_get_bool(settings, "debug_enabled")
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}, Debug: {debug_enabled}", "DEBUG")

def script_load(settings):
    """Called when script is loaded."""
    global stop_threads
    stop_threads = False
    
    log("Script loading...")
    
    # Apply initial settings
    script_update(settings)
    
    # Schedule scene verification after 3 seconds
    obs.timer_add(verify_scene_setup, SCENE_CHECK_DELAY)
    
    # Start worker threads
    start_worker_threads()
    
    # Register frontend event callbacks
    obs.obs_frontend_add_event_callback(on_frontend_event)
    
    log("Script loaded successfully")

def script_unload():
    """Called when script is unloaded."""
    global stop_threads
    
    log("Script unloading...")
    
    # Signal threads to stop
    stop_threads = True
    
    # Stop all worker threads
    stop_worker_threads()
    
    # Remove timers
    obs.timer_remove(verify_scene_setup)
    obs.timer_remove(playback_controller)
    
    log("Script unloaded")

# ===== CALLBACK FUNCTIONS =====
def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    log("Manual sync requested")
    
    # Check if tools are ready
    with state_lock:
        if not tools_ready:
            log("Cannot sync - tools not ready yet", "NORMAL")
            return True
    
    # TODO: Trigger playlist sync
    return True

def on_frontend_event(event):
    """Handle OBS frontend events."""
    global scene_active
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        # Check if our scene is active
        current_scene = obs.obs_frontend_get_current_scene()
        if current_scene:
            scene_name = obs.obs_source_get_name(current_scene)
            scene_active = (scene_name == SCENE_NAME)
            log(f"Scene changed to: {scene_name}, Active: {scene_active}", "DEBUG")
            obs.obs_source_release(current_scene)

def verify_scene_setup():
    """Verify that required scene and sources exist."""
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    if not scene_source:
        log(f"ERROR: Required scene '{SCENE_NAME}' not found! Please create it.", "NORMAL")
        return
    
    scene = obs.obs_scene_from_source(scene_source)
    if scene:
        # Check for required sources
        media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        
        if not media_source:
            log(f"WARNING: Media Source '{MEDIA_SOURCE_NAME}' not found in scene", "NORMAL")
        else:
            obs.obs_source_release(media_source)
            
        if not text_source:
            log(f"WARNING: Text Source '{TEXT_SOURCE_NAME}' not found in scene", "NORMAL")
        else:
            obs.obs_source_release(text_source)
    
    obs.obs_source_release(scene_source)
    
    # Remove this timer - only run once
    obs.timer_remove(verify_scene_setup)

def playback_controller():
    """Main playback controller - runs on main thread."""
    # TODO: Implement playback logic
    pass

# ===== WORKER THREAD STARTERS =====
def start_worker_threads():
    """Start all background worker threads."""
    global tools_thread, playlist_sync_thread, download_worker_thread
    global normalization_worker_thread, metadata_worker_thread
    
    log("Starting worker threads...")
    
    # Start tools setup thread first
    tools_thread = threading.Thread(target=tools_setup_worker, daemon=True)
    tools_thread.start()
    
    # TODO: Start other worker threads
    # playlist_sync_thread = threading.Thread(target=playlist_sync_worker, daemon=True)
    # download_worker_thread = threading.Thread(target=download_worker, daemon=True)
    # normalization_worker_thread = threading.Thread(target=normalization_worker, daemon=True)
    # metadata_worker_thread = threading.Thread(target=metadata_worker, daemon=True)
    
    log("Worker threads started", "DEBUG")

def stop_worker_threads():
    """Stop all background worker threads."""
    global tools_thread
    
    log("Stopping worker threads...")
    
    # Wait for threads to finish (with timeout)
    if tools_thread and tools_thread.is_alive():
        tools_thread.join(timeout=5)
    
    log("Worker threads stopped", "DEBUG")

# ===== WORKER THREAD PLACEHOLDERS =====
def playlist_sync_worker():
    """Background thread for playlist synchronization."""
    global stop_threads
    
    while not stop_threads:
        # Wait for tools to be ready
        with state_lock:
            if not tools_ready:
                time.sleep(1)
                continue
        
        # TODO: Implement in Phase 3
        time.sleep(1)

def download_worker():
    """Background thread for video downloads."""
    global stop_threads
    
    while not stop_threads:
        # Wait for tools to be ready
        with state_lock:
            if not tools_ready:
                time.sleep(1)
                continue
        
        # TODO: Implement in Phase 3
        time.sleep(1)

def normalization_worker():
    """Background thread for audio normalization."""
    global stop_threads
    
    while not stop_threads:
        # Wait for tools to be ready
        with state_lock:
            if not tools_ready:
                time.sleep(1)
                continue
        
        # TODO: Implement in Phase 5
        time.sleep(1)

def metadata_worker():
    """Background thread for metadata retrieval."""
    global stop_threads
    
    while not stop_threads:
        # TODO: Implement in Phase 7
        time.sleep(1)

# ===== UTILITY FUNCTIONS =====
def ensure_cache_directory():
    """Ensure cache directory exists."""
    try:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(cache_dir, TOOLS_SUBDIR)).mkdir(exist_ok=True)
        log(f"Cache directory ready: {cache_dir}", "DEBUG")
        return True
    except Exception as e:
        log(f"Failed to create cache directory: {e}", "NORMAL")
        return False

def get_tools_path():
    """Get path to tools directory."""
    return os.path.join(cache_dir, TOOLS_SUBDIR)

def get_ytdlp_path():
    """Get path to yt-dlp executable."""
    return os.path.join(get_tools_path(), YTDLP_FILENAME)

def get_ffmpeg_path():
    """Get path to ffmpeg executable."""
    return os.path.join(get_tools_path(), FFMPEG_FILENAME)
