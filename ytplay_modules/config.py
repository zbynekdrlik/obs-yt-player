"""
Configuration constants for OBS YouTube Player.
"""

# Script version
SCRIPT_VERSION = "4.0.6"

# Scene and source names
MEDIA_SOURCE_NAME = "YouTube Player Media"
TEXT_SOURCE_NAME = "YouTube Player Title"

# Download settings
DOWNLOAD_CHECK_INTERVAL = 30 * 1000  # 30 seconds in milliseconds
NORMALIZATION_THREADS = 2  # Number of parallel normalization threads

# Playlist sync settings
PLAYLIST_SYNC_INTERVAL = 300 * 1000  # 5 minutes in milliseconds
SYNC_ON_STARTUP_DELAY = 10 * 1000   # 10 seconds delay before first sync

# Progress tracking
PROGRESS_LOG_POINTS = [10, 25, 50, 75, 90]  # Log at these percentages

# Audio normalization
TARGET_LUFS = -14.0  # YouTube standard

# Playback settings
PLAYBACK_CHECK_INTERVAL = 500  # 500ms check interval
TITLE_SHOW_DELAY = 3.0  # Seconds to wait before showing title
TITLE_CLEAR_BEFORE_END = 5.0  # Seconds before end to clear title

# Scene check delay
SCENE_CHECK_DELAY = 3000  # 3 seconds in milliseconds

# Playback modes
PLAYBACK_MODE_CONTINUOUS = "continuous"
PLAYBACK_MODE_SINGLE = "single"
PLAYBACK_MODE_LOOP = "loop"

# Default settings
DEFAULT_PLAYBACK_MODE = PLAYBACK_MODE_CONTINUOUS
DEFAULT_AUDIO_ONLY_MODE = False

# Tool URLs
TOOLS_BASE_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

# Error retry settings
MAX_DOWNLOAD_RETRIES = 3
RETRY_DELAY = 60  # seconds

# File size limits
MAX_VIDEO_SIZE_MB = 500  # Maximum video size to download
MIN_FREE_SPACE_GB = 1  # Minimum free space required

# Metadata settings
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_TIMEOUT = 30  # seconds
GEMINI_MAX_RETRIES = 2
GEMINI_RATE_LIMIT_DELAY = 60  # seconds

# Cache cleanup
TEMP_FILE_MAX_AGE_HOURS = 24  # Clean up temp files older than this
CACHE_CLEANUP_INTERVAL = 3600 * 1000  # 1 hour in milliseconds

# Thread management
THREAD_SHUTDOWN_TIMEOUT = 5  # seconds to wait for threads to stop

# UI settings
WARNING_UPDATE_INTERVAL = 1000  # 1 second in milliseconds

# Reprocess settings
REPROCESS_CHECK_INTERVAL = 300 * 1000  # 5 minutes
REPROCESS_BATCH_SIZE = 5  # Number of videos to reprocess at once
