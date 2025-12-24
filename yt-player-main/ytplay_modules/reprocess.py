"""
Reprocess videos that failed Gemini extraction on previous runs.
This module handles renaming files when Gemini succeeds on retry.
"""

import os
import subprocess
import threading
import time

from .logger import log
from .metadata import get_video_metadata
from .state import (
    add_cached_video,
    get_cache_dir,
    get_cached_videos,
    get_gemini_api_key,
    is_tools_ready,
    should_stop_threads,
)
from .utils import sanitize_filename

_reprocess_thread = None

def get_video_title_from_youtube(video_id):
    """Fetch video title from YouTube for a specific video ID."""
    try:
        from .utils import get_ytdlp_path

        ytdlp_path = get_ytdlp_path()

        # Prepare command to get video info
        cmd = [
            ytdlp_path,
            '--get-title',
            '--no-warnings',
            f'https://www.youtube.com/watch?v={video_id}'
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
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            log(f"Failed to get title for video {video_id}")
            return None

    except Exception as e:
        log(f"Error fetching video title: {e}")
        return None

def find_videos_to_reprocess():
    """Find all videos with _gf marker that need Gemini retry."""
    videos_to_reprocess = []
    cached_videos = get_cached_videos()

    for video_id, video_info in cached_videos.items():
        if video_info.get('gemini_failed', False):
            # We need to get the title - either from cache or fetch it
            title = None

            # First try to use the song title we have (it might be from title parsing)
            if video_info.get('song') and video_info.get('song') != 'Unknown Song':
                # Reconstruct a reasonable title from what we have
                title = f"{video_info['song']} - {video_info['artist']}"
            else:
                # Fetch the actual title from YouTube
                title = get_video_title_from_youtube(video_id)

            if title:
                videos_to_reprocess.append({
                    'id': video_id,
                    'title': title,
                    'current_path': video_info['path'],
                    'song': video_info['song'],
                    'artist': video_info['artist']
                })

    return videos_to_reprocess

def reprocess_video(video_info):
    """Attempt to reprocess a single video with Gemini."""
    video_id = video_info['id']
    title = video_info['title']
    current_path = video_info['current_path']

    log(f"Retrying Gemini extraction for: {title}")

    # Try to get metadata again (will use Gemini if API key is available)
    song, artist, metadata_source, gemini_failed = get_video_metadata(
        current_path, title, video_id
    )

    if not gemini_failed and metadata_source == 'Gemini':
        # Gemini succeeded! Need to rename the file
        log(f"Gemini extraction succeeded on retry: {artist} - {song}")

        # Generate new filename without _gf marker
        cache_dir = get_cache_dir()
        safe_song = sanitize_filename(song)
        safe_artist = sanitize_filename(artist)
        new_filename = f"{safe_song}_{safe_artist}_{video_id}_normalized.mp4"
        new_path = os.path.join(cache_dir, new_filename)

        # Rename the file if paths are different
        if current_path != new_path and os.path.exists(current_path):
            try:
                # Remove new path if it exists (shouldn't happen)
                if os.path.exists(new_path):
                    os.remove(new_path)

                # Rename the file
                os.rename(current_path, new_path)
                log(f"Renamed file: {os.path.basename(current_path)} -> {os.path.basename(new_path)}")

                # Update cached video info
                add_cached_video(video_id, {
                    'path': new_path,
                    'song': song,
                    'artist': artist,
                    'normalized': True,
                    'gemini_failed': False
                })

                return True
            except Exception as e:
                log(f"Error renaming file: {e}")
                return False
    else:
        # Gemini still failed or no API key
        if not get_gemini_api_key():
            log("Skipping reprocess - no Gemini API key configured")
        else:
            log(f"Gemini extraction failed again for: {title}")
        return False

def reprocess_worker():
    """Background worker to reprocess videos with failed Gemini extraction."""
    # Wait for tools to be ready
    while not is_tools_ready() and not should_stop_threads():
        time.sleep(1)

    if should_stop_threads():
        return

    # Wait a bit to ensure cache scan is complete
    time.sleep(5)

    # Check if Gemini API key is configured
    if not get_gemini_api_key():
        log("No Gemini API key configured - skipping reprocess of failed videos")
        return

    # Find videos to reprocess
    videos_to_reprocess = find_videos_to_reprocess()

    if not videos_to_reprocess:
        log("No videos found that need Gemini reprocessing")
        return

    log(f"Found {len(videos_to_reprocess)} videos to retry Gemini extraction")

    # Process each video
    success_count = 0
    for video_info in videos_to_reprocess:
        if should_stop_threads():
            break

        if reprocess_video(video_info):
            success_count += 1

        # Small delay between attempts
        time.sleep(0.5)

    if success_count > 0:
        log(f"Successfully reprocessed {success_count} videos with Gemini")

    log("Gemini reprocessing complete")

def start_reprocess_thread():
    """Start the reprocess thread if needed."""
    global _reprocess_thread

    # Only start if not already running
    if _reprocess_thread is None or not _reprocess_thread.is_alive():
        _reprocess_thread = threading.Thread(target=reprocess_worker, daemon=True)
        _reprocess_thread.start()
        log("Started Gemini reprocess thread")
