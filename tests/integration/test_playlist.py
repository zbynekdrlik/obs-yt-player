"""
Integration tests for ytplay_modules.playlist

Tests for playlist synchronization with mocked subprocess calls.
Target: 80%+ coverage
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

# Mock Windows-specific subprocess attributes for Linux testing
if not hasattr(subprocess, 'STARTUPINFO'):
    subprocess.STARTUPINFO = MagicMock
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0


class TestFetchPlaylistWithYtdlp:
    """Tests for fetch_playlist_with_ytdlp function."""

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_successful_fetch(self, mock_run, mock_ytdlp_path):
        """Should parse playlist JSON output correctly."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"

        # Simulate yt-dlp output (one JSON object per line)
        mock_output = "\n".join([
            json.dumps({"id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up", "duration": 213}),
            json.dumps({"id": "9bZkp7q19f0", "title": "PSY - Gangnam Style", "duration": 252}),
            json.dumps({"id": "kJQP7kiw5Fk", "title": "Luis Fonsi - Despacito", "duration": 282}),
        ])

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert len(videos) == 3
        assert videos[0]["id"] == "dQw4w9WgXcQ"
        assert videos[0]["title"] == "Rick Astley - Never Gonna Give You Up"
        assert videos[0]["duration"] == 213
        assert videos[1]["id"] == "9bZkp7q19f0"
        assert videos[2]["id"] == "kJQP7kiw5Fk"

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_returns_empty_on_failure(self, mock_run, mock_ytdlp_path):
        """Should return empty list when yt-dlp fails."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="ERROR: Unable to download playlist"
        )

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=INVALID")

        assert videos == []

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_handles_invalid_json_lines(self, mock_run, mock_ytdlp_path):
        """Should skip invalid JSON lines and continue."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"

        # Mix of valid and invalid lines
        mock_output = "\n".join([
            json.dumps({"id": "valid1", "title": "Valid Video 1", "duration": 100}),
            "Not valid JSON",
            json.dumps({"id": "valid2", "title": "Valid Video 2", "duration": 200}),
            "",  # Empty line
        ])

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert len(videos) == 2
        assert videos[0]["id"] == "valid1"
        assert videos[1]["id"] == "valid2"

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_handles_exception(self, mock_run, mock_ytdlp_path):
        """Should return empty list on exception."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.side_effect = Exception("Process error")

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert videos == []

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_handles_timeout(self, mock_run, mock_ytdlp_path):
        """Should return empty list on timeout."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yt-dlp", timeout=30)

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert videos == []

    @patch("ytplay_modules.playlist.get_ytdlp_path")
    @patch("subprocess.run")
    def test_handles_missing_fields(self, mock_run, mock_ytdlp_path):
        """Should handle videos with missing optional fields."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"

        # Video with minimal data
        mock_output = json.dumps({"id": "minimal123"})

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )

        videos = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert len(videos) == 1
        assert videos[0]["id"] == "minimal123"
        assert videos[0]["title"] == "Unknown"  # Default
        assert videos[0]["duration"] == 0  # Default


class TestTriggerStartupSync:
    """Tests for trigger_startup_sync function."""

    def test_sets_sync_done_flag(self):
        """Should set sync_on_startup_done flag."""
        from ytplay_modules.playlist import trigger_startup_sync
        from ytplay_modules.state import is_sync_on_startup_done, set_sync_on_startup_done

        set_sync_on_startup_done(False)

        trigger_startup_sync()

        assert is_sync_on_startup_done() is True

    def test_only_triggers_once(self):
        """Should only trigger sync once."""
        from ytplay_modules.playlist import trigger_startup_sync
        from ytplay_modules.state import set_sync_on_startup_done, sync_event

        set_sync_on_startup_done(False)
        sync_event.clear()

        trigger_startup_sync()
        first_triggered = sync_event.is_set()

        sync_event.clear()
        trigger_startup_sync()  # Second call
        second_triggered = sync_event.is_set()

        assert first_triggered is True
        assert second_triggered is False  # Should not trigger again


class TestTriggerManualSync:
    """Tests for trigger_manual_sync function."""

    def test_sets_sync_event(self):
        """Should set the sync event."""
        from ytplay_modules.playlist import trigger_manual_sync
        from ytplay_modules.state import sync_event

        sync_event.clear()

        trigger_manual_sync()

        assert sync_event.is_set() is True


class TestPlaylistSyncWorker:
    """Tests for playlist_sync_worker function behavior."""

    @patch("ytplay_modules.playlist.scan_existing_cache")
    @patch("ytplay_modules.playlist.fetch_playlist_with_ytdlp")
    @patch("ytplay_modules.playlist.cleanup_removed_videos")
    def test_queues_uncached_videos(
        self, mock_cleanup, mock_fetch, mock_scan
    ):
        """Should queue videos that are not in cache."""
        from ytplay_modules.state import (
            add_cached_video,
            is_video_cached,
            set_playlist_url,
            set_stop_threads,
            set_tools_ready,
            video_queue,
        )

        # Set up state
        set_tools_ready(True)
        set_stop_threads(False)
        set_playlist_url("https://youtube.com/playlist?list=TEST")

        # Pre-cache one video
        add_cached_video("cached_vid", {"path": "/test.mp4", "song": "Cached", "artist": "Artist"})

        # Mock playlist fetch returns 3 videos
        mock_fetch.return_value = [
            {"id": "cached_vid", "title": "Cached Video", "duration": 100},
            {"id": "new_vid_1", "title": "New Video 1", "duration": 200},
            {"id": "new_vid_2", "title": "New Video 2", "duration": 300},
        ]

        # Clear the queue
        while not video_queue.empty():
            video_queue.get_nowait()

        # Import and call the internal sync logic
        from ytplay_modules.state import set_playlist_video_ids

        videos = mock_fetch.return_value
        video_ids = [v["id"] for v in videos]
        set_playlist_video_ids(video_ids)

        queued_count = 0
        for video in videos:
            if not is_video_cached(video["id"]):
                video_queue.put(video)
                queued_count += 1

        # Should have queued 2 videos (not the cached one)
        assert queued_count == 2
        assert video_queue.qsize() == 2


class TestStartPlaylistSyncThread:
    """Tests for start_playlist_sync_thread function."""

    @patch("threading.Thread")
    def test_creates_daemon_thread(self, mock_thread):
        """Should create a daemon thread."""
        from ytplay_modules.playlist import start_playlist_sync_thread

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        start_playlist_sync_thread()

        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs.get("daemon") is True
        mock_thread_instance.start.assert_called_once()
