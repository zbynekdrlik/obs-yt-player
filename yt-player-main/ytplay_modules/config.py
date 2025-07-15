"""
Configuration constants for OBS YouTube Player.
Central location for all script settings and constants.
"""

import os
from pathlib import Path

# Version - INCREMENT WITH EVERY CODE CHANGE
SCRIPT_VERSION = "4.1.1"  # Fixed pre-loaded video tracking in played videos list

# Dynamic script detection - works with any script name
# Look for .py file in parent directory that's not __init__.py
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = None
SCRIPT_NAME = None

# Find the main script file dynamically
for file in os.listdir(SCRIPT_DIR):
    if file.endswith('.py') and not file.startswith('_'):
        SCRIPT_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, file))
        SCRIPT_NAME = os.path.splitext(file)[0]
        break

# Fallback if no script found (shouldn't happen)
if not SCRIPT_PATH:
    SCRIPT_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, 'ytplay.py'))
    SCRIPT_NAME = 'ytplay'

# Default settings
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U"
DEFAULT_CACHE_DIR = os.path.join(SCRIPT_DIR, "cache")

# Playback behavior modes
PLAYBACK_MODE_CONTINUOUS = "continuous"  # Play videos forever (default)
PLAYBACK_MODE_SINGLE = "single"  # Play only first video and stop
PLAYBACK_MODE_LOOP = "loop"  # Loop the first video
DEFAULT_PLAYBACK_MODE = PLAYBACK_MODE_CONTINUOUS

# Audio-only mode settings
DEFAULT_AUDIO_ONLY_MODE = False

# OBS Scene and Source names
SCENE_NAME = SCRIPT_NAME  # Scene name matches script filename without extension

# Dynamic source names - prefixed with scene name to ensure uniqueness
MEDIA_SOURCE_NAME = f"{SCENE_NAME}_video"
TEXT_SOURCE_NAME = f"{SCENE_NAME}_title"
OPACITY_FILTER_NAME = "Title Opacity"

# Tool settings
TOOLS_SUBDIR = "tools"
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"

# Timing intervals (milliseconds)
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
TOOLS_CHECK_INTERVAL = 60  # Retry tools download every 60 seconds

# Video settings
MAX_RESOLUTION = "1440"
MIN_VIDEO_HEIGHT = "144"  # Minimum video quality for audio-only mode

# Network timeouts (seconds)
DOWNLOAD_TIMEOUT = 600  # 10 minutes timeout for downloads
NORMALIZE_TIMEOUT = 300  # 5 minutes timeout for normalization

# URLs for tool downloads
YTDLP_URL_BASE = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_WIN = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# For Windows tools.py compatibility
YTDLP_URL = YTDLP_URL_WIN
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

# FFmpeg URLs by platform (for future cross-platform support)
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# Title opacity transition settings
TITLE_FADE_DURATION = 1000  # Total duration for fade (milliseconds)
TITLE_FADE_STEPS = 20  # Number of steps in the fade
TITLE_FADE_INTERVAL = TITLE_FADE_DURATION // TITLE_FADE_STEPS  # Time between steps

# Gemini API settings
GEMINI_API_KEY_PROPERTY = "gemini_api_key"
