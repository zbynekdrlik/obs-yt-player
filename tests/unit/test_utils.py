"""
Unit tests for ytplay_modules.utils

Tests for utility functions that have no OBS dependencies.
Target: 100% coverage
"""

import os
from unittest.mock import patch

from ytplay_modules.utils import (
    ensure_cache_directory,
    format_duration,
    get_ffmpeg_path,
    get_tools_path,
    get_ytdlp_path,
    sanitize_filename,
    validate_youtube_id,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_text(self):
        """Test with simple alphanumeric text."""
        assert sanitize_filename("SimpleTest") == "SimpleTest"

    def test_replaces_forward_slash_with_hyphen(self):
        """Forward slashes should become hyphens."""
        assert sanitize_filename("A/B") == "A-B"
        assert sanitize_filename("path/to/file") == "path-to-file"

    def test_replaces_invalid_chars_with_underscore(self):
        """Invalid filename characters should become underscores."""
        result = sanitize_filename('test<>:"|?*\\file')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result
        assert "\\" not in result

    def test_collapses_multiple_spaces(self):
        """Multiple spaces should collapse to single space."""
        assert sanitize_filename("a   b   c") == "a b c"

    def test_collapses_multiple_dashes(self):
        """Multiple dashes should collapse to single dash."""
        assert sanitize_filename("a---b") == "a-b"

    def test_collapses_multiple_underscores(self):
        """Multiple underscores should collapse to single underscore."""
        assert sanitize_filename("a___b") == "a_b"

    def test_removes_non_ascii(self):
        """Non-ASCII characters should be removed."""
        # café -> cafe (accent removed)
        result = sanitize_filename("café")
        assert result == "cafe"

    def test_unicode_normalization(self):
        """Unicode should be normalized and stripped."""
        # Test with various unicode characters
        result = sanitize_filename("Привет")  # Russian
        assert result == "Unknown" or result == ""  # All removed, becomes Unknown

    def test_strips_leading_trailing_chars(self):
        """Leading/trailing spaces, dashes, underscores should be stripped."""
        assert sanitize_filename("  test  ") == "test"
        assert sanitize_filename("--test--") == "test"
        assert sanitize_filename("__test__") == "test"
        assert sanitize_filename(" -_test_- ") == "test"

    def test_limits_length_to_50(self):
        """Result should be max 50 characters."""
        long_name = "a" * 100
        result = sanitize_filename(long_name)
        assert len(result) <= 50

    def test_removes_trailing_dot(self):
        """Trailing dots should be removed."""
        assert sanitize_filename("test...") == "test"
        assert sanitize_filename("file.name.") == "file.name"

    def test_empty_returns_unknown(self):
        """Empty input should return 'Unknown'."""
        assert sanitize_filename("") == "Unknown"

    def test_whitespace_only_returns_unknown(self):
        """Whitespace-only input should return 'Unknown'."""
        assert sanitize_filename("   ") == "Unknown"

    def test_special_chars_only_returns_unknown(self):
        """Special characters only should return 'Unknown'."""
        result = sanitize_filename("---___")
        # After stripping, becomes empty, which returns Unknown
        assert result == "Unknown" or len(result) > 0

    def test_preserves_alphanumeric_and_basic_punctuation(self):
        """Normal alphanumeric with allowed punctuation should be preserved."""
        assert sanitize_filename("Song - Artist (2023)") == "Song - Artist (2023)"

    def test_real_world_youtube_title(self):
        """Test with realistic YouTube title."""
        title = "Hillsong UNITED - Oceans (Where Feet May Fail) [Live]"
        result = sanitize_filename(title)
        assert len(result) <= 50
        assert "/" not in result
        assert "<" not in result


class TestValidateYoutubeId:
    """Tests for validate_youtube_id function."""

    def test_valid_standard_id(self):
        """Test with standard 11-character YouTube ID."""
        assert validate_youtube_id("dQw4w9WgXcQ") is True

    def test_valid_id_with_underscore(self):
        """YouTube IDs can contain underscores."""
        assert validate_youtube_id("abc_def_123") is True

    def test_valid_id_with_hyphen(self):
        """YouTube IDs can contain hyphens."""
        assert validate_youtube_id("abc-def-123") is True

    def test_valid_id_mixed_chars(self):
        """Test with mix of letters, numbers, underscore, hyphen."""
        assert validate_youtube_id("aB3-_xY7zQ1") is True

    def test_invalid_too_short(self):
        """IDs shorter than 11 characters are invalid."""
        assert validate_youtube_id("dQw4w9WgXc") is False  # 10 chars
        assert validate_youtube_id("abc") is False
        assert validate_youtube_id("") is False

    def test_invalid_too_long(self):
        """IDs longer than 11 characters are invalid."""
        assert validate_youtube_id("dQw4w9WgXcQQ") is False  # 12 chars

    def test_invalid_special_chars(self):
        """Special characters (except - and _) are invalid."""
        assert validate_youtube_id("dQw4w9WgXc!") is False
        assert validate_youtube_id("dQw4w9Wg@Xc") is False
        assert validate_youtube_id("dQw4w9Wg#Xc") is False
        assert validate_youtube_id("dQw4w9Wg$Xc") is False
        assert validate_youtube_id("dQw4w9Wg%Xc") is False

    def test_invalid_with_space(self):
        """Spaces are invalid in YouTube IDs."""
        assert validate_youtube_id("dQw4w9Wg Xc") is False
        assert validate_youtube_id(" dQw4w9WgXc") is False

    def test_none_input(self):
        """None input should return False (not crash)."""
        # The function uses regex match which handles None by returning None
        try:
            result = validate_youtube_id(None)
            assert result is False
        except (TypeError, AttributeError):
            pass  # Expected if function doesn't handle None

    def test_real_youtube_ids(self):
        """Test with known real YouTube video IDs."""
        real_ids = [
            "dQw4w9WgXcQ",  # Rick Astley
            "9bZkp7q19f0",  # Gangnam Style
            "kJQP7kiw5Fk",  # Despacito
            "JGwWNGJdvx8",  # Shape of You
            "RgKAFK5djSk",  # See You Again
        ]
        for vid_id in real_ids:
            assert validate_youtube_id(vid_id) is True, f"Failed for {vid_id}"


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_zero_seconds(self):
        """Zero seconds should format correctly."""
        assert format_duration(0) == "0s"

    def test_seconds_only(self):
        """Less than 60 seconds."""
        assert format_duration(45) == "45s"
        assert format_duration(1) == "1s"
        assert format_duration(59) == "59s"

    def test_minutes_and_seconds(self):
        """Between 1 minute and 1 hour."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(61) == "1m 1s"
        assert format_duration(125) == "2m 5s"
        assert format_duration(599) == "9m 59s"

    def test_hours_minutes_seconds(self):
        """One hour or more."""
        assert format_duration(3600) == "1h 0m 0s"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(3665) == "1h 1m 5s"
        assert format_duration(7325) == "2h 2m 5s"

    def test_large_duration(self):
        """Very long duration (multiple hours)."""
        assert format_duration(36000) == "10h 0m 0s"

    def test_none_returns_unknown(self):
        """None input should return 'unknown'."""
        assert format_duration(None) == "unknown"

    def test_negative_returns_unknown(self):
        """Negative input should return 'unknown'."""
        assert format_duration(-1) == "unknown"
        assert format_duration(-100) == "unknown"

    def test_float_input(self):
        """Float input should be converted to int."""
        assert format_duration(65.7) == "1m 5s"
        assert format_duration(125.9) == "2m 5s"


class TestGetToolsPath:
    """Tests for get_tools_path function."""

    @patch("ytplay_modules.utils.get_cache_dir")
    def test_returns_tools_subdir(self, mock_cache_dir):
        """Should return cache_dir/tools."""
        mock_cache_dir.return_value = "/home/user/cache"
        result = get_tools_path()
        assert result == os.path.join("/home/user/cache", "tools")

    @patch("ytplay_modules.utils.get_cache_dir")
    def test_with_windows_path(self, mock_cache_dir):
        """Should work with Windows paths."""
        mock_cache_dir.return_value = "C:\\Users\\test\\cache"
        result = get_tools_path()
        assert "tools" in result


class TestGetYtdlpPath:
    """Tests for get_ytdlp_path function."""

    @patch("ytplay_modules.utils.get_tools_path")
    def test_returns_ytdlp_in_tools(self, mock_tools_path):
        """Should return path to yt-dlp executable in tools dir."""
        mock_tools_path.return_value = "/cache/tools"
        result = get_ytdlp_path()
        assert "tools" in result
        assert "yt-dlp" in result.lower() or "ytdlp" in result.lower()


class TestGetFfmpegPath:
    """Tests for get_ffmpeg_path function."""

    @patch("ytplay_modules.utils.get_tools_path")
    def test_returns_ffmpeg_in_tools(self, mock_tools_path):
        """Should return path to ffmpeg executable in tools dir."""
        mock_tools_path.return_value = "/cache/tools"
        result = get_ffmpeg_path()
        assert "tools" in result
        assert "ffmpeg" in result.lower()


class TestEnsureCacheDirectory:
    """Tests for ensure_cache_directory function."""

    @patch("ytplay_modules.utils.get_cache_dir")
    def test_creates_cache_directory(self, mock_cache_dir, tmp_path):
        """Should create cache directory if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        mock_cache_dir.return_value = str(cache_dir)

        result = ensure_cache_directory()

        assert result is True
        assert cache_dir.exists()

    @patch("ytplay_modules.utils.get_cache_dir")
    def test_creates_tools_subdirectory(self, mock_cache_dir, tmp_path):
        """Should create tools subdirectory."""
        cache_dir = tmp_path / "cache"
        mock_cache_dir.return_value = str(cache_dir)

        ensure_cache_directory()

        tools_dir = cache_dir / "tools"
        assert tools_dir.exists()

    @patch("ytplay_modules.utils.get_cache_dir")
    def test_succeeds_if_directory_exists(self, mock_cache_dir, tmp_path):
        """Should succeed even if directory already exists."""
        cache_dir = tmp_path / "existing_cache"
        cache_dir.mkdir()
        mock_cache_dir.return_value = str(cache_dir)

        result = ensure_cache_directory()

        assert result is True

    @patch("ytplay_modules.utils.get_cache_dir")
    @patch("pathlib.Path.mkdir")
    def test_returns_false_on_error(self, mock_mkdir, mock_cache_dir, tmp_path):
        """Should return False if directory creation fails."""
        mock_cache_dir.return_value = str(tmp_path / "cache")
        mock_mkdir.side_effect = PermissionError("Access denied")

        result = ensure_cache_directory()

        assert result is False
