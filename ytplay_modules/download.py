"""
Video download module for OBS YouTube Player.
Handles downloading videos from YouTube using yt-dlp.
"""

import threading
import time
import queue
import os
import re
import subprocess

from config import MAX_RESOLUTION, MIN_VIDEO_HEIGHT, DOWNLOAD_TIMEOUT
from logger import log
from state import (
    should_stop_threads, get_download_queue, set_download_queue,
    set_thread_script_context, register_thread, unregister_thread,
    get_cache_dir, is_audio_only_mode,
    get_local_videos, get_metadata_cache
)
from tools import get_ytdlp_path, get_ffmpeg_path

# Track download progress per video
_download_progress = {}
_progress_lock = threading.Lock()

def download_video(video_id, title):
    """Download video to temporary file."""
    cache_dir = get_cache_dir()
    output_path = os.path.join(cache_dir, f"{video_id}_temp.mp4")
    
    # Remove existing temp file
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            log(f"Removed existing temp file: {output_path}")
        except Exception as e:
            log(f"Error removing temp file: {e}")
    
    try:
        # Check if audio-only mode is enabled
        audio_only_mode = is_audio_only_mode()
        
        # Set video quality format based on mode
        if audio_only_mode:
            # Minimal video quality (144p) with best audio
            format_string = f'bestvideo[height<={MIN_VIDEO_HEIGHT}]+bestaudio/worst[height<={MIN_VIDEO_HEIGHT}]+bestaudio/bestaudio'
            log(f"Audio-only mode: downloading minimal video quality ({MIN_VIDEO_HEIGHT}p) with best audio")
        else:
            # Normal quality settings
            format_string = f'bestvideo[height<={MAX_RESOLUTION}]+bestaudio/best[height<={MAX_RESOLUTION}]/best'
        
        # First, get video info to log quality
        info_cmd = [
            get_ytdlp_path(),
            '-f', format_string,
            '--print', '%(width)s,%(height)s,%(fps)s,%(vcodec)s,%(acodec)s',
            '--no-warnings',
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        
        # Get video info (Windows-specific subprocess settings)
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
                    quality_mode = "Audio-only mode" if audio_only_mode else "Normal mode"
                    log(f"{quality_mode} - Video quality: {width}x{height} @ {fps}fps, video: {vcodec}, audio: {acodec}")
        except Exception as e:
            log(f"Could not get video info: {e}")
        
        # Now download the video
        cmd = [
            get_ytdlp_path(),
            '-f', format_string,
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
        
        # Reset progress tracking for this video
        with _progress_lock:
            _download_progress[video_id] = set()
        
        # Start download process with hidden window
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
        with _progress_lock:
            _download_progress.pop(video_id, None)

def parse_progress(line, video_id, title):
    """Parse yt-dlp progress output and log at milestones."""
    # Look for: [download]  XX.X% of ~XXX.XXMiB at XXX.XXKiB/s
    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
    if match:
        percent = float(match.group(1))
        
        # Get milestone set for this video
        with _progress_lock:
            milestones = _download_progress.get(video_id, set())
            
            # If we've already logged 50%, ignore further progress
            if 50 in milestones:
                return
            
            # Log only at 50%
            if percent >= 50 and 50 not in milestones:
                log(f"Downloading {title}: 50%")
                milestones.add(50)
                _download_progress[video_id] = milestones

def process_video(video_info):
    """Process a single video through all stages."""
    video_id = video_info['id']
    title = video_info['title']
    
    # Check if already cached
    local_videos = get_local_videos()
    metadata_cache = get_metadata_cache()
    
    if video_id in local_videos and video_id in metadata_cache:
        # Check if file exists
        cached_info = metadata_cache.get(video_id, {})
        if cached_info.get('path') and os.path.exists(cached_info['path']):
            log(f"Skipping already cached video: {title}")
            return
    
    # Download video
    temp_path = download_video(video_id, title)
    if not temp_path:
        log(f"Failed to download: {title}")
        return
    
    # Get metadata
    from metadata import extract_metadata, get_gemini_api_key
    from state import get_gemini_api_key as state_get_gemini_api_key
    
    gemini_key = state_get_gemini_api_key()
    metadata_result = extract_metadata({'id': video_id, 'title': title}, gemini_key)
    
    # Extract song and artist
    song = metadata_result.get('song', 'Unknown Song')
    artist = metadata_result.get('artist', 'Unknown Artist')
    gemini_failed = metadata_result.get('gemini_failed', False)
    
    log(f"Metadata extracted - Artist: {artist}, Song: {song}")
    
    # Normalize audio
    from normalize import normalize_audio
    normalized_path = normalize_audio(temp_path, video_id, {
        'song': song,
        'artist': artist,
        'yt_title': title
    }, gemini_failed)
    
    if not normalized_path:
        log(f"Failed to normalize: {title}")
        return
    
    # Update cache
    local_videos.add(video_id)
    metadata_cache[video_id] = {
        'path': normalized_path,
        'song': song,
        'artist': artist,
        'normalized': True,
        'gemini_failed': gemini_failed
    }
    
    log(f"Video ready for playback: {artist} - {song}")

def download_video_worker(script_path):
    """Background thread for video downloading."""
    # Set thread context
    set_thread_script_context(script_path)
    
    # Register thread
    register_thread('download', threading.current_thread())
    
    # Get or create download queue
    download_queue = get_download_queue()
    if not download_queue:
        download_queue = queue.Queue()
        set_download_queue(download_queue)
    
    try:
        while not should_stop_threads():
            try:
                # Check for videos to download
                video_info = download_queue.get(timeout=1)
                
                # Process the video
                process_video(video_info)
                
                # Mark task as done
                download_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                log(f"Error in download worker: {e}")
    
    finally:
        # Unregister thread
        unregister_thread('download')
        log("Download thread exiting")

def start_video_processing_thread():
    """Start the video processing thread."""
    # Get current script path from thread-local storage
    script_path = getattr(threading.current_thread(), '_script_path', None)
    
    if not script_path:
        # Try to get from main thread state
        import state
        script_path = getattr(state._thread_local, 'script_path', None)
    
    if not script_path:
        log("ERROR: No script path available for download thread")
        return
    
    thread = threading.Thread(
        target=download_video_worker,
        args=(script_path,),
        daemon=True
    )
    thread.start()
