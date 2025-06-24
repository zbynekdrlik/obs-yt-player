"""
Tools management for OBS YouTube Player.
Handles downloading and updating of yt-dlp and ffmpeg.
"""

import os
import threading
import time
import subprocess
import urllib.request
import zipfile
import tarfile
import platform
from pathlib import Path

from ytfast_modules.logger import log
from ytfast_modules.config import (
    TOOLS_SUBDIR, YTDLP_FILENAME, FFMPEG_FILENAME,
    TOOLS_CHECK_INTERVAL, YTDLP_URL, FFMPEG_URL
)
from ytfast_modules.state import (
    get_cache_dir, is_tools_ready, set_tools_ready,
    should_stop_threads, is_tools_logged_waiting,
    set_tools_logged_waiting, tools_thread
)

def get_tools_dir():
    """Get tools directory path."""
    cache_dir = get_cache_dir()
    return os.path.join(cache_dir, TOOLS_SUBDIR)

def ensure_tools_dir():
    """Ensure tools directory exists."""
    tools_dir = get_tools_dir()
    os.makedirs(tools_dir, exist_ok=True)
    return tools_dir

def check_tool_exists(tool_name):
    """Check if a tool exists and is executable."""
    tools_dir = get_tools_dir()
    tool_path = os.path.join(tools_dir, tool_name)
    
    if not os.path.exists(tool_path):
        return False
    
    # On Windows, .exe files are executable by default
    if platform.system() == 'Windows':
        return tool_name.endswith('.exe')
    
    # On Unix, check if file is executable
    return os.access(tool_path, os.X_OK)

def download_file(url, dest_path):
    """Download a file with progress reporting."""
    try:
        log(f"Downloading {os.path.basename(dest_path)}...")
        
        # Download with urllib
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            # Download in chunks
            chunk_size = 8192
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Report progress
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        if percent % 20 == 0 and percent > 0:  # Log every 20%
                            log(f"Download progress: {percent}%")
        
        log(f"Download complete: {os.path.basename(dest_path)}")
        return True
        
    except Exception as e:
        log(f"Download failed: {e}")
        # Clean up partial download
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def download_ytdlp():
    """Download yt-dlp executable."""
    tools_dir = ensure_tools_dir()
    ytdlp_path = os.path.join(tools_dir, YTDLP_FILENAME)
    
    # Download yt-dlp
    if not download_file(YTDLP_URL, ytdlp_path):
        return False
    
    # Make executable on Unix
    if platform.system() != 'Windows':
        os.chmod(ytdlp_path, 0o755)
    
    return True

def download_ffmpeg():
    """Download and extract FFmpeg."""
    tools_dir = ensure_tools_dir()
    
    # Platform-specific handling
    system = platform.system()
    
    if system == 'Windows':
        # Download zip file
        zip_path = os.path.join(tools_dir, 'ffmpeg.zip')
        if not download_file(FFMPEG_URL, zip_path):
            return False
        
        try:
            # Extract zip
            log("Extracting FFmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find ffmpeg.exe in the archive
                ffmpeg_found = False
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('ffmpeg.exe'):
                        # Extract just ffmpeg.exe
                        file_data = zip_ref.read(file_info)
                        ffmpeg_path = os.path.join(tools_dir, FFMPEG_FILENAME)
                        with open(ffmpeg_path, 'wb') as f:
                            f.write(file_data)
                        ffmpeg_found = True
                        break
                
                if not ffmpeg_found:
                    log("FFmpeg.exe not found in archive")
                    return False
            
            # Clean up zip file
            os.remove(zip_path)
            log("FFmpeg extracted successfully")
            return True
            
        except Exception as e:
            log(f"Failed to extract FFmpeg: {e}")
            # Clean up
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False
    
    else:
        # Unix/Mac systems - would need different handling
        log(f"FFmpeg download not implemented for {system}")
        return False

def verify_tool_works(tool_name):
    """Verify a tool can be executed."""
    tools_dir = get_tools_dir()
    tool_path = os.path.join(tools_dir, tool_name)
    
    try:
        # Try to run the tool with version flag
        if 'ffmpeg' in tool_name:
            cmd = [tool_path, '-version']
        else:  # yt-dlp
            cmd = [tool_path, '--version']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            # Extract version info
            version_line = result.stdout.split('\n')[0]
            log(f"{tool_name} verified: {version_line}")
            return True
        else:
            log(f"{tool_name} failed to run: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"{tool_name} timed out during verification")
        return False
    except Exception as e:
        log(f"Failed to verify {tool_name}: {e}")
        return False

def tools_check_loop():
    """Main loop for tools thread."""
    while not should_stop_threads():
        try:
            # Check if tools are ready
            ytdlp_exists = check_tool_exists(YTDLP_FILENAME)
            ffmpeg_exists = check_tool_exists(FFMPEG_FILENAME)
            
            if ytdlp_exists and ffmpeg_exists:
                # Verify tools actually work
                ytdlp_works = verify_tool_works(YTDLP_FILENAME)
                ffmpeg_works = verify_tool_works(FFMPEG_FILENAME)
                
                if ytdlp_works and ffmpeg_works:
                    if not is_tools_ready():
                        log("Tools verified and ready")
                        set_tools_ready(True)
                        set_tools_logged_waiting(False)
                    # Tools ready, just sleep
                    time.sleep(30)  # Check less frequently when tools are ready
                    continue
            
            # Tools not ready
            set_tools_ready(False)
            
            if not is_tools_logged_waiting():
                log("Tools not found, downloading...")
                set_tools_logged_waiting(True)
            
            # Download missing tools
            if not ytdlp_exists:
                log("Downloading yt-dlp...")
                if download_ytdlp():
                    log("yt-dlp downloaded successfully")
                else:
                    log("Failed to download yt-dlp, will retry")
            
            if not ffmpeg_exists:
                log("Downloading FFmpeg...")
                if download_ffmpeg():
                    log("FFmpeg downloaded successfully")
                else:
                    log("Failed to download FFmpeg, will retry")
            
            # Wait before retry
            time.sleep(TOOLS_CHECK_INTERVAL)
            
        except Exception as e:
            log(f"Error in tools thread: {e}")
            time.sleep(TOOLS_CHECK_INTERVAL)

def start_tools_thread():
    """Start the tools management thread."""
    global tools_thread
    
    if tools_thread and tools_thread.is_alive():
        return
    
    tools_thread = threading.Thread(target=tools_check_loop, name="ToolsThread")
    tools_thread.daemon = True
    tools_thread.start()
    log("Tools thread started")

def cleanup_tools_thread():
    """Wait for tools thread to finish."""
    global tools_thread
    
    if tools_thread and tools_thread.is_alive():
        log("Waiting for tools thread to finish...")
        tools_thread.join(timeout=2.0)
        if tools_thread.is_alive():
            log("Tools thread did not finish in time")
        else:
            log("Tools thread finished")