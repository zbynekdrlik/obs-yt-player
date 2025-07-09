"""Tool management for OBS YouTube Player.
Handles downloading and verification of required tools (yt-dlp, ffmpeg).
"""

import os
import time
import threading
import subprocess
import zipfile
import requests
from pathlib import Path

from .logger import log
from .state import (
    is_tools_ready, set_tools_ready,
    should_stop_threads, is_tools_logged_waiting,
    set_tools_logged_waiting, tools_thread
)
from .config import (
    TOOLS_CHECK_INTERVAL, YTDLP_URL, FFMPEG_URL,
    YTDLP_FILENAME, FFMPEG_FILENAME, TOOLS_SUBDIR
)

# Import utils functions
from .utils import get_tools_path, get_ytdlp_path, get_ffmpeg_path, ensure_cache_directory

def verify_tool(tool_path, version_arg="--version"):
    """Verify a tool exists and is executable."""
    if not os.path.exists(tool_path):
        return False
    
    try:
        # Test if tool is executable
        result = subprocess.run(
            [tool_path, version_arg],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def download_file(url, dest_path, description="file"):
    """Download a file with progress reporting."""
    try:
        log(f"Downloading {description}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        last_progress = 0
        
        # Ensure parent directory exists
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if should_stop_threads():
                    return False
                f.write(chunk)
                downloaded += len(chunk)
                
                # Log progress every 10%
                if total_size > 0:
                    progress = int((downloaded / total_size) * 100)
                    if progress >= last_progress + 10:
                        log(f"{description}: {progress}% complete")
                        last_progress = progress
        
        log(f"{description} downloaded successfully")
        return True
    except Exception as e:
        log(f"Failed to download {description}: {e}")
        return False

def extract_ffmpeg_windows():
    """Extract FFmpeg from downloaded zip."""
    try:
        tools_path = get_tools_path()
        zip_path = os.path.join(tools_path, "ffmpeg.zip")
        
        if not os.path.exists(zip_path):
            return False
        
        log("Extracting FFmpeg...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find ffmpeg.exe in the zip
            ffmpeg_found = False
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('ffmpeg.exe'):
                    # Extract just ffmpeg.exe
                    target_path = os.path.join(tools_path, FFMPEG_FILENAME)
                    with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    ffmpeg_found = True
                    break
            
            if not ffmpeg_found:
                log("FFmpeg.exe not found in zip")
                return False
        
        # Clean up zip file
        try:
            os.remove(zip_path)
        except Exception:
            pass
        
        log("FFmpeg extracted successfully")
        return True
        
    except Exception as e:
        log(f"Failed to extract FFmpeg: {e}")
        return False

def download_ytdlp():
    """Download yt-dlp executable."""
    ytdlp_path = get_ytdlp_path()
    
    # Check if already exists and works
    if verify_tool(ytdlp_path):
        return True
    
    # Download yt-dlp
    return download_file(YTDLP_URL, ytdlp_path, "yt-dlp")

def download_ffmpeg():
    """Download and extract FFmpeg."""
    ffmpeg_path = get_ffmpeg_path()
    
    # Check if already exists and works
    if verify_tool(ffmpeg_path):
        return True
    
    # For Windows, download zip and extract
    if os.name == 'nt':
        tools_path = get_tools_path()
        zip_path = os.path.join(tools_path, "ffmpeg.zip")
        
        # Download zip
        if not download_file(FFMPEG_URL, zip_path, "FFmpeg"):
            return False
        
        # Extract ffmpeg.exe
        if not extract_ffmpeg_windows():
            return False
        
        # Verify it works
        return verify_tool(ffmpeg_path)
    
    # For other platforms, would need different handling
    log("FFmpeg download not implemented for this platform")
    return False

def update_ytdlp():
    """Update yt-dlp to latest version."""
    ytdlp_path = get_ytdlp_path()
    
    if not os.path.exists(ytdlp_path):
        return False
    
    try:
        log("Updating yt-dlp...")
        result = subprocess.run(
            [ytdlp_path, "-U"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            if "yt-dlp is up to date" in result.stdout:
                log("yt-dlp is already up to date")
            else:
                log("yt-dlp updated successfully")
            return True
        else:
            log(f"yt-dlp update failed: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"Failed to update yt-dlp: {e}")
        return False

def check_and_setup_tools():
    """Check for required tools and download if needed."""
    # Ensure cache directory exists
    if not ensure_cache_directory():
        return False
    
    tools_ready = True
    
    # Check yt-dlp
    ytdlp_path = get_ytdlp_path()
    if not verify_tool(ytdlp_path):
        log("yt-dlp not found, downloading...")
        if not download_ytdlp():
            tools_ready = False
        else:
            # Try to update after download
            update_ytdlp()
    else:
        log("yt-dlp found and working")
        # Try to update existing yt-dlp
        update_ytdlp()
    
    # Check FFmpeg
    ffmpeg_path = get_ffmpeg_path()
    if not verify_tool(ffmpeg_path):
        log("FFmpeg not found, downloading...")
        if not download_ffmpeg():
            tools_ready = False
    else:
        log("FFmpeg found and working")
    
    return tools_ready

def tools_check_thread():
    """Background thread to check and download required tools."""
    log("[Tools Thread] Starting tools check...")
    
    while not should_stop_threads():
        try:
            if check_and_setup_tools():
                log("[Tools Thread] All tools ready!")
                set_tools_ready(True)
                break
            else:
                if not is_tools_logged_waiting():
                    log("[Tools Thread] Some tools missing, will retry...")
                    set_tools_logged_waiting(True)
                time.sleep(TOOLS_CHECK_INTERVAL)
                
        except Exception as e:
            log(f"[Tools Thread] Error: {e}")
            time.sleep(TOOLS_CHECK_INTERVAL)
    
    log("[Tools Thread] Exiting")

def start_tools_thread():
    """Start the tools checking thread."""
    global tools_thread
    
    if tools_thread and tools_thread.is_alive():
        return
    
    from .state import tools_thread as state_tools_thread
    state_tools_thread = threading.Thread(target=tools_check_thread, name="ToolsThread")
    state_tools_thread.daemon = True
    state_tools_thread.start()