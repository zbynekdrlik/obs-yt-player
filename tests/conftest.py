"""
Pytest configuration and shared fixtures for OBS YouTube Player tests.

CRITICAL: This file injects the mock obspython module into sys.modules
BEFORE any ytplay_modules are imported. This must happen first!
"""

import subprocess
import sys
from pathlib import Path

# =============================================================================
# MOCK WINDOWS-SPECIFIC SUBPROCESS ATTRIBUTES FOR LINUX TESTING
# =============================================================================
# These are Windows-only but the code uses them. Mock them on Linux.
if not hasattr(subprocess, "STARTUPINFO"):

    class MockSTARTUPINFO:
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = 0

    subprocess.STARTUPINFO = MockSTARTUPINFO
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0

# =============================================================================
# MOCK OBSPYTHON INJECTION - MUST BE FIRST!
# =============================================================================

# Add the tests directory to path so we can import mocks
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))

# Import and inject mock obspython BEFORE any other imports
from mocks import obspython as mock_obs

sys.modules["obspython"] = mock_obs

# Now add the main source directory to path
YTPLAY_DIR = PROJECT_ROOT / "yt-player-main"
sys.path.insert(0, str(YTPLAY_DIR))

# =============================================================================
# STANDARD IMPORTS (after mock injection)
# =============================================================================

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

# =============================================================================
# AUTOUSE FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def reset_obs_mock():
    """
    Reset the mock OBS state before and after each test.
    This ensures test isolation.
    """
    mock_obs.reset()
    yield
    mock_obs.reset()


@pytest.fixture(autouse=True)
def reset_state_module():
    """
    Reset the ytplay_modules.state module between tests.
    This ensures no state leaks between tests.
    """
    try:
        from ytplay_modules import state
        from ytplay_modules.config import (
            DEFAULT_PLAYLIST_URL,
            DEFAULT_CACHE_DIR,
            DEFAULT_PLAYBACK_MODE,
            DEFAULT_AUDIO_ONLY_MODE,
        )

        # Reset all module-level state variables directly
        with state._state_lock:
            # Configuration state
            state._playlist_url = DEFAULT_PLAYLIST_URL
            state._cache_dir = DEFAULT_CACHE_DIR
            state._gemini_api_key = None
            state._playback_mode = DEFAULT_PLAYBACK_MODE
            state._audio_only_mode = DEFAULT_AUDIO_ONLY_MODE

            # System state flags
            state._tools_ready = False
            state._tools_logged_waiting = False
            state._scene_active = False
            state._is_playing = False
            state._stop_threads = False
            state._sync_on_startup_done = False
            state._stop_requested = False
            state._first_video_played = False

            # Playback state
            state._current_video_path = None
            state._current_playback_video_id = None
            state._loop_video_id = None

            # Data structures - clear in place
            state._cached_videos.clear()
            state._played_videos.clear()
            state._playlist_video_ids.clear()
            state.download_progress_milestones.clear()

    except (ImportError, AttributeError):
        pass
    yield

    # Also reset after test
    try:
        from ytplay_modules import state
        from ytplay_modules.config import (
            DEFAULT_PLAYLIST_URL,
            DEFAULT_CACHE_DIR,
            DEFAULT_PLAYBACK_MODE,
            DEFAULT_AUDIO_ONLY_MODE,
        )

        with state._state_lock:
            state._playlist_url = DEFAULT_PLAYLIST_URL
            state._cache_dir = DEFAULT_CACHE_DIR
            state._gemini_api_key = None
            state._playback_mode = DEFAULT_PLAYBACK_MODE
            state._audio_only_mode = DEFAULT_AUDIO_ONLY_MODE
            state._tools_ready = False
            state._tools_logged_waiting = False
            state._scene_active = False
            state._is_playing = False
            state._stop_threads = False
            state._sync_on_startup_done = False
            state._stop_requested = False
            state._first_video_played = False
            state._current_video_path = None
            state._current_playback_video_id = None
            state._loop_video_id = None
            state._cached_videos.clear()
            state._played_videos.clear()
            state._playlist_video_ids.clear()
            state.download_progress_milestones.clear()
    except (ImportError, AttributeError):
        pass


# =============================================================================
# DIRECTORY FIXTURES
# =============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Provide a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def temp_tools_dir(temp_cache_dir: Path) -> Path:
    """Provide a temporary tools directory for testing."""
    tools_dir = temp_cache_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    return tools_dir


@pytest.fixture
def temp_logs_dir(temp_cache_dir: Path) -> Path:
    """Provide a temporary logs directory for testing."""
    logs_dir = temp_cache_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================


@pytest.fixture
def sample_video_info() -> dict[str, Any]:
    """Provide sample video info for testing."""
    return {
        "path": "/cache/Song_Artist_dQw4w9WgXcQ_normalized.mp4",
        "song": "Never Gonna Give You Up",
        "artist": "Rick Astley",
        "normalized": True,
        "gemini_failed": False,
    }


@pytest.fixture
def sample_playlist_data() -> list[dict[str, Any]]:
    """Provide sample YouTube playlist data."""
    return [
        {"id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up", "duration": 213},
        {"id": "9bZkp7q19f0", "title": "PSY - GANGNAM STYLE", "duration": 252},
        {"id": "kJQP7kiw5Fk", "title": "Luis Fonsi - Despacito ft. Daddy Yankee", "duration": 282},
    ]


@pytest.fixture
def sample_gemini_response() -> dict[str, Any]:
    """Provide sample Gemini API response."""
    return {
        "candidates": [
            {"content": {"parts": [{"text": '{"artist": "Rick Astley", "song": "Never Gonna Give You Up"}'}]}}
        ]
    }


@pytest.fixture
def sample_cached_videos() -> dict[str, dict]:
    """Provide sample cached videos dictionary."""
    return {
        "dQw4w9WgXcQ": {
            "path": "/cache/Never_Gonna_Give_You_Up_Rick_Astley_dQw4w9WgXcQ_normalized.mp4",
            "song": "Never Gonna Give You Up",
            "artist": "Rick Astley",
            "normalized": True,
            "gemini_failed": False,
        },
        "9bZkp7q19f0": {
            "path": "/cache/GANGNAM_STYLE_PSY_9bZkp7q19f0_normalized.mp4",
            "song": "GANGNAM STYLE",
            "artist": "PSY",
            "normalized": True,
            "gemini_failed": False,
        },
    }


# =============================================================================
# OBS MOCK CONFIGURATION FIXTURES
# =============================================================================


@pytest.fixture
def obs_with_scene():
    """Configure mock OBS with a basic scene setup."""
    mock_obs.set_current_scene_name("ytplay")
    mock_obs.create_source("ytplay", "scene")
    mock_obs.create_source("ytplay_video", "ffmpeg_source")
    mock_obs.create_source("ytplay_title", "text_gdiplus")
    return mock_obs


@pytest.fixture
def obs_with_nested_scene():
    """Configure mock OBS with nested scene setup."""
    mock_obs.set_current_scene_name("MainScene")
    mock_obs.create_source("MainScene", "scene")
    mock_obs.create_source("ytplay", "scene")
    mock_obs.add_nested_scene("MainScene", "ytplay", visible=True)
    mock_obs.create_source("ytplay_video", "ffmpeg_source")
    mock_obs.create_source("ytplay_title", "text_gdiplus")
    return mock_obs


@pytest.fixture
def obs_playing():
    """Configure mock OBS in playing state."""
    mock_obs.set_current_scene_name("ytplay")
    mock_obs.set_media_state(mock_obs.OBS_MEDIA_STATE_PLAYING)
    mock_obs.set_media_duration(180000)  # 3 minutes
    mock_obs.set_media_time(30000)  # 30 seconds in
    mock_obs.create_source("ytplay", "scene")
    mock_obs.create_source("ytplay_video", "ffmpeg_source", {"local_file": "/cache/video.mp4"})
    return mock_obs


# =============================================================================
# SUBPROCESS MOCK FIXTURES
# =============================================================================


@pytest.fixture
def mock_subprocess_success(mocker):
    """Mock subprocess.run to return success."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="",
        stderr="",
    )
    return mock_run


@pytest.fixture
def mock_subprocess_popen(mocker):
    """Mock subprocess.Popen for streaming output."""
    mock_popen = mocker.patch("subprocess.Popen")
    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.stderr = iter([])
    mock_process.returncode = 0
    mock_process.wait.return_value = None
    mock_process.poll.return_value = 0
    mock_popen.return_value = mock_process
    return mock_popen


# =============================================================================
# NETWORK MOCK FIXTURES
# =============================================================================


@pytest.fixture
def mock_urlopen(mocker):
    """Mock urllib.request.urlopen."""
    mock_open = mocker.patch("urllib.request.urlopen")
    return mock_open


@pytest.fixture
def mock_urlopen_json(mock_urlopen, sample_gemini_response):
    """Mock urlopen to return JSON response."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(sample_gemini_response).encode()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response
    return mock_urlopen


# =============================================================================
# FILE SYSTEM MOCK FIXTURES
# =============================================================================


@pytest.fixture
def create_temp_video_file(temp_cache_dir: Path):
    """Factory fixture to create temporary video files."""

    def _create_video(filename: str, size_mb: int = 2) -> Path:
        video_path = temp_cache_dir / filename
        # Create a file of specified size (at least 1MB for valid video check)
        video_path.write_bytes(b"x" * (size_mb * 1024 * 1024))
        return video_path

    return _create_video


# =============================================================================
# STATE CONFIGURATION FIXTURES
# =============================================================================


@pytest.fixture
def configured_state(temp_cache_dir: Path):
    """Configure ytplay_modules.state with test values."""
    from ytplay_modules import state

    state.set_playlist_url("https://www.youtube.com/playlist?list=TEST")
    state.set_cache_dir(str(temp_cache_dir))
    state.set_playback_mode("continuous")
    state.set_audio_only_mode(False)
    state.set_tools_ready(True)

    return state


@pytest.fixture
def state_with_videos(configured_state, sample_cached_videos):
    """Configure state with cached videos."""
    for video_id, video_info in sample_cached_videos.items():
        configured_state.add_cached_video(video_id, video_info)
    return configured_state


# =============================================================================
# MARKER-BASED SKIPPING
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (mocked external deps)")
    config.addinivalue_line("markers", "obs: Tests requiring mock OBS module")
    config.addinivalue_line("markers", "slow: Tests that take significant time")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def assert_no_resource_leaks():
    """Helper to check for unreleased OBS resources."""
    # Check call log for unbalanced get/release calls
    calls = mock_obs.get_call_log()
    get_count = sum(1 for name, _, _ in calls if "get_source_by_name" in name)
    release_count = sum(1 for name, _, _ in calls if "source_release" in name)
    # Note: In real usage there may be intentional holds, so this is informational
    return get_count, release_count
