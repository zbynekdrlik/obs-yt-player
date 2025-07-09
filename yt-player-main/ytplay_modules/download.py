"""
Video downloading for OBS YouTube Player (Windows-only).
Downloads videos using yt-dlp and manages the processing pipeline.
"""

import os
import re
import subprocess
import threading
import queue

from .config import MAX_RESOLUTION, MIN_VIDEO_HEIGHT, DOWNLOAD_TIMEOUT, SCRIPT_VERSION
from .logger import log
from .state import (
    video_queue, process_videos_thread, should_stop_threads,
    get_cache_dir, is_video_cached, add_cached_video,
    download_progress_milestones, is_audio_only_mode
)
from .utils import get_ytdlp_path, get_ffmpeg_path
from .metadata import get_video_metadata
from .normalize import normalize_audio

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
        download_progress_milestones[video_id] = set()
        
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

def process_videos_worker():
    """Process videos serially - download, metadata, normalize."""
    while not should_stop_threads():
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
            if is_video_cached(video_id):
                log(f"Skipping already cached video: {title}")
                continue
            
            # Download video
            temp_path = download_video(video_id, title)
            if not temp_path:
                log(f"Failed to download: {title}")
                continue
            
            # Get metadata (from metadata module) - UPDATED to handle 4 return values
            song, artist, metadata_source, gemini_failed = get_video_metadata(temp_path, title, video_id)
            
            # Log metadata source with detailed results
            log(f"Metadata from {metadata_source}: {artist} - {song}")
            if gemini_failed:
                log(f"Note: Gemini extraction failed for this video")
            
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
            log(f"    Gemini Failed: {gemini_failed}")
            log(f"=====================================")
            
            # Normalize audio - PASS GEMINI_FAILED FLAG
            normalized_path = normalize_audio(temp_path, video_id, metadata, gemini_failed)
            if not normalized_path:
                log(f"Failed to normalize: {title}")
                continue
            
            # Update cached videos registry - include gemini_failed flag
            add_cached_video(video_id, {
                'path': normalized_path,
                'song': metadata['song'],
                'artist': metadata['artist'],
                'normalized': True,
                'gemini_failed': gemini_failed
            })
            
            log(f"Video ready for playback: {metadata['artist']} - {metadata['song']}")
            
        except Exception as e:
            log(f"Error processing video: {e}")
    
    log("Video processing thread exiting")

def start_video_processing_thread():
    """Start the video processing thread."""
    global process_videos_thread
    from . import state
    state.process_videos_thread = threading.Thread(target=process_videos_worker, daemon=True)
    state.process_videos_thread.start()
