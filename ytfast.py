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
import re
import random
import shutil
import unicodedata
import string

# ===== MODULE-LEVEL CONSTANTS =====
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U"
# Set default cache dir to script location + scriptname-cache subfolder
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]  # Get name without .py extension
DEFAULT_CACHE_DIR = os.path.join(SCRIPT_DIR, f"{SCRIPT_NAME}-cache")
SCENE_NAME = SCRIPT_NAME  # Scene name matches script filename without extension
MEDIA_SOURCE_NAME = "video"
TEXT_SOURCE_NAME = "title"
TOOLS_SUBDIR = "tools"
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
# REMOVED SYNC_INTERVAL - No periodic sync per requirements
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second in milliseconds
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
MAX_RESOLUTION = "1440"
TOOLS_CHECK_INTERVAL = 60  # Retry tools download every 60 seconds
ACOUSTID_API_KEY = "M6o6ia3dKu"  # AcoustID API key for metadata

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
process_videos_thread = None  # Changed from multiple workers to single serial processor

# Synchronization primitives
state_lock = threading.Lock()
video_queue = queue.Queue()  # Queue for videos to process
sync_event = threading.Event()  # Signal for manual sync

# State flags
tools_ready = False
tools_logged_waiting = False
scene_active = False
is_playing = False
current_video_path = None
stop_threads = False
sync_on_startup_done = False  # Track if startup sync has been done

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
        
        # Track which percentages we've already logged
        logged_percentages = set()
        
        # Download with progress
        def download_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                
                # Log at 0%, 25%, 50%, 75%, and 100% milestones only
                milestone = None
                if percent >= 100 and 100 not in logged_percentages:
                    milestone = 100
                elif percent >= 75 and 75 not in logged_percentages:
                    milestone = 75
                elif percent >= 50 and 50 not in logged_percentages:
                    milestone = 50
                elif percent >= 25 and 25 not in logged_percentages:
                    milestone = 25
                elif percent >= 0 and 0 not in logged_percentages:
                    milestone = 0
                
                if milestone is not None:
                    log(f"Downloading {description}: {milestone}%", "DEBUG")
                    logged_percentages.add(milestone)
        
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
                # Tools are ready, trigger startup sync
                log("Tools ready, triggering startup sync", "DEBUG")
                trigger_startup_sync()
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

def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    global sync_on_startup_done
    
    with state_lock:
        if sync_on_startup_done:
            return
        sync_on_startup_done = True
    
    log("Starting one-time playlist sync on startup", "NORMAL")
    sync_event.set()  # Signal playlist sync thread to run

# ===== PLAYLIST SYNC FUNCTIONS =====
def fetch_playlist_with_ytdlp(playlist_url):
    """Fetch playlist information using yt-dlp."""
    try:
        ytdlp_path = get_ytdlp_path()
        
        # Prepare command
        cmd = [
            ytdlp_path,
            '--flat-playlist',
            '--dump-json',
            '--no-warnings',
            playlist_url
        ]
        
        # Run command with hidden window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=30
        )
        
        if result.returncode != 0:
            log(f"yt-dlp failed: {result.stderr}", "NORMAL")
            return []
        
        # Parse JSON output (one JSON object per line)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    videos.append({
                        'id': video_data.get('id', ''),
                        'title': video_data.get('title', 'Unknown'),
                        'duration': video_data.get('duration', 0)
                    })
                except json.JSONDecodeError:
                    continue
        
        log(f"Fetched {len(videos)} videos from playlist", "NORMAL")
        return videos
        
    except Exception as e:
        log(f"Error fetching playlist: {e}", "NORMAL")
        return []

def cleanup_old_videos():
    """Remove videos no longer in playlist (except currently playing)."""
    try:
        with state_lock:
            current_ids = playlist_video_ids.copy()
            cached_ids = set(cached_videos.keys())
            playing = current_video_path
        
        # Find videos to remove
        to_remove = cached_ids - current_ids
        
        for video_id in to_remove:
            video_info = cached_videos.get(video_id)
            if video_info and video_info['path'] != playing:
                try:
                    if os.path.exists(video_info['path']):
                        os.remove(video_info['path'])
                        log(f"Removed old video: {video_info['path']}", "DEBUG")
                    
                    with state_lock:
                        del cached_videos[video_id]
                except Exception as e:
                    log(f"Error removing old video: {e}", "DEBUG")
                    
    except Exception as e:
        log(f"Error in cleanup_old_videos: {e}", "DEBUG")

# ===== METADATA FUNCTIONS =====
def get_metadata(filepath, yt_title):
    """Get song and artist metadata using AcoustID or YouTube title."""
    # Try AcoustID first
    try:
        song, artist = get_acoustid_metadata(filepath)
        if song and artist:
            log(f"YT: '{yt_title}' → Song: '{song}', Artist: '{artist}'")
            return song, artist
    except Exception as e:
        log(f"AcoustID failed: {e}", "DEBUG")
    
    # Fallback to parsing YouTube title
    song, artist = parse_youtube_title(yt_title)
    log(f"YT: '{yt_title}' → Song: '{song}', Artist: '{artist}'")
    return song, artist

def get_acoustid_metadata(filepath):
    """Query AcoustID for metadata using audio fingerprint."""
    try:
        # Use fpcalc (comes with AcoustID) to generate fingerprint
        # For now, returning None to use fallback
        # Full implementation would require fpcalc binary
        return None, None
    except Exception:
        return None, None

def parse_youtube_title(title):
    """Parse YouTube title to extract artist and song."""
    # Common patterns in YouTube titles
    patterns = [
        (r'^(.*?)\s*-\s*(.*)$', 'hyphen'),  # Artist - Song
        (r'^(.*?)\s*\|\s*(.*)$', 'pipe'),   # Artist | Song
        (r'^(.*?)\s*:\s*(.*)$', 'colon'),   # Artist : Song
    ]
    
    for pattern, name in patterns:
        match = re.match(pattern, title)
        if match:
            artist = match.group(1).strip()
            song = match.group(2).strip()
            
            # Clean up common suffixes
            song = re.sub(r'\s*\([^)]*\)$', '', song)  # Remove (Official Video) etc
            song = re.sub(r'\s*\[[^\]]*\]$', '', song)  # Remove [HD] etc
            
            return song, artist
    
    # If no pattern matches, use title as song name
    return title, "Unknown Artist"

# ===== FILE MANAGEMENT FUNCTIONS =====
def sanitize_filename(song, artist, video_id):
    """Create safe filename from metadata."""
    def clean_string(s):
        # Remove non-ASCII characters
        s = unicodedata.normalize('NFKD', s)
        s = s.encode('ASCII', 'ignore').decode('ASCII')
        
        # Replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            s = s.replace(char, '_')
        
        # Remove multiple underscores and trim
        s = re.sub(r'_+', '_', s)
        s = s.strip('_. ')
        
        # Limit length
        return s[:50] if s else "unknown"
    
    clean_song = clean_string(song)
    clean_artist = clean_string(artist)
    
    return f"{clean_song}_{clean_artist}_{video_id}_normalized.mp4"

def get_cached_videos():
    """Scan cache directory for normalized videos."""
    videos = {}
    
    try:
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return videos
        
        # Look for normalized mp4 files
        for file_path in cache_path.glob("*_normalized.mp4"):
            # Extract video ID from filename
            match = re.search(r'_([a-zA-Z0-9_-]{11})_normalized\.mp4$', file_path.name)
            if match:
                video_id = match.group(1)
                
                # Extract metadata from filename
                parts = file_path.stem.replace('_normalized', '').split('_')
                if len(parts) >= 3:
                    song = parts[0]
                    artist = parts[1]
                    
                    videos[video_id] = {
                        "path": str(file_path),
                        "song": song,
                        "artist": artist,
                        "normalized": True
                    }
        
        log(f"Found {len(videos)} cached videos", "DEBUG")
        
    except Exception as e:
        log(f"Error scanning cache: {e}", "DEBUG")
    
    return videos

def cleanup_cache():
    """Remove duplicates and temporary files."""
    try:
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return
        
        # Remove .part files
        for part_file in cache_path.glob("*.part"):
            try:
                part_file.unlink()
                log(f"Removed partial file: {part_file.name}", "DEBUG")
            except Exception:
                pass
        
        # Remove temporary files
        for temp_file in cache_path.glob("*_temp.mp4"):
            try:
                temp_file.unlink()
                log(f"Removed temp file: {temp_file.name}", "DEBUG")
            except Exception:
                pass
                
        # Find and remove duplicates (keep newest)
        video_groups = {}
        for file_path in cache_path.glob("*_normalized.mp4"):
            match = re.search(r'_([a-zA-Z0-9_-]{11})_normalized\.mp4$', file_path.name)
            if match:
                video_id = match.group(1)
                if video_id not in video_groups:
                    video_groups[video_id] = []
                video_groups[video_id].append(file_path)
        
        # Remove older duplicates
        for video_id, paths in video_groups.items():
            if len(paths) > 1:
                # Sort by modification time, keep newest
                paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                for old_path in paths[1:]:
                    try:
                        old_path.unlink()
                        log(f"Removed duplicate: {old_path.name}", "DEBUG")
                    except Exception:
                        pass
                        
    except Exception as e:
        log(f"Error in cleanup_cache: {e}", "DEBUG")

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
    
    # Cache directory text field - editable for easy customization
    obs.obs_properties_add_text(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_TEXT_DEFAULT
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
    
    # Clean up cache on startup
    cleanup_cache()
    
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
    
    # Trigger playlist sync
    sync_event.set()
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
    global tools_thread, playlist_sync_thread, process_videos_thread
    
    log("Starting worker threads...")
    
    # Start tools setup thread first
    tools_thread = threading.Thread(target=tools_setup_worker, daemon=True)
    tools_thread.start()
    
    # Start playlist sync thread
    playlist_sync_thread = threading.Thread(target=playlist_sync_worker, daemon=True)
    playlist_sync_thread.start()
    
    # Start video processing thread (will be implemented in Phase 4)
    # process_videos_thread = threading.Thread(target=process_videos_worker, daemon=True)
    # process_videos_thread.start()
    
    log("Worker threads started", "DEBUG")

def stop_worker_threads():
    """Stop all background worker threads."""
    global tools_thread, playlist_sync_thread
    
    log("Stopping worker threads...")
    
    # Signal threads to stop
    sync_event.set()  # Wake up sync thread
    
    # Wait for threads to finish (with timeout)
    if tools_thread and tools_thread.is_alive():
        tools_thread.join(timeout=5)
    
    if playlist_sync_thread and playlist_sync_thread.is_alive():
        playlist_sync_thread.join(timeout=5)
    
    log("Worker threads stopped", "DEBUG")

# ===== WORKER THREADS =====
def playlist_sync_worker():
    """Background thread for playlist synchronization - NO PERIODIC SYNC."""
    global stop_threads
    
    while not stop_threads:
        # Wait for sync signal or timeout
        if not sync_event.wait(timeout=1):
            continue
        
        # Clear the event
        sync_event.clear()
        
        # Check if we should exit
        if stop_threads:
            break
            
        # Wait for tools to be ready
        with state_lock:
            if not tools_ready:
                log("Sync requested but tools not ready", "DEBUG")
                continue
        
        log("Starting playlist synchronization", "NORMAL")
        
        try:
            # Clean up cache first
            cleanup_cache()
            
            # Scan for existing videos
            with state_lock:
                cached_videos.clear()
                cached_videos.update(get_cached_videos())
            
            # Fetch playlist
            videos = fetch_playlist_with_ytdlp(playlist_url)
            
            if not videos:
                log("No videos found in playlist or fetch failed", "NORMAL")
                continue
            
            # Update playlist video IDs
            with state_lock:
                playlist_video_ids.clear()
                playlist_video_ids.update(video['id'] for video in videos)
            
            # Queue videos for processing (skip already cached)
            queued_count = 0
            for video in videos:
                with state_lock:
                    if video['id'] not in cached_videos:
                        video_queue.put(video)
                        queued_count += 1
            
            log(f"Queued {queued_count} new videos for processing", "NORMAL")
            
            # Clean up old videos
            cleanup_old_videos()
            
        except Exception as e:
            log(f"Error in playlist sync: {e}", "NORMAL")
    
    log("Playlist sync thread exiting", "DEBUG")

def process_videos_worker():
    """Process videos serially - download, metadata, normalize."""
    # TODO: Implement in Phase 4
    pass

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