"""
Integration tests for ytplay_modules.reprocess

Tests for reprocessing videos with failed Gemini extraction.
Uses mocked subprocess and state for testing.
"""

import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock

# Mock Windows-specific subprocess attributes for Linux testing
if not hasattr(subprocess, 'STARTUPINFO'):
    subprocess.STARTUPINFO = MagicMock
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0


class TestGetVideoTitleFromYoutube:
    """Tests for get_video_title_from_youtube function."""

    @patch("subprocess.run")
    @patch("ytplay_modules.utils.get_ytdlp_path")
    def test_returns_title_on_success(self, mock_ytdlp_path, mock_run):
        """Should return video title on successful fetch."""
        from ytplay_modules.reprocess import get_video_title_from_youtube

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Test Video Title\n"
        )

        result = get_video_title_from_youtube("abc123")

        assert result == "Test Video Title"

    @patch("subprocess.run")
    @patch("ytplay_modules.utils.get_ytdlp_path")
    def test_returns_none_on_failure(self, mock_ytdlp_path, mock_run):
        """Should return None on fetch failure."""
        from ytplay_modules.reprocess import get_video_title_from_youtube

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )

        result = get_video_title_from_youtube("abc123")

        assert result is None

    @patch("subprocess.run")
    @patch("ytplay_modules.utils.get_ytdlp_path")
    def test_handles_timeout(self, mock_ytdlp_path, mock_run):
        """Should return None on timeout."""
        from ytplay_modules.reprocess import get_video_title_from_youtube

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 10)

        result = get_video_title_from_youtube("abc123")

        assert result is None


class TestFindVideosToReprocess:
    """Tests for find_videos_to_reprocess function."""

    def test_finds_videos_with_gemini_failed(self):
        """Should find videos with gemini_failed flag."""
        from ytplay_modules.reprocess import find_videos_to_reprocess
        from ytplay_modules.state import add_cached_video

        # Add a video with gemini_failed
        add_cached_video("video1", {
            "path": "/path/to/video1_normalized_gf.mp4",
            "song": "Test Song",
            "artist": "Test Artist",
            "gemini_failed": True
        })

        result = find_videos_to_reprocess()

        assert len(result) == 1
        assert result[0]['id'] == "video1"

    def test_skips_successful_videos(self):
        """Should skip videos without gemini_failed flag."""
        from ytplay_modules.reprocess import find_videos_to_reprocess
        from ytplay_modules.state import add_cached_video

        # Add successful video
        add_cached_video("video2", {
            "path": "/path/to/video2_normalized.mp4",
            "song": "Good Song",
            "artist": "Good Artist",
            "gemini_failed": False
        })

        result = find_videos_to_reprocess()

        # Should not include video2
        video_ids = [v['id'] for v in result]
        assert "video2" not in video_ids

    @patch("ytplay_modules.reprocess.get_video_title_from_youtube")
    def test_fetches_title_for_unknown_songs(self, mock_get_title):
        """Should fetch title from YouTube for unknown songs."""
        from ytplay_modules.reprocess import find_videos_to_reprocess
        from ytplay_modules.state import add_cached_video

        mock_get_title.return_value = "Fetched Title"

        add_cached_video("video3", {
            "path": "/path/to/video3.mp4",
            "song": "Unknown Song",
            "artist": "Unknown Artist",
            "gemini_failed": True
        })

        result = find_videos_to_reprocess()

        assert len(result) >= 1
        # Should have fetched the title
        mock_get_title.assert_called()


class TestReprocessVideo:
    """Tests for reprocess_video function."""

    @patch("ytplay_modules.reprocess.get_video_metadata")
    @patch("ytplay_modules.reprocess.get_gemini_api_key")
    def test_returns_false_without_api_key(self, mock_api_key, mock_metadata):
        """Should return False when no API key configured."""
        from ytplay_modules.reprocess import reprocess_video

        mock_api_key.return_value = None
        mock_metadata.return_value = ("Song", "Artist", "title", True)

        video_info = {
            'id': 'video1',
            'title': 'Test Title',
            'current_path': '/path/to/video.mp4',
            'song': 'Old Song',
            'artist': 'Old Artist'
        }

        result = reprocess_video(video_info)

        assert result is False

    @patch("ytplay_modules.reprocess.get_video_metadata")
    @patch("ytplay_modules.reprocess.get_gemini_api_key")
    def test_returns_false_when_gemini_fails_again(self, mock_api_key, mock_metadata):
        """Should return False when Gemini fails again."""
        from ytplay_modules.reprocess import reprocess_video

        mock_api_key.return_value = "test-api-key"
        mock_metadata.return_value = ("Song", "Artist", "title", True)  # gemini_failed=True

        video_info = {
            'id': 'video1',
            'title': 'Test Title',
            'current_path': '/path/to/video.mp4',
            'song': 'Old Song',
            'artist': 'Old Artist'
        }

        result = reprocess_video(video_info)

        assert result is False

    def test_renames_file_on_success(self, tmp_path):
        """Should rename file when Gemini succeeds on retry."""
        from ytplay_modules.reprocess import reprocess_video
        from ytplay_modules.state import set_gemini_api_key, set_cache_dir

        # Create actual temp file
        old_file = tmp_path / "old_file_gf.mp4"
        old_file.write_bytes(b"video content")

        video_info = {
            'id': 'video1',
            'title': 'Test Title',
            'current_path': str(old_file),
            'song': 'Old Song',
            'artist': 'Old Artist'
        }

        # Without a valid API key, Gemini will fail
        set_gemini_api_key("")
        set_cache_dir(str(tmp_path))

        result = reprocess_video(video_info)

        # Without valid API key, should return False
        assert result is False


class TestReprocessWorker:
    """Tests for reprocess_worker function."""

    @patch("ytplay_modules.reprocess.find_videos_to_reprocess")
    @patch("ytplay_modules.reprocess.get_gemini_api_key")
    @patch("ytplay_modules.reprocess.is_tools_ready")
    @patch("ytplay_modules.reprocess.should_stop_threads")
    @patch("time.sleep")
    def test_skips_when_no_api_key(
        self, mock_sleep, mock_stop, mock_tools_ready, mock_api_key, mock_find
    ):
        """Should skip reprocessing when no API key."""
        from ytplay_modules.reprocess import reprocess_worker

        mock_stop.side_effect = [False, False, False]  # Don't stop
        mock_tools_ready.return_value = True
        mock_api_key.return_value = None

        reprocess_worker()

        # Should not try to find videos
        mock_find.assert_not_called()

    @patch("ytplay_modules.reprocess.find_videos_to_reprocess")
    @patch("ytplay_modules.reprocess.get_gemini_api_key")
    @patch("ytplay_modules.reprocess.is_tools_ready")
    @patch("ytplay_modules.reprocess.should_stop_threads")
    @patch("time.sleep")
    def test_processes_videos_when_api_key_present(
        self, mock_sleep, mock_stop, mock_tools_ready, mock_api_key, mock_find
    ):
        """Should process videos when API key is present."""
        from ytplay_modules.reprocess import reprocess_worker

        mock_stop.return_value = False
        mock_tools_ready.return_value = True
        mock_api_key.return_value = "test-api-key"
        mock_find.return_value = []  # No videos to process

        reprocess_worker()

        mock_find.assert_called_once()


class TestStartReprocessThread:
    """Tests for start_reprocess_thread function."""

    @patch("threading.Thread")
    def test_starts_thread(self, mock_thread_class):
        """Should start reprocess thread."""
        from ytplay_modules import reprocess
        from ytplay_modules.reprocess import start_reprocess_thread

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_thread_class.return_value = mock_thread

        # Reset thread
        reprocess._reprocess_thread = None

        start_reprocess_thread()

        mock_thread.start.assert_called_once()

    @patch("threading.Thread")
    def test_does_not_start_if_already_running(self, mock_thread_class):
        """Should not start thread if already running."""
        from ytplay_modules import reprocess
        from ytplay_modules.reprocess import start_reprocess_thread

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        reprocess._reprocess_thread = mock_thread

        start_reprocess_thread()

        # Should not create new thread
        mock_thread_class.assert_not_called()
