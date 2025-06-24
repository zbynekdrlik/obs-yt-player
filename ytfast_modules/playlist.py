"""
Playlist fetching for OBS YouTube Player.
Handles YouTube playlist fetching using yt-dlp.
"""

import subprocess
import json
import os

from ytfast_modules.logger import log
from ytfast_modules.config import YTDLP_FILENAME, TOOLS_SUBDIR
from ytfast_modules.state import get_cache_dir, get_playlist_url

def get_ytdlp_path():
    """Get full path to yt-dlp executable."""
    return os.path.join(get_cache_dir(), TOOLS_SUBDIR, YTDLP_FILENAME)

def fetch_playlist_videos():
    """Fetch playlist video IDs using yt-dlp."""
    playlist_url = get_playlist_url()
    if not playlist_url:
        log("No playlist URL configured")
        return []
    
    ytdlp_path = get_ytdlp_path()
    
    # Extract playlist info
    cmd = [
        ytdlp_path,
        '--flat-playlist',
        '--dump-json',
        '--no-warnings',
        playlist_url
    ]
    
    try:
        log(f"Fetching playlist: {playlist_url}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"Failed to fetch playlist: {result.stderr}")
            return []
        
        # Parse JSON output (one JSON object per line)
        video_ids = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    video_id = video_data.get('id')
                    if video_id:
                        video_ids.append(video_id)
                except json.JSONDecodeError:
                    continue
        
        log(f"Found {len(video_ids)} videos in playlist")
        return video_ids
        
    except Exception as e:
        log(f"Error fetching playlist: {e}")
        return []