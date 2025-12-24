"""
Utility functions for OBS YouTube Player.
"""

import os
import re
import unicodedata
from pathlib import Path

from .config import TOOLS_SUBDIR
from .state import get_cache_dir

# YouTube ID validation pattern
YOUTUBE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')

def get_tools_path():
    """Get path to tools directory."""
    return os.path.join(get_cache_dir(), TOOLS_SUBDIR)

def get_ytdlp_path():
    """Get path to yt-dlp executable."""
    from .config import YTDLP_FILENAME
    return os.path.join(get_tools_path(), YTDLP_FILENAME)

def get_ffmpeg_path():
    """Get path to ffmpeg executable."""
    from .config import FFMPEG_FILENAME
    return os.path.join(get_tools_path(), FFMPEG_FILENAME)

def sanitize_filename(text):
    """Sanitize text for use in filename."""
    # First, replace forward slashes with hyphens to avoid space issues
    text = text.replace('/', '-')

    # Remove/replace other invalid filename characters
    invalid_chars = '<>:"|?*\\'  # Note: forward slash already handled
    for char in invalid_chars:
        text = text.replace(char, '_')

    # Clean up multiple spaces or dashes
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'-+', '-', text)   # Replace multiple dashes with single dash
    text = re.sub(r'_+', '_', text)   # Replace multiple underscores with single underscore

    # Remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Remove any leading/trailing spaces, dashes, or underscores
    text = text.strip(' -_')

    # Limit length and clean up
    text = text[:50].strip().rstrip('.')

    return text or 'Unknown'

def ensure_cache_directory():
    """Ensure cache directory exists."""
    from .logger import log

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

def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds is None or seconds < 0:
        return "unknown"

    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {seconds}s"

    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {seconds}s"
