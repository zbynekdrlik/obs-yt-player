"""
Utility functions for OBS YouTube Player.
"""

import os
import re
import unicodedata
from pathlib import Path
from config import TOOLS_SUBDIR
from state import get_cache_dir

# YouTube ID validation pattern
YOUTUBE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')

def get_tools_path():
    """Get path to tools directory."""
    return os.path.join(get_cache_dir(), TOOLS_SUBDIR)

def get_ytdlp_path():
    """Get path to yt-dlp executable."""
    from config import YTDLP_FILENAME
    return os.path.join(get_tools_path(), YTDLP_FILENAME)

def get_ffmpeg_path():
    """Get path to ffmpeg executable."""
    from config import FFMPEG_FILENAME
    return os.path.join(get_tools_path(), FFMPEG_FILENAME)

def get_fpcalc_path():
    """Get path to fpcalc executable."""
    from config import FPCALC_FILENAME
    return os.path.join(get_tools_path(), FPCALC_FILENAME)

def sanitize_filename(text):
    """Sanitize text for use in filename."""
    # Remove/replace invalid filename characters
    invalid_chars = '<>:"|?*\\/'  # Note: escaped backslash
    for char in invalid_chars:
        text = text.replace(char, '_')
    
    # Remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Limit length and clean up
    text = text[:50].strip().rstrip('.')
    
    return text or 'Unknown'

def ensure_cache_directory():
    """Ensure cache directory exists."""
    from logger import log
    
    try:
        cache_dir = get_cache_dir()
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(cache_dir, TOOLS_SUBDIR)).mkdir(exist_ok=True)
        log(f"Cache directory ready: {cache_dir}")
        return True
    except Exception as e:
        log(f"Failed to create cache directory: {e}")
        return False

def validate_youtube_id(video_id):
    """Validate YouTube video ID format."""
    return bool(YOUTUBE_ID_PATTERN.match(video_id))
