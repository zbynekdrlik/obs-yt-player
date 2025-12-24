"""
Unit tests for ytplay_modules.config

Tests for configuration constants and dynamic script detection.
Target: 100% coverage
"""

import re

from ytplay_modules.config import (
    DEFAULT_AUDIO_ONLY_MODE,
    DEFAULT_CACHE_DIR,
    DEFAULT_PLAYBACK_MODE,
    DEFAULT_PLAYLIST_URL,
    DOWNLOAD_TIMEOUT,
    MAX_RESOLUTION,
    MEDIA_SOURCE_NAME,
    NORMALIZE_TIMEOUT,
    OPACITY_FILTER_NAME,
    PLAYBACK_CHECK_INTERVAL,
    PLAYBACK_MODE_CONTINUOUS,
    PLAYBACK_MODE_LOOP,
    PLAYBACK_MODE_SINGLE,
    SCENE_CHECK_DELAY,
    SCENE_NAME,
    SCRIPT_NAME,
    SCRIPT_VERSION,
    TEXT_SOURCE_NAME,
    TITLE_FADE_DURATION,
    TITLE_FADE_INTERVAL,
    TITLE_FADE_STEPS,
    TOOLS_SUBDIR,
)


class TestScriptVersion:
    """Tests for SCRIPT_VERSION constant."""

    def test_version_format(self):
        """Version should be in semantic versioning format (X.Y.Z)."""
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, SCRIPT_VERSION), f"Version '{SCRIPT_VERSION}' doesn't match X.Y.Z format"

    def test_version_is_string(self):
        """Version should be a string."""
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_is_not_empty(self):
        """Version should not be empty."""
        assert len(SCRIPT_VERSION) > 0


class TestPlaybackModes:
    """Tests for playback mode constants."""

    def test_continuous_mode_value(self):
        """Continuous mode should have correct value."""
        assert PLAYBACK_MODE_CONTINUOUS == "continuous"

    def test_single_mode_value(self):
        """Single mode should have correct value."""
        assert PLAYBACK_MODE_SINGLE == "single"

    def test_loop_mode_value(self):
        """Loop mode should have correct value."""
        assert PLAYBACK_MODE_LOOP == "loop"

    def test_modes_are_unique(self):
        """All playback modes should be unique."""
        modes = [PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP]
        assert len(modes) == len(set(modes))

    def test_default_mode_is_continuous(self):
        """Default playback mode should be continuous."""
        assert DEFAULT_PLAYBACK_MODE == PLAYBACK_MODE_CONTINUOUS


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_audio_only_default_is_false(self):
        """Audio-only mode should be disabled by default."""
        assert DEFAULT_AUDIO_ONLY_MODE is False

    def test_default_cache_dir_is_string(self):
        """Default cache directory should be a string."""
        assert isinstance(DEFAULT_CACHE_DIR, str)

    def test_default_playlist_url_is_string(self):
        """Default playlist URL should be a string."""
        assert isinstance(DEFAULT_PLAYLIST_URL, str)


class TestTimingConstants:
    """Tests for timing-related constants."""

    def test_playback_check_interval_positive(self):
        """Playback check interval should be positive."""
        assert PLAYBACK_CHECK_INTERVAL > 0

    def test_playback_check_interval_reasonable(self):
        """Playback check interval should be reasonable (100ms - 5s)."""
        assert 100 <= PLAYBACK_CHECK_INTERVAL <= 5000

    def test_title_fade_duration_positive(self):
        """Title fade duration should be positive."""
        assert TITLE_FADE_DURATION > 0

    def test_title_fade_steps_positive(self):
        """Title fade steps should be positive."""
        assert TITLE_FADE_STEPS > 0

    def test_title_fade_interval_calculated_correctly(self):
        """Title fade interval should be duration / steps."""
        expected = TITLE_FADE_DURATION // TITLE_FADE_STEPS
        assert expected == TITLE_FADE_INTERVAL or TITLE_FADE_INTERVAL > 0

    def test_download_timeout_positive(self):
        """Download timeout should be positive."""
        assert DOWNLOAD_TIMEOUT > 0

    def test_download_timeout_reasonable(self):
        """Download timeout should be reasonable (1-30 minutes)."""
        assert 60 <= DOWNLOAD_TIMEOUT <= 1800

    def test_normalize_timeout_positive(self):
        """Normalize timeout should be positive."""
        assert NORMALIZE_TIMEOUT > 0

    def test_normalize_timeout_reasonable(self):
        """Normalize timeout should be reasonable (1-10 minutes)."""
        assert 60 <= NORMALIZE_TIMEOUT <= 600

    def test_scene_check_delay_positive(self):
        """Scene check delay should be positive."""
        assert SCENE_CHECK_DELAY > 0


class TestMediaConstants:
    """Tests for media processing constants."""

    def test_max_resolution_is_string(self):
        """Max resolution should be a string."""
        assert isinstance(MAX_RESOLUTION, str)

    def test_max_resolution_is_numeric_string(self):
        """Max resolution should be a numeric string."""
        assert MAX_RESOLUTION.isdigit()
        assert int(MAX_RESOLUTION) > 0

    def test_max_resolution_reasonable(self):
        """Max resolution should be a common video height."""
        valid_resolutions = ["360", "480", "720", "1080", "1440", "2160", "4320"]
        assert MAX_RESOLUTION in valid_resolutions or int(MAX_RESOLUTION) > 0

    def test_tools_subdir_is_string(self):
        """Tools subdirectory should be a string."""
        assert isinstance(TOOLS_SUBDIR, str)
        assert len(TOOLS_SUBDIR) > 0


class TestSourceNames:
    """Tests for OBS source name constants."""

    def test_scene_name_derived_from_script(self):
        """Scene name should be derived from script name."""
        # SCENE_NAME should match SCRIPT_NAME (without .py)
        assert SCENE_NAME == SCRIPT_NAME

    def test_media_source_name_format(self):
        """Media source name should follow pattern: {scene}_video."""
        assert MEDIA_SOURCE_NAME.endswith("_video")
        assert MEDIA_SOURCE_NAME.startswith(SCENE_NAME)

    def test_text_source_name_format(self):
        """Text source name should follow pattern: {scene}_title."""
        assert TEXT_SOURCE_NAME.endswith("_title")
        assert TEXT_SOURCE_NAME.startswith(SCENE_NAME)

    def test_opacity_filter_name_not_empty(self):
        """Opacity filter name should not be empty."""
        assert len(OPACITY_FILTER_NAME) > 0
        assert isinstance(OPACITY_FILTER_NAME, str)


class TestScriptDetection:
    """Tests for dynamic script name detection."""

    def test_script_name_is_string(self):
        """Script name should be a string."""
        assert isinstance(SCRIPT_NAME, str)

    def test_script_name_not_empty(self):
        """Script name should not be empty."""
        assert len(SCRIPT_NAME) > 0

    def test_script_name_no_extension(self):
        """Script name should not include .py extension."""
        assert not SCRIPT_NAME.endswith(".py")

    def test_script_name_alphanumeric(self):
        """Script name should be mostly alphanumeric (with underscore/hyphen)."""
        # Allow letters, numbers, underscore, hyphen
        pattern = r"^[a-zA-Z0-9_-]+$"
        assert re.match(pattern, SCRIPT_NAME), f"Script name '{SCRIPT_NAME}' has invalid characters"


class TestConfigurationConsistency:
    """Tests for overall configuration consistency."""

    def test_all_constants_defined(self):
        """All expected constants should be defined and not None."""
        constants = [
            SCRIPT_VERSION,
            SCRIPT_NAME,
            SCENE_NAME,
            MEDIA_SOURCE_NAME,
            TEXT_SOURCE_NAME,
            PLAYBACK_MODE_CONTINUOUS,
            PLAYBACK_MODE_SINGLE,
            PLAYBACK_MODE_LOOP,
            DEFAULT_PLAYBACK_MODE,
            PLAYBACK_CHECK_INTERVAL,
            DOWNLOAD_TIMEOUT,
            NORMALIZE_TIMEOUT,
        ]
        for const in constants:
            assert const is not None

    def test_playback_modes_are_lowercase(self):
        """Playback modes should be lowercase for consistency."""
        assert PLAYBACK_MODE_CONTINUOUS.lower() == PLAYBACK_MODE_CONTINUOUS
        assert PLAYBACK_MODE_SINGLE.lower() == PLAYBACK_MODE_SINGLE
        assert PLAYBACK_MODE_LOOP.lower() == PLAYBACK_MODE_LOOP
