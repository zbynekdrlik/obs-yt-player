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
def reset_state_module(tmp_path):
    """
    Reset the ytplay_modules.state module between tests.
    This ensures no state leaks between tests.
    Uses tmp_path to provide a valid cache directory for each test.
    """
    try:
        from ytplay_modules import state
        from ytplay_modules.config import (
            DEFAULT_PLAYLIST_URL,
            DEFAULT_PLAYBACK_MODE,
            DEFAULT_AUDIO_ONLY_MODE,
        )

        # Use tmp_path as cache dir so persistence works in tests
        test_cache_dir = str(tmp_path / "test_cache")

        # Reset all module-level state variables directly
        with state._state_lock:
            # Configuration state
            state._playlist_url = DEFAULT_PLAYLIST_URL
            state._cache_dir = test_cache_dir
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
            DEFAULT_PLAYBACK_MODE,
            DEFAULT_AUDIO_ONLY_MODE,
        )

        with state._state_lock:
            state._playlist_url = DEFAULT_PLAYLIST_URL
            state._cache_dir = test_cache_dir  # Use same temp dir
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
# TIMER TRACKING FIXTURES
# =============================================================================


class TimerTracker:
    """Track OBS timer add/remove calls for verification."""

    def __init__(self):
        self.active_timers = {}
        self.add_calls = []
        self.remove_calls = []

    def track_add(self, callback, interval):
        """Track a timer_add call."""
        timer_id = id(callback)
        self.active_timers[timer_id] = {"callback": callback, "interval": interval}
        self.add_calls.append((callback, interval))

    def track_remove(self, callback):
        """Track a timer_remove call."""
        timer_id = id(callback)
        self.active_timers.pop(timer_id, None)
        self.remove_calls.append(callback)

    def assert_no_leaks(self):
        """Assert all timers have been removed."""
        assert len(self.active_timers) == 0, f"Timer leaks detected: {list(self.active_timers.keys())}"

    def get_active_count(self):
        """Get count of active timers."""
        return len(self.active_timers)

    def reset(self):
        """Reset tracker state."""
        self.active_timers.clear()
        self.add_calls.clear()
        self.remove_calls.clear()


@pytest.fixture
def timer_tracker(mocker):
    """Fixture to track OBS timer lifecycle."""
    tracker = TimerTracker()

    # Patch timer_add to track calls
    original_timer_add = mock_obs.timer_add

    def tracked_timer_add(callback, interval):
        tracker.track_add(callback, interval)
        return original_timer_add(callback, interval)

    mocker.patch.object(mock_obs, "timer_add", side_effect=tracked_timer_add)

    # Patch timer_remove to track calls
    original_timer_remove = mock_obs.timer_remove

    def tracked_timer_remove(callback):
        tracker.track_remove(callback)
        return original_timer_remove(callback)

    mocker.patch.object(mock_obs, "timer_remove", side_effect=tracked_timer_remove)

    return tracker


# =============================================================================
# SUBPROCESS SIMULATION FIXTURES
# =============================================================================


class SubprocessSimulator:
    """Simulate subprocess behavior for testing."""

    def __init__(self):
        self.stdout_lines = []
        self.stderr_lines = []
        self.returncode = 0
        self.should_timeout = False
        self.timeout_after = None

    def set_output(self, stdout_lines=None, stderr_lines=None, returncode=0):
        """Set the simulated output."""
        self.stdout_lines = stdout_lines or []
        self.stderr_lines = stderr_lines or []
        self.returncode = returncode

    def simulate_progress(self, percentages):
        """Simulate download progress output."""
        self.stdout_lines = [f"[download] {p}% of ~100.00MiB at 1.00MiB/s" for p in percentages]

    def simulate_timeout(self, after_lines=5):
        """Simulate a timeout after N lines."""
        self.should_timeout = True
        self.timeout_after = after_lines


@pytest.fixture
def subprocess_simulator():
    """Fixture for controlled subprocess simulation."""
    return SubprocessSimulator()


@pytest.fixture
def mock_popen_with_simulator(mocker, subprocess_simulator):
    """Mock Popen with simulator control."""
    mock_popen = mocker.patch("subprocess.Popen")

    class MockProcess:
        def __init__(self):
            self._line_count = 0

        @property
        def stdout(self):
            for line in subprocess_simulator.stdout_lines:
                self._line_count += 1
                if subprocess_simulator.should_timeout and self._line_count > subprocess_simulator.timeout_after:
                    import subprocess

                    raise subprocess.TimeoutExpired("cmd", 60)
                yield line

        @property
        def returncode(self):
            return subprocess_simulator.returncode

        def wait(self, timeout=None):
            if subprocess_simulator.should_timeout:
                import subprocess

                raise subprocess.TimeoutExpired("cmd", timeout)
            return self.returncode

        def kill(self):
            pass

        def poll(self):
            return self.returncode

    mock_popen.return_value = MockProcess()
    return mock_popen


# =============================================================================
# VIDEO FILE FIXTURES
# =============================================================================


@pytest.fixture
def temp_normalized_video(temp_cache_dir):
    """Create a temporary normalized video file."""
    video_path = temp_cache_dir / "Test_Song_Test_Artist_dQw4w9WgXcQ_normalized.mp4"
    video_path.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB file
    return video_path


@pytest.fixture
def temp_gf_video(temp_cache_dir):
    """Create a temporary Gemini-failed video file."""
    video_path = temp_cache_dir / "Unknown_Unknown_9bZkp7q19f0_normalized_gf.mp4"
    video_path.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB file
    return video_path


@pytest.fixture
def multiple_cached_videos(temp_cache_dir):
    """Create multiple cached video files for testing."""
    videos = []
    for i, video_id in enumerate(["vid001", "vid002", "vid003", "vid004", "vid005"]):
        video_path = temp_cache_dir / f"Song{i}_Artist{i}_{video_id}_normalized.mp4"
        video_path.write_bytes(b"x" * (1024 * 1024))  # 1MB each
        videos.append(video_path)
    return videos


# =============================================================================
# THREADING FIXTURES
# =============================================================================


@pytest.fixture
def stop_threads_after_test():
    """Ensure threads are stopped after test."""
    yield
    try:
        from ytplay_modules import state

        state.set_stop_threads(True)
    except ImportError:
        pass


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


def create_mock_ytdlp_output(video_id, title, duration=180):
    """Create mock yt-dlp JSON output."""
    return {
        "id": video_id,
        "title": title,
        "duration": duration,
        "formats": [{"format_id": "22", "ext": "mp4", "height": 720}],
    }


def create_mock_ffmpeg_loudnorm_output(input_i=-23.0, input_tp=-1.0, input_lra=7.0):
    """Create mock FFmpeg loudnorm analysis output."""
    return f"""
[Parsed_loudnorm_0 @ 0x0] {{
    "input_i": "{input_i:.2f}",
    "input_tp": "{input_tp:.2f}",
    "input_lra": "{input_lra:.2f}",
    "input_thresh": "-33.00",
    "output_i": "-14.00",
    "output_tp": "-1.50",
    "output_lra": "7.00",
    "output_thresh": "-24.00",
    "normalization_type": "dynamic",
    "target_offset": "0.00"
}}
"""
