"""
Tests for playlist sync worker functionality.
Covers the playlist_sync_worker event loop and integration with cache.
"""

import threading
import time
from unittest.mock import MagicMock


class TestPlaylistSyncWorker:
    """Tests for playlist_sync_worker function."""

    def test_worker_exits_on_stop_threads(self, configured_state):
        """Worker should exit when stop_threads is set."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_stop_threads(True)

        # Run worker in thread - should exit immediately
        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()
        thread.join(timeout=2)

        assert not thread.is_alive(), "Worker should have exited"

    def test_worker_waits_for_sync_event(self, configured_state):
        """Worker should wait for sync event."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        # Don't set the sync event
        state.set_stop_threads(False)

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        # Wait briefly - worker should still be waiting
        time.sleep(0.5)
        assert thread.is_alive(), "Worker should be waiting for sync event"

        # Signal stop
        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

    def test_worker_requires_tools_ready(self, configured_state, mocker):
        """Worker should skip sync if tools not ready."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_tools_ready(False)
        state.set_stop_threads(False)

        mock_log = mocker.patch("ytplay_modules.playlist.log")
        mock_fetch = mocker.patch("ytplay_modules.playlist.fetch_playlist_with_ytdlp")

        # Trigger sync event
        state.sync_event.set()

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        # Wait for one iteration
        time.sleep(0.5)

        # Stop the worker
        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

        # Should have logged tools not ready
        mock_log.assert_any_call("Sync requested but tools not ready")
        mock_fetch.assert_not_called()

    def test_worker_processes_playlist_successfully(self, configured_state, mocker):
        """Worker should process playlist when tools ready."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_tools_ready(True)
        state.set_stop_threads(False)

        # Mock dependencies
        mocker.patch("ytplay_modules.playlist.scan_existing_cache")
        mocker.patch("ytplay_modules.state.initialize_played_videos")
        mocker.patch("ytplay_modules.playlist.cleanup_removed_videos")

        mock_fetch = mocker.patch("ytplay_modules.playlist.fetch_playlist_with_ytdlp")
        mock_fetch.return_value = [
            {"id": "video1", "title": "Video 1", "duration": 180},
            {"id": "video2", "title": "Video 2", "duration": 200},
        ]

        # Trigger sync
        state.sync_event.set()

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        # Wait for processing
        time.sleep(0.5)

        # Stop worker
        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

        # Verify playlist IDs were set
        playlist_ids = state.get_playlist_video_ids()
        assert "video1" in playlist_ids
        assert "video2" in playlist_ids

    def test_worker_queues_only_uncached_videos(self, configured_state, mocker):
        """Worker should only queue videos not already in cache."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_tools_ready(True)
        state.set_stop_threads(False)

        # Pre-cache one video
        state.add_cached_video("video1", {"path": "/test.mp4", "song": "Test", "artist": "Artist"})

        mocker.patch("ytplay_modules.playlist.scan_existing_cache")
        mocker.patch("ytplay_modules.state.initialize_played_videos")
        mocker.patch("ytplay_modules.playlist.cleanup_removed_videos")

        mock_fetch = mocker.patch("ytplay_modules.playlist.fetch_playlist_with_ytdlp")
        mock_fetch.return_value = [
            {"id": "video1", "title": "Video 1", "duration": 180},  # Already cached
            {"id": "video2", "title": "Video 2", "duration": 200},  # Not cached
        ]

        mock_log = mocker.patch("ytplay_modules.playlist.log")

        # Trigger sync
        state.sync_event.set()

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        time.sleep(0.5)

        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

        # Should log that 1 was queued, 1 skipped
        calls = [str(c) for c in mock_log.call_args_list]
        assert any("1" in c and "queued" in c.lower() for c in calls) or any(
            "1" in c and "cache" in c.lower() for c in calls
        )

    def test_worker_handles_empty_playlist(self, configured_state, mocker):
        """Worker should handle empty playlist gracefully."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_tools_ready(True)
        state.set_stop_threads(False)

        mocker.patch("ytplay_modules.playlist.scan_existing_cache")
        mocker.patch("ytplay_modules.state.initialize_played_videos")

        mock_fetch = mocker.patch("ytplay_modules.playlist.fetch_playlist_with_ytdlp")
        mock_fetch.return_value = []

        mock_log = mocker.patch("ytplay_modules.playlist.log")

        state.sync_event.set()

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        time.sleep(0.5)

        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

        # Should log no videos found
        calls = [str(c) for c in mock_log.call_args_list]
        assert any("no videos" in c.lower() for c in calls)

    def test_worker_handles_sync_exception(self, configured_state, mocker):
        """Worker should handle exceptions gracefully."""
        from ytplay_modules import state
        from ytplay_modules.playlist import playlist_sync_worker

        state.set_tools_ready(True)
        state.set_stop_threads(False)

        mocker.patch("ytplay_modules.playlist.scan_existing_cache", side_effect=Exception("Test error"))
        mock_log = mocker.patch("ytplay_modules.playlist.log")

        state.sync_event.set()

        thread = threading.Thread(target=playlist_sync_worker, daemon=True)
        thread.start()

        time.sleep(0.5)

        state.set_stop_threads(True)
        state.sync_event.set()
        thread.join(timeout=2)

        # Should log error
        calls = [str(c) for c in mock_log.call_args_list]
        assert any("error" in c.lower() for c in calls)


class TestFetchPlaylistWithYtdlp:
    """Tests for fetch_playlist_with_ytdlp function."""

    def test_fetch_returns_video_list(self, mocker):
        """Should return list of videos from yt-dlp output."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"id": "vid1", "title": "Title 1", "duration": 180}\n'
            '{"id": "vid2", "title": "Title 2", "duration": 200}\n',
            stderr="",
        )

        mocker.patch("ytplay_modules.playlist.get_ytdlp_path", return_value="/tools/yt-dlp")

        result = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert len(result) == 2
        assert result[0]["id"] == "vid1"
        assert result[1]["id"] == "vid2"

    def test_fetch_handles_empty_playlist(self, mocker):
        """Should return empty list for empty playlist."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        mocker.patch("ytplay_modules.playlist.get_ytdlp_path", return_value="/tools/yt-dlp")

        result = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=EMPTY")

        assert result == []

    def test_fetch_handles_ytdlp_failure(self, mocker):
        """Should return empty list on yt-dlp failure."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error: playlist not found")

        mocker.patch("ytplay_modules.playlist.get_ytdlp_path", return_value="/tools/yt-dlp")

        result = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=INVALID")

        assert result == []

    def test_fetch_handles_invalid_json(self, mocker):
        """Should skip invalid JSON lines."""
        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"id": "vid1", "title": "Title 1", "duration": 180}\n'
            "not valid json\n"
            '{"id": "vid2", "title": "Title 2", "duration": 200}\n',
            stderr="",
        )

        mocker.patch("ytplay_modules.playlist.get_ytdlp_path", return_value="/tools/yt-dlp")

        result = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=TEST")

        assert len(result) == 2

    def test_fetch_handles_timeout(self, mocker):
        """Should return empty list on timeout."""
        import subprocess

        from ytplay_modules.playlist import fetch_playlist_with_ytdlp

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 30)

        mocker.patch("ytplay_modules.playlist.get_ytdlp_path", return_value="/tools/yt-dlp")

        result = fetch_playlist_with_ytdlp("https://youtube.com/playlist?list=SLOW")

        assert result == []


class TestTriggerFunctions:
    """Tests for trigger_startup_sync and trigger_manual_sync."""

    def test_trigger_startup_sync_sets_flag(self, configured_state):
        """Startup sync should set done flag."""
        from ytplay_modules import state
        from ytplay_modules.playlist import trigger_startup_sync

        assert not state.is_sync_on_startup_done()

        trigger_startup_sync()

        assert state.is_sync_on_startup_done()
        assert state.sync_event.is_set()

    def test_trigger_startup_sync_only_once(self, configured_state):
        """Startup sync should only trigger once."""
        from ytplay_modules import state
        from ytplay_modules.playlist import trigger_startup_sync

        # First call
        trigger_startup_sync()
        state.sync_event.clear()

        # Second call should not set event
        trigger_startup_sync()

        assert not state.sync_event.is_set()

    def test_trigger_manual_sync_sets_event(self, configured_state):
        """Manual sync should set event."""
        from ytplay_modules import state
        from ytplay_modules.playlist import trigger_manual_sync

        state.sync_event.clear()

        trigger_manual_sync()

        assert state.sync_event.is_set()


class TestStartPlaylistSyncThread:
    """Tests for start_playlist_sync_thread function."""

    def test_starts_daemon_thread(self, configured_state, mocker):
        """Should start a daemon thread."""
        from ytplay_modules import state
        from ytplay_modules.playlist import start_playlist_sync_thread

        # Ensure thread exits quickly
        state.set_stop_threads(True)

        start_playlist_sync_thread()

        assert state.playlist_sync_thread is not None
        assert state.playlist_sync_thread.daemon is True

        # Wait for thread to exit
        state.sync_event.set()
        state.playlist_sync_thread.join(timeout=2)
