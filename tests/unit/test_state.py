"""
Unit tests for ytplay_modules.state

Tests for thread-safe state management functions.
Target: 100% coverage
"""

import pytest
import threading
import queue
from unittest.mock import patch, MagicMock


class TestPlaylistUrlState:
    """Tests for playlist URL state accessors."""

    def test_get_default_playlist_url(self):
        """Should return default playlist URL initially."""
        from ytplay_modules.state import get_playlist_url
        from ytplay_modules.config import DEFAULT_PLAYLIST_URL

        result = get_playlist_url()
        assert result == DEFAULT_PLAYLIST_URL

    def test_set_and_get_playlist_url(self):
        """Should store and retrieve playlist URL."""
        from ytplay_modules.state import set_playlist_url, get_playlist_url

        test_url = "https://www.youtube.com/playlist?list=TEST123"
        set_playlist_url(test_url)

        assert get_playlist_url() == test_url

    def test_set_empty_playlist_url(self):
        """Should handle empty URL."""
        from ytplay_modules.state import set_playlist_url, get_playlist_url

        set_playlist_url("")
        assert get_playlist_url() == ""


class TestCacheDirState:
    """Tests for cache directory state accessors."""

    def test_get_default_cache_dir(self):
        """Should return cache directory (set by fixture for test isolation)."""
        from ytplay_modules.state import get_cache_dir

        result = get_cache_dir()
        # Note: conftest sets a temp cache dir for test isolation
        # Just verify it's a valid string path
        assert isinstance(result, str)
        assert len(result) > 0

    def test_set_and_get_cache_dir(self):
        """Should store and retrieve cache directory."""
        from ytplay_modules.state import set_cache_dir, get_cache_dir

        test_dir = "/test/cache/dir"
        set_cache_dir(test_dir)

        assert get_cache_dir() == test_dir


class TestGeminiApiKeyState:
    """Tests for Gemini API key state accessors."""

    def test_get_default_gemini_api_key(self):
        """Should return None initially."""
        from ytplay_modules.state import get_gemini_api_key

        # After reset, should be None or empty
        result = get_gemini_api_key()
        assert result is None or result == ""

    def test_set_and_get_gemini_api_key(self):
        """Should store and retrieve Gemini API key."""
        from ytplay_modules.state import set_gemini_api_key, get_gemini_api_key

        test_key = "test_api_key_12345"
        set_gemini_api_key(test_key)

        assert get_gemini_api_key() == test_key

    def test_set_none_gemini_api_key(self):
        """Should handle None API key."""
        from ytplay_modules.state import set_gemini_api_key, get_gemini_api_key

        set_gemini_api_key(None)
        assert get_gemini_api_key() is None


class TestPlaybackModeState:
    """Tests for playback mode state accessors."""

    def test_get_default_playback_mode(self):
        """Should return default playback mode initially."""
        from ytplay_modules.state import get_playback_mode
        from ytplay_modules.config import DEFAULT_PLAYBACK_MODE

        result = get_playback_mode()
        assert result == DEFAULT_PLAYBACK_MODE

    def test_set_and_get_playback_mode(self):
        """Should store and retrieve playback mode."""
        from ytplay_modules.state import set_playback_mode, get_playback_mode
        from ytplay_modules.config import PLAYBACK_MODE_LOOP

        set_playback_mode(PLAYBACK_MODE_LOOP)

        assert get_playback_mode() == PLAYBACK_MODE_LOOP


class TestAudioOnlyModeState:
    """Tests for audio-only mode state accessors."""

    def test_get_default_audio_only_mode(self):
        """Should return False initially."""
        from ytplay_modules.state import is_audio_only_mode
        from ytplay_modules.config import DEFAULT_AUDIO_ONLY_MODE

        result = is_audio_only_mode()
        assert result == DEFAULT_AUDIO_ONLY_MODE

    def test_set_and_get_audio_only_mode(self):
        """Should store and retrieve audio-only mode."""
        from ytplay_modules.state import set_audio_only_mode, is_audio_only_mode

        set_audio_only_mode(True)
        assert is_audio_only_mode() is True

        set_audio_only_mode(False)
        assert is_audio_only_mode() is False


class TestToolsReadyState:
    """Tests for tools ready state flag."""

    def test_tools_ready_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_tools_ready

        result = is_tools_ready()
        assert result is False

    def test_set_tools_ready(self):
        """Should set tools ready flag."""
        from ytplay_modules.state import set_tools_ready, is_tools_ready

        set_tools_ready(True)
        assert is_tools_ready() is True

        set_tools_ready(False)
        assert is_tools_ready() is False


class TestToolsLoggedWaitingState:
    """Tests for tools logged waiting state flag."""

    def test_tools_logged_waiting_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_tools_logged_waiting

        result = is_tools_logged_waiting()
        assert result is False

    def test_set_tools_logged_waiting(self):
        """Should set tools logged waiting flag."""
        from ytplay_modules.state import set_tools_logged_waiting, is_tools_logged_waiting

        set_tools_logged_waiting(True)
        assert is_tools_logged_waiting() is True


class TestSceneActiveState:
    """Tests for scene active state flag."""

    def test_scene_active_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_scene_active

        result = is_scene_active()
        assert result is False

    def test_set_scene_active(self):
        """Should set scene active flag."""
        from ytplay_modules.state import set_scene_active, is_scene_active

        set_scene_active(True)
        assert is_scene_active() is True


class TestIsPlayingState:
    """Tests for is playing state flag."""

    def test_is_playing_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_playing

        result = is_playing()
        assert result is False

    def test_set_playing(self):
        """Should set playing flag."""
        from ytplay_modules.state import set_playing, is_playing

        set_playing(True)
        assert is_playing() is True


class TestStopThreadsState:
    """Tests for stop threads state flag."""

    def test_should_stop_threads_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import should_stop_threads

        result = should_stop_threads()
        assert result is False

    def test_set_stop_threads(self):
        """Should set stop threads flag."""
        from ytplay_modules.state import set_stop_threads, should_stop_threads

        set_stop_threads(True)
        assert should_stop_threads() is True


class TestSyncOnStartupDoneState:
    """Tests for sync on startup done state flag."""

    def test_sync_on_startup_done_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_sync_on_startup_done

        result = is_sync_on_startup_done()
        assert result is False

    def test_set_sync_on_startup_done(self):
        """Should set sync on startup done flag."""
        from ytplay_modules.state import set_sync_on_startup_done, is_sync_on_startup_done

        set_sync_on_startup_done(True)
        assert is_sync_on_startup_done() is True


class TestStopRequestedState:
    """Tests for stop requested state flag."""

    def test_stop_requested_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_stop_requested

        result = is_stop_requested()
        assert result is False

    def test_set_stop_requested(self):
        """Should set stop requested flag."""
        from ytplay_modules.state import set_stop_requested, is_stop_requested

        set_stop_requested(True)
        assert is_stop_requested() is True

    def test_clear_stop_request(self):
        """Should clear stop request flag."""
        from ytplay_modules.state import set_stop_requested, clear_stop_request, is_stop_requested

        set_stop_requested(True)
        assert is_stop_requested() is True

        clear_stop_request()
        assert is_stop_requested() is False


class TestFirstVideoPlayedState:
    """Tests for first video played state flag."""

    def test_first_video_played_default_false(self):
        """Should be False initially."""
        from ytplay_modules.state import is_first_video_played

        result = is_first_video_played()
        assert result is False

    def test_set_first_video_played(self):
        """Should set first video played flag."""
        from ytplay_modules.state import set_first_video_played, is_first_video_played

        set_first_video_played(True)
        assert is_first_video_played() is True


class TestCurrentVideoPathState:
    """Tests for current video path state."""

    def test_current_video_path_default_none(self):
        """Should be None initially."""
        from ytplay_modules.state import get_current_video_path

        result = get_current_video_path()
        assert result is None

    def test_set_and_get_current_video_path(self):
        """Should store and retrieve current video path."""
        from ytplay_modules.state import set_current_video_path, get_current_video_path

        test_path = "/cache/test_video.mp4"
        set_current_video_path(test_path)

        assert get_current_video_path() == test_path


class TestCurrentPlaybackVideoIdState:
    """Tests for current playback video ID state."""

    def test_current_playback_video_id_default_none(self):
        """Should be None initially."""
        from ytplay_modules.state import get_current_playback_video_id

        result = get_current_playback_video_id()
        assert result is None

    def test_set_and_get_current_playback_video_id(self):
        """Should store and retrieve current playback video ID."""
        from ytplay_modules.state import set_current_playback_video_id, get_current_playback_video_id

        test_id = "dQw4w9WgXcQ"
        set_current_playback_video_id(test_id)

        assert get_current_playback_video_id() == test_id


class TestLoopVideoIdState:
    """Tests for loop video ID state."""

    def test_loop_video_id_default_none(self):
        """Should be None initially."""
        from ytplay_modules.state import get_loop_video_id

        result = get_loop_video_id()
        assert result is None

    def test_set_and_get_loop_video_id(self):
        """Should store and retrieve loop video ID."""
        from ytplay_modules.state import set_loop_video_id, get_loop_video_id

        test_id = "dQw4w9WgXcQ"
        set_loop_video_id(test_id)

        assert get_loop_video_id() == test_id


class TestCachedVideosState:
    """Tests for cached videos data structure."""

    def test_get_cached_videos_empty_initially(self):
        """Should return empty dict initially."""
        from ytplay_modules.state import get_cached_videos

        result = get_cached_videos()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_add_cached_video(self):
        """Should add video to cache."""
        from ytplay_modules.state import add_cached_video, get_cached_videos

        video_id = "test123"
        video_info = {
            "path": "/cache/test.mp4",
            "song": "Test Song",
            "artist": "Test Artist",
            "normalized": True
        }

        add_cached_video(video_id, video_info)

        cached = get_cached_videos()
        assert video_id in cached
        assert cached[video_id]["song"] == "Test Song"

    def test_remove_cached_video(self):
        """Should remove video from cache."""
        from ytplay_modules.state import add_cached_video, remove_cached_video, get_cached_videos

        video_id = "test456"
        add_cached_video(video_id, {"path": "/test.mp4", "song": "Test", "artist": "Test"})

        remove_cached_video(video_id)

        cached = get_cached_videos()
        assert video_id not in cached

    def test_remove_nonexistent_video(self):
        """Should handle removing nonexistent video gracefully."""
        from ytplay_modules.state import remove_cached_video

        # Should not raise
        remove_cached_video("nonexistent_id")

    def test_is_video_cached(self):
        """Should check if video is in cache."""
        from ytplay_modules.state import add_cached_video, is_video_cached

        video_id = "cached_id"
        add_cached_video(video_id, {"path": "/test.mp4", "song": "Test", "artist": "Test"})

        assert is_video_cached(video_id) is True
        assert is_video_cached("not_cached") is False

    def test_get_cached_video_info(self):
        """Should get info for cached video."""
        from ytplay_modules.state import add_cached_video, get_cached_video_info

        video_id = "info_test"
        video_info = {"path": "/test.mp4", "song": "My Song", "artist": "My Artist"}
        add_cached_video(video_id, video_info)

        result = get_cached_video_info(video_id)
        assert result["song"] == "My Song"
        assert result["artist"] == "My Artist"

    def test_get_cached_video_info_nonexistent(self):
        """Should return None for nonexistent video."""
        from ytplay_modules.state import get_cached_video_info

        result = get_cached_video_info("nonexistent")
        assert result is None

    def test_get_cached_videos_returns_copy(self):
        """Should return a copy, not the original dict."""
        from ytplay_modules.state import add_cached_video, get_cached_videos

        add_cached_video("copy_test", {"path": "/test.mp4", "song": "Test", "artist": "Test"})

        cached1 = get_cached_videos()
        cached1["modified"] = "value"

        cached2 = get_cached_videos()
        assert "modified" not in cached2


class TestPlaylistVideoIdsState:
    """Tests for playlist video IDs state."""

    def test_get_playlist_video_ids_empty_initially(self):
        """Should return empty set initially."""
        from ytplay_modules.state import get_playlist_video_ids

        result = get_playlist_video_ids()
        assert isinstance(result, set)

    def test_set_playlist_video_ids(self):
        """Should set playlist video IDs."""
        from ytplay_modules.state import set_playlist_video_ids, get_playlist_video_ids

        test_ids = {"id1", "id2", "id3"}
        set_playlist_video_ids(test_ids)

        result = get_playlist_video_ids()
        assert result == test_ids

    def test_get_playlist_video_ids_returns_copy(self):
        """Should return a copy, not the original set."""
        from ytplay_modules.state import set_playlist_video_ids, get_playlist_video_ids

        set_playlist_video_ids({"id1", "id2"})

        result1 = get_playlist_video_ids()
        result1.add("modified")

        result2 = get_playlist_video_ids()
        assert "modified" not in result2


class TestPlayedVideosState:
    """Tests for played videos state."""

    def test_get_played_videos_empty_initially(self):
        """Should return empty list initially."""
        from ytplay_modules.state import get_played_videos

        result = get_played_videos()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_add_played_video(self):
        """Should add video to played list."""
        from ytplay_modules.state import add_played_video, get_played_videos

        add_played_video("played1")
        add_played_video("played2")

        result = get_played_videos()
        assert "played1" in result
        assert "played2" in result

    def test_add_played_video_no_duplicates(self):
        """Should not add duplicate videos."""
        from ytplay_modules.state import add_played_video, get_played_videos, clear_played_videos

        clear_played_videos()
        add_played_video("same_id")
        add_played_video("same_id")

        result = get_played_videos()
        assert result.count("same_id") == 1

    def test_clear_played_videos(self):
        """Should clear played videos list."""
        from ytplay_modules.state import add_played_video, clear_played_videos, get_played_videos

        add_played_video("to_clear")
        clear_played_videos()

        result = get_played_videos()
        assert len(result) == 0

    def test_get_played_videos_returns_copy(self):
        """Should return a copy, not the original list."""
        from ytplay_modules.state import add_played_video, get_played_videos, clear_played_videos

        clear_played_videos()
        add_played_video("copy_test")

        result1 = get_played_videos()
        result1.append("modified")

        result2 = get_played_videos()
        assert "modified" not in result2


class TestIsVideoBeingProcessed:
    """Tests for is_video_being_processed function."""

    def test_video_being_processed_when_current(self):
        """Should return True when video is current playback."""
        from ytplay_modules.state import (
            set_current_playback_video_id,
            is_video_being_processed
        )

        video_id = "processing_test"
        set_current_playback_video_id(video_id)

        assert is_video_being_processed(video_id) is True

    def test_video_not_being_processed(self):
        """Should return False when video is not current."""
        from ytplay_modules.state import (
            set_current_playback_video_id,
            is_video_being_processed
        )

        set_current_playback_video_id("other_id")

        assert is_video_being_processed("different_id") is False


class TestThreadSafety:
    """Tests for thread safety of state operations."""

    def test_concurrent_cache_access(self):
        """Multiple threads should safely access cached videos."""
        from ytplay_modules.state import add_cached_video, get_cached_videos, remove_cached_video

        errors = []

        def writer(thread_id):
            try:
                for i in range(10):
                    video_id = f"thread{thread_id}_video{i}"
                    add_cached_video(video_id, {
                        "path": f"/cache/{video_id}.mp4",
                        "song": f"Song {i}",
                        "artist": f"Artist {thread_id}"
                    })
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(20):
                    _ = get_cached_videos()
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=writer, args=(i,)))
        for _ in range(2):
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_concurrent_flag_access(self):
        """Multiple threads should safely access boolean flags."""
        from ytplay_modules.state import set_playing, is_playing

        errors = []

        def toggle(iterations):
            try:
                for _ in range(iterations):
                    set_playing(True)
                    _ = is_playing()
                    set_playing(False)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=toggle, args=(50,)) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestVideoQueueExists:
    """Tests for video queue initialization."""

    def test_video_queue_is_queue(self):
        """Video queue should be a Queue instance."""
        from ytplay_modules.state import video_queue

        assert video_queue is not None
        assert isinstance(video_queue, queue.Queue)

    def test_sync_event_is_event(self):
        """Sync event should be a threading Event."""
        from ytplay_modules.state import sync_event

        assert sync_event is not None
        assert isinstance(sync_event, threading.Event)
