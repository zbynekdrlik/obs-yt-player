"""
Configuration constants and settings for OBS YouTube Player.
"""

import os
from pathlib import Path

# Version - INCREMENT WITH EVERY CODE CHANGE
SCRIPT_VERSION = "2.0.0"  # Major version for modular refactoring

# Get script information from environment or defaults
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ytfast.py'))
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# Default settings
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U"
DEFAULT_CACHE_DIR = os.path.join(SCRIPT_DIR, f"{SCRIPT_NAME}-cache")

# Scene and source names based on script name
SCENE_NAME = SCRIPT_NAME
MEDIA_SOURCE_NAME = "video"
TEXT_SOURCE_NAME = "title"

# Directory names
TOOLS_SUBDIR = "tools"

# Tool filenames
YTDLP_FILENAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_FILENAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
FPCALC_FILENAME = "fpcalc.exe" if os.name == 'nt' else "fpcalc"

# Timing intervals (milliseconds)
PLAYBACK_CHECK_INTERVAL = 1000  # 1 second
SCENE_CHECK_DELAY = 3000  # 3 seconds after startup
TOOLS_CHECK_INTERVAL = 60  # 60 seconds retry for tools

# Processing limits
MAX_RESOLUTION = "1440"
DOWNLOAD_TIMEOUT = 600  # 10 minutes
NORMALIZE_TIMEOUT = 300  # 5 minutes

# AcoustID settings
ACOUSTID_API_KEY = "RXS1uld515"
ACOUSTID_ENABLED = True

# Tool download URLs
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_WIN = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# FFmpeg URLs by platform
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# fpcalc (Chromaprint) URLs by platform
FPCALC_URLS = {
    "win32": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-windows-x86_64.zip",
    "darwin": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-macos-x86_64.tar.gz",
    "linux": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-linux-x86_64.tar.gz"
}
