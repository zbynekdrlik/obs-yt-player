"""
Playlist synchronization for OBS YouTube Player.
Fetches playlist information and manages sync operations.
"""

import json
import os
import subprocess
import threading

from .cache import cleanup_removed_videos, scan_existing_cache
from .logger import log
from .state import (
    get_playlist_url,
    is_sync_on_startup_done,
    is_tools_ready,
    is_video_cached,
    set_playlist_video_ids,
    set_sync_on_startup_done,
    should_stop_threads,
    sync_event,
    video_queue,
)
from .utils import get_ytdlp_path


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
    while not should_stop_threads():
        # Wait for sync signal or timeout
        if not sync_event.wait(timeout=1):
            continue

        # Clear the event
        sync_event.clear()

        # Check if we should exit
        if should_stop_threads():
            break

        # Wait for tools to be ready
        if not is_tools_ready():
            log("Sync requested but tools not ready")
            continue

        log("Starting playlist synchronization")

        try:
            # First scan existing cache (Phase 3 addition)
            scan_existing_cache()

            # Initialize play history from persistent storage
            from .state import initialize_played_videos
            initialize_played_videos()

            # Fetch playlist
            playlist_url = get_playlist_url()
            videos = fetch_playlist_with_ytdlp(playlist_url)

            if not videos:
                log("No videos found in playlist or fetch failed")
                continue

            # Update playlist video IDs
            video_ids = [video['id'] for video in videos]
            set_playlist_video_ids(video_ids)

            # Queue only videos not in cache (Phase 3 enhancement)
            queued_count = 0
            skipped_count = 0

            for video in videos:
                video_id = video['id']

                # Check if already cached
                if is_video_cached(video_id):
                    skipped_count += 1
                    continue

                # Queue for processing
                video_queue.put(video)
                queued_count += 1

            log(f"Queued {queued_count} videos for processing, {skipped_count} already in cache")

            # Clean up removed videos (Phase 3 addition)
            cleanup_removed_videos()

        except Exception as e:
            log(f"Error in playlist sync: {e}")

    log("Playlist sync thread exiting")

def trigger_startup_sync():
    """Trigger one-time sync on startup after tools are ready."""
    if is_sync_on_startup_done():
        return

    set_sync_on_startup_done(True)
    log("Starting one-time playlist sync on startup")
    sync_event.set()  # Signal playlist sync thread to run

def trigger_manual_sync():
    """Trigger manual playlist sync."""
    sync_event.set()

def start_playlist_sync_thread():
    """Start the playlist sync thread."""
    global playlist_sync_thread
    from . import state
    state.playlist_sync_thread = threading.Thread(target=playlist_sync_worker, daemon=True)
    state.playlist_sync_thread.start()
