"""
Configuration for OBS YouTube Player (Windows-only).
"""

import os
import sys
from pathlib import Path

# Version - INCREMENT WITH EVERY CODE CHANGE
SCRIPT_VERSION = "3.0.9"  # Enhanced Gemini prompt to enforce JSON-only responses and added fallback JSON extraction

# Get script information from environment or defaults
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ytfast.py'))
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# Core settings - these are defaults, actual values are managed via script properties
DEFAULT_PLAYLIST_URL = ""
DEFAULT_CACHE_DIR = ""

# Scene verification delay (milliseconds)
SCENE_CHECK_DELAY = 1000  # 1 second after script load

# Feature flags - can be controlled via environment variables for testing
ACOUSTID_ENABLED = os.environ.get('YTFAST_ACOUSTID_ENABLED', 'true').lower() == 'true'
ACOUSTID_API_KEY = '3xvMBuMEGH'  # Free public key

# Audio normalization settings (LUFS)
TARGET_LUFS = -14.0  # YouTube's standard

# Download settings
DOWNLOAD_MAX_HEIGHT = 1440  # Maximum video height (1440p)
DOWNLOAD_AUDIO_QUALITY = 256  # Audio bitrate in kbps
DOWNLOAD_FORMAT_PREFERENCE = [
    # Prefer AV1 codec for better quality/compression
    'bestvideo[height<=1440][vcodec^=av01]+bestaudio[acodec=opus]/bestaudio[acodec=aac]',
    # Fallback to VP9
    'bestvideo[height<=1440][vcodec^=vp09]+bestaudio[acodec=opus]/bestaudio[acodec=aac]',
    # Fallback to H264
    'bestvideo[height<=1440][vcodec^=avc1]+bestaudio[acodec=aac]/bestaudio[acodec=opus]',
    # Final fallback
    'best[height<=1440]'
]

# Threading settings
MAX_DOWNLOAD_WORKERS = 2  # Simultaneous downloads
MAX_PROCESSING_WORKERS = 1  # Simultaneous audio processing
DOWNLOAD_CHECK_INTERVAL = 300  # Seconds between playlist checks

# UI settings
TITLE_FADE_DURATION = 1.0  # Seconds for fade in/out
TITLE_SHOW_DELAY = 1.5  # Seconds before showing title
TITLE_HIDE_BEFORE_END = 3.5  # Seconds before video end to hide title

# Logging settings
LOG_RETENTION_DAYS = 7  # Keep logs for this many days
MAX_LOG_SIZE_MB = 50  # Maximum size per log file
ENABLE_FILE_LOGGING = True  # Can be disabled via environment

# Performance settings
VIDEO_CACHE_SIZE = 50  # Maximum videos to keep in cache
FINGERPRINT_DURATION = 120  # Seconds of audio to fingerprint

# Paths - will be initialized when script loads
TOOLS_DIR = None
LOGS_DIR = None

def init_paths(cache_directory: str):
    """Initialize paths based on cache directory from script properties."""
    global TOOLS_DIR, LOGS_DIR
    
    if cache_directory:
        cache_path = Path(cache_directory)
        TOOLS_DIR = cache_path / 'tools'
        LOGS_DIR = cache_path / 'logs'
        
        # Ensure directories exist
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
