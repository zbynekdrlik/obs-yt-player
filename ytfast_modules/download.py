"""
Video downloading for OBS YouTube Player.
Handles downloading videos using yt-dlp.
"""

import subprocess
import os
import json
from pathlib import Path

from ytfast_modules.logger import log
from ytfast_modules.config import (
    YTDLP_FILENAME, TOOLS_SUBDIR, MAX_RESOLUTION, DOWNLOAD_TIMEOUT
)
from ytfast_modules.state import get_cache_dir, download_progress_milestones
from ytfast_modules.utils import sanitize_filename

def get_ytdlp_path():
    """Get full path to yt-dlp executable."""
    return os.path.join(get_cache_dir(), TOOLS_SUBDIR, YTDLP_FILENAME)

def progress_hook(line, video_id):
    """Parse yt-dlp progress output and log milestones."""
    try:
        # Look for download percentage
        if '[download]' in line and '%' in line:
            # Extract percentage
            parts = line.split()
            for part in parts:
                if part.endswith('%'):
                    try:
                        percent = float(part[:-1])
                        # Log at 25%, 50%, 75%, 100%
                        milestone = int(percent / 25) * 25
                        if milestone > 0 and milestone not in download_progress_milestones.get(video_id, set()):
                            if video_id not in download_progress_milestones:
                                download_progress_milestones[video_id] = set()
                            download_progress_milestones[video_id].add(milestone)
                            log(f"Download progress: {milestone}%")
                    except ValueError:
                        pass
    except Exception:
        pass  # Ignore parsing errors

def download_video(video_id, output_path):
    """Download a video using yt-dlp."""
    ytdlp_path = get_ytdlp_path()
    
    # Prepare yt-dlp command
    cmd = [
        ytdlp_path,
        f'https://youtube.com/watch?v={video_id}',
        '-f', f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        '--no-playlist',
        '--no-warnings',
        '--quiet',
        '--progress',
        '--newline'
    ]
    
    try:
        log(f"Starting download: {video_id}")
        
        # Clear progress tracking for this video
        download_progress_milestones[video_id] = set()
        
        # Run yt-dlp with timeout
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output line by line for progress
        for line in process.stdout:
            line = line.strip()
            if line:
                progress_hook(line, video_id)
        
        # Wait for completion
        process.wait(timeout=DOWNLOAD_TIMEOUT)
        
        # Clean up progress tracking
        if video_id in download_progress_milestones:
            del download_progress_milestones[video_id]
        
        if process.returncode == 0:
            log(f"Download complete: {video_id}")
            return True
        else:
            log(f"Download failed with return code: {process.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"Download timed out after {DOWNLOAD_TIMEOUT}s")
        process.kill()
        # Clean up partial download
        if os.path.exists(output_path):
            os.remove(output_path)
        return False
    except Exception as e:
        log(f"Download error: {e}")
        return False

def get_video_metadata(video_id):
    """Get video title and metadata using yt-dlp."""
    ytdlp_path = get_ytdlp_path()
    
    cmd = [
        ytdlp_path,
        f'https://youtube.com/watch?v={video_id}',
        '--dump-json',
        '--no-warnings',
        '--no-playlist'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            metadata = json.loads(result.stdout)
            return {
                'title': metadata.get('title', 'Unknown'),
                'uploader': metadata.get('uploader', 'Unknown'),
                'duration': metadata.get('duration', 0)
            }
        else:
            log(f"Failed to get metadata: {result.stderr}")
            return None
            
    except json.JSONDecodeError:
        log("Failed to parse video metadata")
        return None
    except subprocess.TimeoutExpired:
        log("Metadata fetch timed out")
        return None
    except Exception as e:
        log(f"Error getting metadata: {e}")
        return None