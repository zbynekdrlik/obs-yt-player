"""
Tool management for OBS YouTube Player.
Downloads and verifies yt-dlp, FFmpeg, and fpcalc.
"""

import os
import time
import platform
import stat
import subprocess
import urllib.request
import threading
from pathlib import Path

from config import (
    YTDLP_FILENAME, FFMPEG_FILENAME, FPCALC_FILENAME,
    YTDLP_URL, YTDLP_URL_WIN, FFMPEG_URLS, FPCALC_URLS,
    TOOLS_CHECK_INTERVAL
)
from logger import log
from state import (
    tools_thread, set_tools_ready, is_tools_logged_waiting, 
    set_tools_logged_waiting, should_stop_threads
)
from utils import get_ytdlp_path, get_ffmpeg_path, get_fpcalc_path, get_tools_path, ensure_cache_directory

def download_file(url, destination, description="file"):
    """Download a file from URL to destination with progress logging."""
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

def setup_tools():
    """Download and verify required tools."""
    # Log waiting message only once
    if not is_tools_logged_waiting():
        log("Waiting for tools to be ready. Please be patient, downloading FFmpeg may take several minutes.")
        set_tools_logged_waiting(True)
    
    # Ensure tools directory exists
    tools_dir = get_tools_path()
    os.makedirs(tools_dir, exist_ok=True)
    
    # Download all tools
    ytdlp_success = download_ytdlp(tools_dir)
    if not ytdlp_success:
        log("Failed to setup yt-dlp, will retry in 60 seconds")
        return False
    
    ffmpeg_success = download_ffmpeg(tools_dir)
    if not ffmpeg_success:
        log("Failed to setup FFmpeg, will retry in 60 seconds")
        return False
    
    fpcalc_success = download_fpcalc(tools_dir)
    if not fpcalc_success:
        log("Failed to setup fpcalc, will retry in 60 seconds")
        return False
    
    # All tools downloaded and verified successfully
    set_tools_ready(True)
    log("All tools are ready and verified!")
    return True

def tools_setup_worker():
    """Background thread for setting up tools."""
    while not should_stop_threads():
        try:
            # Ensure cache directory exists
            if not ensure_cache_directory():
                time.sleep(TOOLS_CHECK_INTERVAL)
                continue
            
            # Try to setup tools
            if setup_tools():
                # Tools are ready, trigger startup sync
                log("Tools setup complete")
                # Import here to avoid circular import
                from playlist import trigger_startup_sync
                trigger_startup_sync()
                break
            
            # Wait before retry
            log(f"Retrying tool setup in {TOOLS_CHECK_INTERVAL} seconds...")
            
            # Sleep in small increments to check stop_threads
            for _ in range(TOOLS_CHECK_INTERVAL):
                if should_stop_threads():
                    break
                time.sleep(1)
                
        except Exception as e:
            log(f"Error in tools setup: {e}")
            time.sleep(TOOLS_CHECK_INTERVAL)
    
    log("Tools setup thread exiting")

def start_tools_thread():
    """Start the tools setup thread."""
    global tools_thread
    import state
    state.tools_thread = threading.Thread(target=tools_setup_worker, daemon=True)
    state.tools_thread.start()
