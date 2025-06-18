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
import urllib.parse
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
SCRIPT_VERSION = "1.8.2"  # Universal song title cleaning applied to all metadata sources (AcoustID, iTunes, title parsing)
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
FPCALC_FILENAME = "fpcalc.exe" if os.name == 'nt' else "fpcalc"
# REMOVED SYNC_INTERVAL - No periodic sync per requirements
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second in milliseconds
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
MAX_RESOLUTION = "1440"
TOOLS_CHECK_INTERVAL = 60  # Retry tools download every 60 seconds
ACOUSTID_API_KEY = "RXS1uld515"  # AcoustID API key for metadata
ACOUSTID_ENABLED = True  # Toggle to enable/disable AcoustID lookups
DOWNLOAD_TIMEOUT = 600  # 10 minutes timeout for downloads
NORMALIZE_TIMEOUT = 300  # 5 minutes timeout for normalization

# URLs for tool downloads
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_WIN = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# FFmpeg URLs by platform
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# fpcalc (Chromaprint) URLs by platform
FPCALC_URLS = {
    "win32": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-windows-x86_64.zip",
    "darwin": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-macos-x86_64.tar.gz",
    "linux": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-linux-x86_64.tar.gz"
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

# Progress tracking
download_progress_milestones = {}  # Track logged milestones per video

# ===== LOGGING HELPER =====
def log(message):
    """Log messages with timestamp and script identifier."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # In background threads, OBS shows [Unknown Script], so we add our script name
    # This helps distinguish between multiple script instances
    thread_name = threading.current_thread().name
    if thread_name != "MainThread":
        # For background threads, include script name in message
        print(f"[{timestamp}] [{SCRIPT_NAME}] {message}")
    else:
        # For main thread, OBS already shows script name
        print(f"[{timestamp}] {message}")

# ===== TOOL MANAGEMENT FUNCTIONS =====
def download_file(url, destination, description="file"):
    """Download a file from URL to destination."""
    try:
        log(f"Downloading {description} from {url}")
        
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
                    log(f"Downloading {description}: {milestone}%")
                    logged_percentages.add(milestone)
        
        urllib.request.urlretrieve(url, destination, reporthook=download_progress)
        log(f"Successfully downloaded {description}")
        return True
        
    except Exception as e:
        log(f"Failed to download {description}: {e}")
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
                        log("Extracted ffmpeg.exe from archive")
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
                        log("Extracted ffmpeg from archive")
                        return True
                        
        # Make executable on Unix-like systems
        if system in ["darwin", "linux"]:
            ffmpeg_path = os.path.join(tools_dir, FFMPEG_FILENAME)
            os.chmod(ffmpeg_path, os.stat(ffmpeg_path).st_mode | stat.S_IEXEC)
            
        return True
        
    except Exception as e:
        log(f"Failed to extract FFmpeg: {e}")
        return False

def extract_fpcalc(archive_path, tools_dir):
    """Extract fpcalc from downloaded archive."""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: Extract from zip
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Find fpcalc.exe in the archive
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('fpcalc.exe'):
                        # Extract to tools directory
                        target_path = os.path.join(tools_dir, FPCALC_FILENAME)
                        with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                        log("Extracted fpcalc.exe from archive")
                        return True
                        
        elif system in ["darwin", "linux"]:
            # macOS/Linux: Extract from tar.gz
            import tarfile
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                # Find fpcalc in the archive
                for member in tar_ref.getmembers():
                    if member.name.endswith('fpcalc') and member.isfile():
                        # Extract to tools directory
                        member.name = FPCALC_FILENAME
                        tar_ref.extract(member, tools_dir)
                        log("Extracted fpcalc from archive")
                        return True
                        
        # Make executable on Unix-like systems
        if system in ["darwin", "linux"]:
            fpcalc_path = os.path.join(tools_dir, FPCALC_FILENAME)
            os.chmod(fpcalc_path, os.stat(fpcalc_path).st_mode | stat.S_IEXEC)
            
        return True
        
    except Exception as e:
        log(f"Failed to extract fpcalc: {e}")
        return False

def download_ytdlp(tools_dir):
    """Download yt-dlp executable."""
    ytdlp_path = os.path.join(tools_dir, YTDLP_FILENAME)
    
    # Skip if already exists and works
    if os.path.exists(ytdlp_path) and verify_tool(ytdlp_path, ["--version"]):
        log("yt-dlp already exists and works")
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
        log("FFmpeg already exists and works")
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
        log(f"Unsupported platform for FFmpeg: {system}")
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

def download_fpcalc(tools_dir):
    """Download fpcalc executable for AcoustID fingerprinting."""
    fpcalc_path = os.path.join(tools_dir, FPCALC_FILENAME)
    
    # Skip if already exists and works
    if os.path.exists(fpcalc_path) and verify_tool(fpcalc_path, ["-version"]):
        log("fpcalc already exists and works")
        return True
    
    # Get platform-specific URL
    system = platform.system().lower()
    if system == "windows":
        system = "win32"
    elif system == "darwin":
        system = "darwin"
    else:
        system = "linux"
    
    if system not in FPCALC_URLS:
        log(f"Unsupported platform for fpcalc: {system}")
        return False
    
    # Download archive
    archive_ext = ".zip" if system == "win32" else ".tar.gz"
    archive_path = os.path.join(tools_dir, f"fpcalc_temp{archive_ext}")
    
    if download_file(FPCALC_URLS[system], archive_path, "fpcalc"):
        # Extract fpcalc
        if extract_fpcalc(archive_path, tools_dir):
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
            log(f"Tool verified: {os.path.basename(tool_path)}")
        else:
            log(f"Tool verification failed: {os.path.basename(tool_path)}")
            
        return success
        
    except Exception as e:
        log(f"Tool verification error for {tool_path}: {e}")
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
    
    # Download yt-dlp (already verifies internally)
    ytdlp_success = download_ytdlp(tools_dir)
    if not ytdlp_success:
        log("Failed to setup yt-dlp, will retry in 60 seconds")
        return False
    
    # Download FFmpeg (already verifies internally)
    ffmpeg_success = download_ffmpeg(tools_dir)
    if not ffmpeg_success:
        log("Failed to setup FFmpeg, will retry in 60 seconds")
        return False
    
    # Download fpcalc (already verifies internally)
    fpcalc_success = download_fpcalc(tools_dir)
    if not fpcalc_success:
        log("Failed to setup fpcalc, will retry in 60 seconds")
        return False
    
    # All tools downloaded and verified successfully
    with state_lock:
        tools_ready = True
    log("All tools are ready and verified!")
    return True

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
                log("Tools setup complete")
                trigger_startup_sync()
                break
            
            # Wait before retry
            log(f"Retrying tool setup in {TOOLS_CHECK_INTERVAL} seconds...")
            
            # Sleep in small increments to check stop_threads
            for _ in range(TOOLS_CHECK_INTERVAL):
                if stop_threads:
                    break
                time.sleep(1)
                
        except Exception as e:
            log(f"Error in tools setup: {e}")
            time.sleep(TOOLS_CHECK_INTERVAL)
    
    log("Tools setup thread exiting")

def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    global sync_on_startup_done
    
    with state_lock:
        if sync_on_startup_done:
            return
        sync_on_startup_done = True
    
    log("Starting one-time playlist sync on startup")
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
            log(f"yt-dlp failed: {result.stderr}")
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
        
        log(f"Fetched {len(videos)} videos from playlist")
        return videos
        
    except Exception as e:
        log(f"Error fetching playlist: {e}")
        return []

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
                log("Sync requested but tools not ready")
                continue
        
        log("Starting playlist synchronization")
        
        try:
            # Fetch playlist
            videos = fetch_playlist_with_ytdlp(playlist_url)
            
            if not videos:
                log("No videos found in playlist or fetch failed")
                continue
            
            # Update playlist video IDs
            with state_lock:
                playlist_video_ids.clear()
                playlist_video_ids.update(video['id'] for video in videos)
            
            # Queue videos for processing
            queued_count = 0
            for video in videos:
                video_queue.put(video)
                queued_count += 1
            
            log(f"Queued {queued_count} videos for processing")
            
        except Exception as e:
            log(f"Error in playlist sync: {e}")
    
    log("Playlist sync thread exiting")

# ===== VIDEO DOWNLOAD FUNCTIONS =====
def download_video(video_id, title):
    """Download video to temporary file."""
    output_path = os.path.join(cache_dir, f"{video_id}_temp.mp4")
    
    # Remove existing temp file
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            log(f"Removed existing temp file: {output_path}")
        except Exception as e:
            log(f"Error removing temp file: {e}")
    
    try:
        # First, get video info to log quality
        info_cmd = [
            get_ytdlp_path(),
            '-f', f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]/best',
            '--print', '%(width)s,%(height)s,%(fps)s,%(vcodec)s,%(acodec)s',
            '--no-warnings',
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        
        # Get video info
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        try:
            info_result = subprocess.run(
                info_cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=10
            )
            
            if info_result.returncode == 0 and info_result.stdout.strip():
                info_parts = info_result.stdout.strip().split(',')
                if len(info_parts) >= 2:
                    width, height = info_parts[0], info_parts[1]
                    fps = info_parts[2] if len(info_parts) > 2 else "?"
                    vcodec = info_parts[3] if len(info_parts) > 3 else "?"
                    acodec = info_parts[4] if len(info_parts) > 4 else "?"
                    log(f"Video quality: {width}x{height} @ {fps}fps, video: {vcodec}, audio: {acodec}")
        except Exception as e:
            log(f"Could not get video info: {e}")
        
        # Now download the video
        cmd = [
            get_ytdlp_path(),
            '-f', f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]/best',
            '--merge-output-format', 'mp4',
            '--ffmpeg-location', get_ffmpeg_path(),
            '--no-playlist',
            '--no-warnings',
            '--progress',
            '--newline',
            '-o', output_path,
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        
        log(f"Starting download: {title} ({video_id})")
        
        # Prepare subprocess with hidden window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Reset progress tracking for this video
        global download_progress_milestones
        download_progress_milestones[video_id] = set()
        
        # Start download process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        
        # Parse progress output
        for line in process.stdout:
            if '[download]' in line:
                # Skip fragment/part download progress lines
                if any(skip in line.lower() for skip in ['fragment', 'downloading', 'destination:']):
                    continue
                # Only parse percentage lines that show actual download progress
                if '%' in line and 'of' in line:
                    parse_progress(line, video_id, title)
        
        # Wait for process to complete
        process.wait(timeout=DOWNLOAD_TIMEOUT)
        
        if process.returncode != 0:
            log(f"Download failed for {title}: return code {process.returncode}")
            return None
        
        # Verify file exists and has size
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            log(f"Downloaded successfully: {title} ({file_size_mb:.1f} MB)")
            return output_path
        else:
            log(f"Download failed - file missing or empty: {title}")
            return None
            
    except subprocess.TimeoutExpired:
        log(f"Download timeout for {title} after {DOWNLOAD_TIMEOUT} seconds")
        try:
            process.kill()
        except:
            pass
        return None
    except Exception as e:
        log(f"Error downloading {title}: {e}")
        return None
    finally:
        # Clean up progress tracking
        download_progress_milestones.pop(video_id, None)

def parse_progress(line, video_id, title):
    """Parse yt-dlp progress output and log at milestones."""
    # Look for: [download]  XX.X% of ~XXX.XXMiB at XXX.XXKiB/s
    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
    if match:
        percent = float(match.group(1))
        
        # Get milestone set for this video
        milestones = download_progress_milestones.get(video_id, set())
        
        # If we've already logged 50%, ignore further progress
        if 50 in milestones:
            return
        
        # Log only at 50%
        if percent >= 50 and 50 not in milestones:
            log(f"Downloading {title}: 50%")
            milestones.add(50)
            download_progress_milestones[video_id] = milestones

# ===== METADATA EXTRACTION FUNCTIONS =====
def search_itunes_metadata(search_query, expected_artist=None):
    """
    Search iTunes API for song metadata with improved matching.
    Returns (song, artist) or (None, None)
    """
    try:
        original_query = search_query
        
        # Clean up search query
        search_query = search_query.lower()
        
        # Remove common video suffixes
        for suffix in ['official music video', 'official video', 'lyrics', 'live', 
                       'worship together session', 'official', 'music video', 'hd', '4k',
                       '+ the choir room', 'the choir room', 'video oficial', '(video oficial)',
                       '[official]', '(official)', 'en vivo', '(en vivo)', 'worship cover',
                       'songs for church', 'live at chapel', 'revival', 'feat.', 'ft.']:
            search_query = search_query.replace(suffix, '').strip()
        
        # Replace multiple separators with spaces
        search_query = search_query.replace('//', ' ')
        search_query = search_query.replace('|', ' ')
        search_query = search_query.replace(' - ', ' ')
        
        # Remove extra whitespace
        search_query = ' '.join(search_query.split())
        
        log(f"iTunes search - Query: '{search_query}', Expected artist: '{expected_artist}'")
        
        # URL encode the search query
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&limit=25"
        
        # Make request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get('resultCount', 0) == 0:
            log("No iTunes results found")
            return None, None
        
        # Strategy 1: If we have expected artist, try strict matching first
        if expected_artist:
            best_match = find_artist_match(data['results'], expected_artist, search_query, strict=True)
            if best_match:
                song, artist = best_match
                log(f"iTunes strict match: {artist} - {song}")
                return song, artist
        
        # Strategy 2: Enhanced genre-aware matching
        best_match = find_best_itunes_match_with_validation(data['results'], search_query, expected_artist, original_query)
        if best_match:
            song, artist = best_match
            log(f"iTunes validated match: {artist} - {song}")
            return song, artist
        
        log("No suitable iTunes matches found")
        return None, None
        
    except Exception as e:
        log(f"iTunes search error: {e}")
        return None, None

def find_artist_match(results, expected_artist, search_query, strict=True):
    """Find iTunes results that match expected artist."""
    expected_artist_lower = expected_artist.lower()
    best_match = None
    best_score = 0
    
    for result in results:
        artist = result.get('artistName', '')
        song = result.get('trackName', '')
        
        if not artist or not song:
            continue
        
        artist_lower = artist.lower()
        
        # Artist similarity check
        artist_match = False
        if strict:
            # Strict: exact substring match or word subset
            if expected_artist_lower in artist_lower or artist_lower in expected_artist_lower:
                artist_match = True
            else:
                # Check if all words in expected artist are in result artist
                expected_words = set(expected_artist_lower.split())
                result_words = set(artist_lower.split())
                if expected_words and expected_words.issubset(result_words):
                    artist_match = True
        else:
            # Relaxed: any significant word overlap
            expected_words = set(w for w in expected_artist_lower.split() if len(w) > 2)
            result_words = set(w for w in artist_lower.split() if len(w) > 2)
            overlap = len(expected_words.intersection(result_words))
            if overlap > 0 and overlap >= len(expected_words) * 0.6:
                artist_match = True
        
        if not artist_match:
            continue
        
        # Score based on how well song title matches search
        song_lower = song.lower()
        search_words = set(w for w in search_query.split() if len(w) > 2)
        song_score = sum(1 for word in search_words if word in song_lower)
        
        if song_score > best_score:
            best_match = (song, artist)
            best_score = song_score
            
    return best_match

def find_best_itunes_match_with_validation(results, search_query, expected_artist=None, original_query=""):
    """Find best iTunes match with enhanced genre validation and context checking."""
    search_words = set(w for w in search_query.split() if len(w) > 2)
    
    if len(search_words) < 2:
        return None
    
    best_match = None
    best_score = 0
    
    for result in results:
        artist = result.get('artistName', '')
        song = result.get('trackName', '')
        
        if not artist or not song:
            continue
        
        # Enhanced genre/context mismatch detection
        if is_enhanced_genre_mismatch(search_query, artist.lower(), song.lower(), original_query):
            log(f"Rejected iTunes match for genre mismatch: {artist} - {song}")
            continue
        
        # Score based on word matching
        song_lower = song.lower()
        artist_lower = artist.lower()
        
        # Count matches in song title (weighted more)
        song_matches = sum(2 for word in search_words if word in song_lower)
        
        # Count matches in artist name
        artist_matches = sum(1 for word in search_words if word in artist_lower)
        
        # Bonus for artist consistency if we have expected artist
        artist_bonus = 0
        if expected_artist:
            expected_lower = expected_artist.lower()
            expected_words = set(w for w in expected_lower.split() if len(w) > 2)
            result_words = set(w for w in artist_lower.split() if len(w) > 2)
            if expected_words.intersection(result_words):
                artist_bonus = 3
        
        total_score = song_matches + artist_matches + artist_bonus
        
        # Stricter validation: Require higher threshold
        min_required = max(4, len(search_words) // 2)  # Increased threshold
        
        # Require meaningful song title overlap (not just artist name matches)
        if song_matches == 0 and artist_bonus == 0:
            continue  # Must match something in the song title or have artist consistency
        
        if total_score >= min_required and total_score > best_score:
            best_match = (song, artist)
            best_score = total_score
    
    return best_match

def is_enhanced_genre_mismatch(search_query, artist_lower, song_lower, original_query=""):
    """Enhanced genre mismatch detection with better context awareness."""
    search_lower = search_query.lower()
    original_lower = original_query.lower()
    
    # Worship/Christian music indicators (expanded)
    worship_indicators = [
        'worship', 'church', 'praise', 'glory', 'lord', 'god', 'jesus', 'christ', 'holy', 
        'prayer', 'faith', 'blessed', 'heaven', 'salvation', 'hallelujah', 'amen',
        'planetshakers', 'elevation', 'hillsong', 'bethel', 'gateway', 'lakewood',
        'revival', 'presence', 'sanctuary', 'almighty', 'sovereign', 'redeemer',
        'savior', 'emmanuel', 'hosanna', 'christian', 'gospel'
    ]
    
    # Secular genre indicators that would be clear mismatches
    secular_genres = [
        'jazz', 'funk', 'disco', 'metal', 'punk', 'rap', 'hip hop', 'techno', 
        'electronic', 'blues', 'country', 'classical', 'rock', 'pop', 'r&b'
    ]
    
    # Known problematic artist patterns
    problematic_artists = [
        'level 42',           # Jazz-funk band often matched incorrectly
        'physical presence',  # Common false match
        'worship songs on the piano',  # Generic cover artist
        'piano tribute',      # Generic tribute albums
        'instrumental',       # Generic instrumental versions
    ]
    
    # Check if search suggests worship context
    has_worship_context = any(indicator in search_lower for indicator in worship_indicators)
    has_worship_context = has_worship_context or any(indicator in original_lower for indicator in worship_indicators)
    
    # Check result text for problematic patterns
    result_text = f"{artist_lower} {song_lower}".lower()
    
    # Check for known problematic artists
    if any(problematic in result_text for problematic in problematic_artists):
        if has_worship_context:
            log(f"Genre mismatch detected: worship context with problematic artist pattern")
            return True
    
    # Check for secular genre indicators
    has_secular_genre = any(genre in result_text for genre in secular_genres)
    if has_worship_context and has_secular_genre:
        log(f"Genre mismatch detected: worship context with secular genre indicators")
        return True
    
    # Specific pattern checks
    if has_worship_context:
        # Reject "Level 42" matches for worship content
        if 'level 42' in artist_lower:
            log(f"Genre mismatch detected: Level 42 matched for worship content")
            return True
        
        # Reject piano tribute/cover albums for specific worship content
        if 'piano' in artist_lower and any(word in artist_lower for word in ['tribute', 'cover', 'instrumental']):
            # Only reject if we have specific artist expectations
            if any(artist in original_lower for artist in ['planetshakers', 'elevation', 'hillsong']):
                log(f"Genre mismatch detected: generic piano cover for specific worship artist")
                return True
    
    # Check for obvious instrumental/cover mismatches when original artist is expected
    original_words = original_lower.split()
    if any(artist in original_words for artist in ['planetshakers', 'elevation', 'hillsong', 'bethel']):
        if 'instrumental' in result_text or 'karaoke' in result_text:
            log(f"Genre mismatch detected: instrumental/karaoke version when original artist expected")
            return True
    
    return False

def parse_title_smart(title):
    """
    Smart title parser that handles various YouTube title formats.
    Returns (song, artist) or (None, None)
    """
    if not title:
        return None, None
        
    # Log original title
    log(f"Title parser - Original: '{title}'")
    
    # Clean the title
    cleaned = title.strip()
    
    # First check for special patterns that indicate artist
    # Pattern 1: "Song | Artist" or "Song | Artist feat. X"
    pipe_match = re.match(r'^([^|]+)\s*\|\s*([^|]+?)(?:\s*(?:Official|Music|Video|Live|feat\.|ft\.)|$)', cleaned, re.IGNORECASE)
    if pipe_match:
        song = pipe_match.group(1).strip()
        artist = pipe_match.group(2).strip()
        # Clean up artist name
        for suffix in ['Official Music Video', 'Official Video', 'Music Video', 'Official', 'Video', 'Live']:
            artist = re.sub(f'\\s*{suffix}.*', '', artist, flags=re.IGNORECASE)
        if song and artist and len(artist) > 2:
            song = clean_featuring_from_song(song)
            log(f"Title parser - Pipe pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Pattern 2: "Artist - Song" (most common)
    dash_match = re.match(r'^([^-]+?)\s*-\s*([^-]+?)(?:\s*\(|\s*\[|$)', cleaned)
    if dash_match:
        part1 = dash_match.group(1).strip()
        part2 = dash_match.group(2).strip()
        
        # Check if this looks like "Artist - Song" pattern
        # Usually artist names are shorter and don't contain certain keywords
        song_keywords = ['official', 'video', 'lyrics', 'live', 'feat', 'ft.', 'audio']
        if any(keyword in part2.lower() for keyword in song_keywords):
            # Part2 likely contains song + extra info
            artist = part1
            song = part2
        else:
            # Standard "Artist - Song"
            artist = part1
            song = part2
        
        # Clean up
        song = clean_featuring_from_song(song)
        # Remove video suffixes from song
        for suffix in ['Official Music Video', 'Official Video', 'Music Video', 'Official', 'Video', 'Live', 'Audio']:
            song = re.sub(f'\\s*[\\(\\[]?{suffix}[\\)\\]]?', '', song, flags=re.IGNORECASE).strip()
        
        if song and artist and len(artist) > 2:
            log(f"Title parser - Dash pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Pattern 3: Check for worship/church patterns
    worship_match = re.match(r'^(.+?)\s*\|\s*([\w\s]+?)(?:\s*\(worship.*?\))?', cleaned, re.IGNORECASE)
    if worship_match and 'worship' in cleaned.lower():
        song = worship_match.group(1).strip()
        artist = worship_match.group(2).strip()
        # Remove common suffixes
        artist = re.sub(r'\s*\(.*?\)\s*', '', artist, flags=re.IGNORECASE)
        if song and artist and len(artist) > 2:
            log(f"Title parser - Worship pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Remove common video suffixes before further parsing
    suffixes_to_remove = [
        'official music video', 'official video', 'official audio',
        'music video', 'lyrics video', 'lyric video', 'lyrics',
        'hd', '4k', 'live', 'acoustic', 'cover', 'remix',
        'feat.', 'ft.', 'featuring', '(audio)', '[audio]',
        'worship together session', 'official', 'video',
        'video oficial', '(video oficial)', 'en vivo', '(en vivo)',
        'songs for church', 'live at chapel'
    ]
    
    # Make lowercase for suffix matching
    cleaned_lower = cleaned.lower()
    for suffix in suffixes_to_remove:
        # Remove suffix with various bracket types
        for bracket in ['()', '[]', '{}']:
            pattern = f"{bracket[0]}{suffix}{bracket[1]}"
            cleaned_lower = cleaned_lower.replace(pattern, '')
        # Remove suffix at end of string
        if cleaned_lower.endswith(suffix):
            cleaned_lower = cleaned_lower[:-len(suffix)].strip()
    
    # Apply case changes back
    if len(cleaned_lower) < len(cleaned):
        cleaned = cleaned[:len(cleaned_lower)]
    
    log(f"Title parser - After cleaning: '{cleaned}'")
    
    # Try other separator patterns
    separators = [
        ' – ',     # Em dash variant
        ' — ',     # En dash variant  
        ' // ',    # Double slash
        ': ',      # Colon separator
        ' by ',    # "Song by Artist"
    ]
    
    # Check each separator
    for sep in separators:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)  # Split only on first occurrence
            if len(parts) == 2:
                part1, part2 = parts[0].strip(), parts[1].strip()
                
                if sep == ' by ':
                    # "Song by Artist" pattern
                    song, artist = part1, part2
                else:
                    # Default assumption: Artist - Song
                    artist, song = part1, part2
                
                # Clean up featuring artists from song title
                song = clean_featuring_from_song(song)
                
                if song and artist and len(artist) > 2:
                    log(f"Title parser - Found separator '{sep}': Artist='{artist}', Song='{song}'")
                    return song, artist
    
    # Pattern: Quoted song title
    quote_match = re.search(r'[""''](.*?)["'']', cleaned)
    if quote_match:
        song = quote_match.group(1)
        # Remove the quoted part to find artist
        artist = cleaned.replace(quote_match.group(0), '').strip()
        if artist and song and len(artist) > 2:
            log(f"Title parser - Quote pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Unable to parse - return None to avoid bad metadata
    log(f"Title parser - Unable to parse title reliably")
    return None, None

def clean_featuring_from_song(song):
    """
    Remove ALL bracket phrases from song title including multiple consecutive brackets.
    Handles: (feat. X), [Live], {Official}, (Audio), etc.
    """
    if not song:
        return song
    
    original_song = song
    log(f"Song title cleaning - Original: '{original_song}'")
    
    # Define bracket types and their patterns
    bracket_pairs = [
        ('(', ')'),  # Parentheses
        ('[', ']'),  # Square brackets  
        ('{', '}'),  # Curly brackets
    ]
    
    # Common annotation patterns to remove (case-insensitive)
    annotation_patterns = [
        # Featuring patterns
        r'feat\.?\s+[^)}\]]*',
        r'ft\.?\s+[^)}\]]*', 
        r'featuring\s+[^)}\]]*',
        
        # Video/audio descriptors
        r'official\s*(?:music\s*)?video',
        r'official\s*audio',
        r'music\s*video',
        r'lyric\s*video',
        r'lyrics?\s*video',
        r'lyrics?',
        r'audio',
        r'video',
        
        # Performance descriptors
        r'live',
        r'acoustic',
        r'unplugged',
        r'session',
        r'worship\s+together\s+session',
        r'en\s+vivo',
        
        # Quality descriptors
        r'hd',
        r'4k',
        r'high\s+quality',
        
        # Miscellaneous
        r'official',
        r'cover',
        r'remix',
        r'radio\s+edit',
        r'extended\s+version',
        r'choir\s+room',
        r'video\s+oficial',
    ]
    
    # Step 1: Remove complete bracket phrases that contain annotations
    cleaned = song
    iteration = 0
    max_iterations = 10  # Prevent infinite loops
    
    while iteration < max_iterations:
        iteration += 1
        original_length = len(cleaned)
        
        # For each bracket type
        for open_bracket, close_bracket in bracket_pairs:
            # Find all bracket pairs of this type
            bracket_pattern = re.escape(open_bracket) + r'([^' + re.escape(open_bracket) + re.escape(close_bracket) + r']*)' + re.escape(close_bracket)
            
            def should_remove_bracket(match):
                content = match.group(1).strip().lower()
                if not content:
                    return True  # Remove empty brackets
                
                # Check if content matches any annotation pattern
                for pattern in annotation_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return True
                
                # Check for additional numeric/year patterns
                if re.match(r'^\d{4}$', content):  # Year like (2019)
                    return True
                if re.match(r'^[0-9\s\-:]+$', content):  # Time stamps or numbers
                    return True
                
                return False
            
            # Remove matching brackets
            def replace_bracket(match):
                if should_remove_bracket(match):
                    log(f"Removing bracket phrase: '{match.group(0)}'")
                    return ''
                return match.group(0)
            
            cleaned = re.sub(bracket_pattern, replace_bracket, cleaned)
        
        # Clean up whitespace and check if we made changes
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) == original_length:
            break  # No more changes
    
    # Step 2: Remove trailing annotation phrases without brackets
    trailing_patterns = [
        r'\s+feat\.?\s+.*$',
        r'\s+ft\.?\s+.*$',
        r'\s+featuring\s+.*$',
        r'\s+official\s*(?:music\s*)?video\s*$',
        r'\s+official\s*audio\s*$',
        r'\s+music\s*video\s*$',
        r'\s+live\s*$',
        r'\s+acoustic\s*$',
        r'\s+hd\s*$',
        r'\s+4k\s*$',
    ]
    
    for pattern in trailing_patterns:
        new_cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        if new_cleaned != cleaned:
            log(f"Removing trailing phrase: '{pattern}' from '{cleaned}'")
            cleaned = new_cleaned
    
    # Step 3: Final cleanup
    cleaned = cleaned.strip()
    
    # Remove any remaining double spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove trailing punctuation that might be left behind
    cleaned = re.sub(r'[,\-\|\s]+$', '', cleaned).strip()
    
    if cleaned != original_song:
        log(f"Song title cleaned: '{original_song}' → '{cleaned}'")
    
    return cleaned or original_song  # Return original if cleaning resulted in empty string

def apply_universal_song_cleaning(song, artist, source):
    """
    Apply universal song title cleaning to metadata from ANY source.
    This is the final step that ensures ALL song titles are clean regardless of source.
    """
    if not song:
        return song, artist
    
    original_song = song
    
    # Apply the comprehensive cleaning function
    cleaned_song = clean_featuring_from_song(song)
    
    # Log the cleaning if it changed anything
    if cleaned_song != original_song:
        log(f"Universal cleaning applied to {source} result: '{original_song}' → '{cleaned_song}'")
    
    return cleaned_song, artist

def extract_metadata_from_title(title):
    """
    Enhanced title parser that tries iTunes then falls back to parsing.
    Always returns metadata - never None. This is the final fallback step.
    Returns (song, artist, source)
    """
    # First, try smart title parsing to extract expected artist
    song_parsed, artist_parsed = parse_title_smart(title)
    
    # Try iTunes search with multiple strategies:
    # 1. If we have parsed artist, try strict matching
    # 2. Always try relaxed matching regardless of parsing success
    song_itunes, artist_itunes = search_itunes_metadata(title, expected_artist=artist_parsed)
    if song_itunes and artist_itunes:
        # Apply universal cleaning to iTunes results
        song_itunes, artist_itunes = apply_universal_song_cleaning(song_itunes, artist_itunes, "iTunes")
        return song_itunes, artist_itunes, "iTunes"
    
    # If iTunes fails but we have good parsed results, use them
    if song_parsed and artist_parsed:
        log(f"Using parsed metadata: {artist_parsed} - {song_parsed}")
        # Apply universal cleaning to parsed results (already cleaned, but ensures consistency)
        song_parsed, artist_parsed = apply_universal_song_cleaning(song_parsed, artist_parsed, "title_parsing")
        return song_parsed, artist_parsed, "title_parsing"
    
    # Conservative fallback - still counts as title parsing attempt
    log("No reliable artist/song could be parsed - using conservative fallback")
    return title, "Unknown Artist", "title_parsing"

def get_acoustid_metadata(filepath):
    """Query AcoustID for metadata using audio fingerprint."""
    if not ACOUSTID_ENABLED:
        log("AcoustID disabled, skipping fingerprinting")
        return None, None
        
    try:
        # Run fpcalc to generate fingerprint
        cmd = [
            get_fpcalc_path(),
            '-json',
            '-length', '120',  # Analyze first 2 minutes
            filepath
        ]
        
        # Hide console window on Windows
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
            log(f"fpcalc failed: {result.stderr}")
            return None, None
            
        # Parse fingerprint data
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"Failed to parse fpcalc JSON output: {e}")
            log(f"fpcalc output: {result.stdout[:200]}...")
            return None, None
            
        fingerprint = data.get('fingerprint')
        duration = data.get('duration')
        
        if not fingerprint or not duration:
            log(f"Missing fingerprint or duration in fpcalc output")
            return None, None
            
        log(f"Generated fingerprint, duration: {duration}s")
        
        # Query AcoustID API
        return query_acoustid(fingerprint, duration)
        
    except subprocess.TimeoutExpired:
        log("fpcalc timeout after 30 seconds")
        return None, None
    except Exception as e:
        log(f"AcoustID fingerprinting error: {e}")
        return None, None

def query_acoustid(fingerprint, duration):
    """Query AcoustID API for metadata using urllib."""
    url = 'https://api.acoustid.org/v2/lookup'
    params = {
        'client': ACOUSTID_API_KEY,
        'fingerprint': fingerprint,
        'duration': int(duration),
        'meta': 'recordings'
    }
    
    try:
        # Build URL with parameters
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # Log the request details for debugging (but not the full fingerprint)
        log(f"AcoustID request - duration: {duration}s, fingerprint length: {len(fingerprint)}")
        
        # Make request with User-Agent
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
        
        # Log API response status
        status = data.get('status', 'unknown')
        if status != 'ok':
            log(f"AcoustID API status: {status}")
            if 'error' in data:
                log(f"AcoustID error: {data['error']}")
            return None, None
        
        # Extract best match
        results = data.get('results', [])
        log(f"AcoustID returned {len(results)} results")
        
        for result in results:
            if result.get('recordings'):
                # Get first recording with good confidence
                confidence = result.get('score', 0)
                if confidence < 0.4:  # Skip low confidence matches
                    log(f"Skipping low confidence match: {confidence:.2f}")
                    continue
                    
                for recording in result['recordings']:
                    artists = recording.get('artists', [])
                    if artists and recording.get('title'):
                        artist = artists[0]['name']
                        title = recording['title']
                        log(f"AcoustID match (confidence: {confidence:.2f}): {artist} - {title}")
                        return title, artist
        
        log("No suitable AcoustID matches found")
        return None, None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No response body'
        log(f"AcoustID API HTTP error: {e.code} {e.reason}")
        log(f"Error response: {error_body[:200]}")
    except urllib.error.URLError as e:
        log(f"AcoustID API connection error: {e}")
    except Exception as e:
        log(f"AcoustID API error: {e}")
    
    return None, None

# ===== AUDIO NORMALIZATION FUNCTIONS =====
def sanitize_filename(text):
    """
    Sanitize text for use in filename.
    """
    # Remove/replace invalid filename characters
    invalid_chars = '<>:"|?*\\/'  # Invalid on Windows
    for char in invalid_chars:
        text = text.replace(char, '_')
    
    # Remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Limit length and clean up
    text = text[:50].strip().rstrip('.')
    
    return text or 'Unknown'

def extract_loudnorm_stats(ffmpeg_output):
    """
    Extract loudnorm statistics from FFmpeg output.
    """
    try:
        # Find JSON output in stderr
        json_start = ffmpeg_output.rfind('{')
        json_end = ffmpeg_output.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            log("No JSON data found in FFmpeg output")
            return None
        
        json_str = ffmpeg_output[json_start:json_end]
        stats = json.loads(json_str)
        
        # Verify required fields
        required_fields = ['input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset']
        for field in required_fields:
            if field not in stats:
                log(f"Missing required field: {field}")
                return None
        
        return stats
        
    except json.JSONDecodeError as e:
        log(f"Failed to parse loudnorm JSON: {e}")
        return None
    except Exception as e:
        log(f"Error extracting loudnorm stats: {e}")
        return None

def normalize_audio(input_path, video_id, metadata):
    """
    Normalize audio to -14 LUFS using FFmpeg's loudnorm filter.
    Returns path to normalized file or None on failure.
    """
    try:
        # Generate output filename based on metadata
        safe_song = sanitize_filename(metadata.get('song', 'Unknown'))
        safe_artist = sanitize_filename(metadata.get('artist', 'Unknown'))
        output_filename = f"{safe_song}_{safe_artist}_{video_id}_normalized.mp4"
        output_path = os.path.join(cache_dir, output_filename)
        
        # Skip if already normalized
        if os.path.exists(output_path):
            log(f"Already normalized: {output_filename}")
            return output_path
        
        log(f"Starting normalization: {metadata['artist']} - {metadata['song']}")
        
        # First pass: Analyze audio
        log("Running first pass audio analysis...")
        analysis_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json',
            '-f', 'null',
            '-'
        ]
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Run analysis
        result = subprocess.run(
            analysis_cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=NORMALIZE_TIMEOUT
        )
        
        if result.returncode != 0:
            log(f"FFmpeg analysis failed: {result.stderr}")
            return None
        
        # Extract loudnorm stats from output
        stats = extract_loudnorm_stats(result.stderr)
        if not stats:
            log("Failed to extract loudnorm statistics")
            return None
        
        log(f"Audio analysis complete - Input: {stats['input_i']} LUFS")
        
        # Second pass: Apply normalization
        log("Running second pass normalization...")
        
        # Build normalization filter with measured values
        loudnorm_filter = (
            f"loudnorm=I=-14:TP=-1:LRA=11:"
            f"measured_I={stats['input_i']}:"
            f"measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:"
            f"measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}"
        )
        
        normalize_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-af', loudnorm_filter,
            '-c:v', 'copy',  # Copy video stream without re-encoding
            '-c:a', 'aac',   # Re-encode audio to AAC
            '-b:a', '192k',  # Audio bitrate
            '-y',  # Overwrite output
            output_path
        ]
        
        # Show progress for long operation
        process = subprocess.Popen(
            normalize_cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        
        # Monitor progress
        for line in process.stderr:
            if 'time=' in line:
                # Extract time progress
                time_match = re.search(r'time=(\d+):(\d+):(\d+)', line)
                if time_match:
                    hours, minutes, seconds = map(int, time_match.groups())
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    # Log progress every 30 seconds
                    if total_seconds % 30 == 0:
                        log(f"Normalizing... {total_seconds}s processed")
        
        process.wait()
        
        if process.returncode != 0:
            log(f"FFmpeg normalization failed")
            return None
        
        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            log(f"Normalization complete: {output_filename} ({file_size_mb:.1f} MB)")
            
            # Clean up temp file
            try:
                os.remove(input_path)
                log(f"Removed temp file: {os.path.basename(input_path)}")
            except Exception as e:
                log(f"Error removing temp file: {e}")
            
            return output_path
        else:
            log("Normalization failed - output file missing or empty")
            return None
            
    except subprocess.TimeoutExpired:
        log("Normalization timeout after 5 minutes")
        return None
    except Exception as e:
        log(f"Normalization error: {e}")
        return None

# ===== VIDEO PROCESSING FUNCTIONS =====
def process_videos_worker():
    """Process videos serially - download, metadata, normalize."""
    global stop_threads
    
    while not stop_threads:
        try:
            # Get video from queue (timeout to check stop_threads)
            try:
                video_info = video_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # Process this video through all stages
            video_id = video_info['id']
            title = video_info['title']
            
            # Skip if already fully processed
            with state_lock:
                if video_id in cached_videos:
                    log(f"Skipping already cached video: {title}")
                    continue
            
            # Download video
            temp_path = download_video(video_id, title)
            if not temp_path:
                log(f"Failed to download: {title}")
                continue
            
            # Try AcoustID metadata extraction
            song, artist = get_acoustid_metadata(temp_path)
            metadata_source = "AcoustID" if (song and artist) else None
            
            # Apply universal cleaning to AcoustID results if found
            if song and artist:
                song, artist = apply_universal_song_cleaning(song, artist, "AcoustID")
            
            # If AcoustID fails, try title-based extraction (iTunes + parsing)
            # This function always returns metadata - never None
            if not song or not artist:
                song, artist, metadata_source = extract_metadata_from_title(title)
            
            # Log metadata source with detailed results
            log(f"Metadata from {metadata_source}: {artist} - {song}")
            
            # Store metadata for normalization
            metadata = {
                'song': song,
                'artist': artist,
                'yt_title': title
            }
            
            # Log final metadata decision
            log(f"=== METADATA RESULT for '{title}' ===")
            log(f"    Artist: {artist}")
            log(f"    Song: {song}")
            log(f"    Source: {metadata_source}")
            log(f"=====================================")
            
            # Normalize audio (Phase 8)
            normalized_path = normalize_audio(temp_path, video_id, metadata)
            if not normalized_path:
                log(f"Failed to normalize: {title}")
                continue
            
            # Update cached videos registry
            with state_lock:
                cached_videos[video_id] = {
                    'path': normalized_path,
                    'song': metadata['song'],
                    'artist': metadata['artist'],
                    'normalized': True
                }
            
            log(f"Video ready for playback: {metadata['artist']} - {metadata['song']}")
            
            # TODO: Continue to Phase 9 (Playback Control)
            
        except Exception as e:
            log(f"Error processing video: {e}")
    
    log("Video processing thread exiting")

# ===== UTILITY FUNCTIONS =====
def ensure_cache_directory():
    """Ensure cache directory exists."""
    try:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(cache_dir, TOOLS_SUBDIR)).mkdir(exist_ok=True)
        log(f"Cache directory ready: {cache_dir}")
        return True
    except Exception as e:
        log(f"Failed to create cache directory: {e}")
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

def get_fpcalc_path():
    """Get path to fpcalc executable."""
    return os.path.join(get_tools_path(), FPCALC_FILENAME)

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
    
    return props

def script_defaults(settings):
    """Set default values for script properties."""
    obs.obs_data_set_default_string(settings, "playlist_url", DEFAULT_PLAYLIST_URL)
    obs.obs_data_set_default_string(settings, "cache_dir", DEFAULT_CACHE_DIR)

def script_update(settings):
    """Called when script properties are updated."""
    global playlist_url, cache_dir
    
    playlist_url = obs.obs_data_get_string(settings, "playlist_url")
    cache_dir = obs.obs_data_get_string(settings, "cache_dir")
    
    log(f"Settings updated - Playlist: {playlist_url}, Cache: {cache_dir}")

def script_load(settings):
    """Called when script is loaded."""
    global stop_threads
    stop_threads = False
    
    log(f"Script version {SCRIPT_VERSION} loaded")
    
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
            log("Cannot sync - tools not ready yet")
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
            log(f"Scene changed to: {scene_name}, Active: {scene_active}")
            obs.obs_source_release(current_scene)

def verify_scene_setup():
    """Verify that required scene and sources exist."""
    scene_source = obs.obs_get_source_by_name(SCENE_NAME)
    if not scene_source:
        log(f"ERROR: Required scene '{SCENE_NAME}' not found! Please create it.")
        return
    
    scene = obs.obs_scene_from_source(scene_source)
    if scene:
        # Check for required sources
        media_source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        
        if not media_source:
            log(f"WARNING: Media Source '{MEDIA_SOURCE_NAME}' not found in scene")
        else:
            obs.obs_source_release(media_source)
            
        if not text_source:
            log(f"WARNING: Text Source '{TEXT_SOURCE_NAME}' not found in scene")
        else:
            obs.obs_source_release(text_source)
    
    obs.obs_source_release(scene_source)
    
    # Remove this timer - only run once
    obs.timer_remove(verify_scene_setup)

def playback_controller():
    """Main playback controller - runs on main thread."""
    # TODO: Implement in Phase 9
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
    
    # Start video processing thread
    process_videos_thread = threading.Thread(target=process_videos_worker, daemon=True)
    process_videos_thread.start()
    
    log("Worker threads started")

def stop_worker_threads():
    """Stop all background worker threads."""
    global tools_thread, playlist_sync_thread, process_videos_thread
    
    log("Stopping worker threads...")
    
    # Signal threads to stop
    sync_event.set()  # Wake up sync thread
    
    # Wait for threads to finish (with timeout)
    if tools_thread and tools_thread.is_alive():
        tools_thread.join(timeout=5)
    
    if playlist_sync_thread and playlist_sync_thread.is_alive():
        playlist_sync_thread.join(timeout=5)
        
    if process_videos_thread and process_videos_thread.is_alive():
        process_videos_thread.join(timeout=5)
    
    log("Worker threads stopped")
