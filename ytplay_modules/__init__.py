"""
OBS YouTube Player Modules Package.

This package contains all the modular components for the OBS YouTube Player.
The modules are designed to be shared across multiple script instances while
maintaining complete state isolation.

Key modules:
- main: Entry points for OBS script interface
- state: Thread-safe state management with per-script isolation
- config: Configuration constants and defaults
- logger: Thread-aware logging system
- ui: User interface property definitions
- tools: yt-dlp and FFmpeg management
- playlist: YouTube playlist synchronization
- download: Video download management
- metadata: Artist/song extraction (Gemini API and fallback)
- normalize: Audio normalization to -14 LUFS
- playback: Video playback control
- scene: OBS scene and source management
- cache: File caching and management
"""

__version__ = "4.0.0"
__author__ = "OBS YouTube Player Contributors"

# Module imports for convenience
from .config import SCRIPT_VERSION
from .logger import log
from .state import get_state, set_thread_script_context

__all__ = [
    'SCRIPT_VERSION',
    'log',
    'get_state',
    'set_thread_script_context'
]
