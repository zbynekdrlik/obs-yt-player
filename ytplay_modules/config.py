"""
Configuration constants for OBS YouTube Player.
Central location for all script settings and constants.
"""

import os
from pathlib import Path

# Version - INCREMENT WITH EVERY CODE CHANGE
SCRIPT_VERSION = "4.0.3"  # Working on complete removal of ytfast_modules directory

# Default settings
DEFAULT_PLAYLIST_URL = ""  # Empty by default - user must configure
DEFAULT_CACHE_DIR = None  # Will be set dynamically based on script name

# Playback behavior modes
PLAYBACK_MODE_CONTINUOUS = "continuous"  # Play videos forever (default)
PLAYBACK_MODE_SINGLE = "single"  # Play only first video and stop
PLAYBACK_MODE_LOOP = "loop"  # Loop the first video
DEFAULT_PLAYBACK_MODE = PLAYBACK_MODE_CONTINUOUS

# Audio-only mode settings
DEFAULT_AUDIO_ONLY_MODE = False

# OBS Source names (scene name is dynamic based on script name)
MEDIA_SOURCE_NAME = "video"
TEXT_SOURCE_NAME = "title"
OPACITY_FILTER_NAME = "Title Opacity"

# Tool settings
TOOLS_SUBDIR = "tools"
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"

# Timing intervals (milliseconds)
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
TOOLS_CHECK_INTERVAL = 60  # Retry tools download every 60 seconds

# Title display settings
TITLE_SHOW_DELAY = 3  # Seconds after video starts to show title
TITLE_CLEAR_BEFORE_END = 10  # Seconds before video ends to clear title

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
