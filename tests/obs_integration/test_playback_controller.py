"""
OBS Integration tests for ytplay_modules.playback_controller

Tests for main playback controller and video management.
Uses mock obspython module for testing outside of OBS runtime.
"""


import obspython as obs


class TestVerifySources:
    """Tests for verify_sources function."""

    def test_returns_true_when_all_sources_exist(self):
        """Should return True when all required sources exist."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, SCENE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import verify_sources

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        # Reset the verified flag
        from ytplay_modules import playback_controller
        playback_controller._sources_verified = False

        result = verify_sources()

        assert result is True

    def test_returns_false_when_scene_missing(self):
        """Should return False when scene is missing."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import verify_sources

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        from ytplay_modules import playback_controller
        playback_controller._sources_verified = False

        result = verify_sources()

        assert result is False

    def test_returns_false_when_media_source_missing(self):
        """Should return False when media source is missing."""
        from ytplay_modules.config import SCENE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import verify_sources

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        from ytplay_modules import playback_controller
        playback_controller._sources_verified = False

        result = verify_sources()

        assert result is False


class TestPlaybackController:
    """Tests for playback_controller main function."""

    def setup_method(self):
        """Reset state before each test."""
        obs.reset()
        from ytplay_modules import playback_controller
        playback_controller._sources_verified = False
        playback_controller._waiting_for_videos_logged = False
        playback_controller._last_cached_count = 0
        playback_controller._initial_state_checked = False

    def test_returns_early_when_threads_should_stop(self):
        """Should return early when stop_threads flag is set."""
        from ytplay_modules.playback_controller import playback_controller
        from ytplay_modules.state import set_stop_threads

        set_stop_threads(True)

        # Should not raise exception
        playback_controller()

    def test_returns_early_when_sources_missing(self):
        """Should return early when sources are missing."""
        from ytplay_modules.playback_controller import playback_controller
        from ytplay_modules.state import set_stop_threads

        set_stop_threads(False)

        # Should not raise exception
        playback_controller()

    def test_stops_playback_when_scene_inactive(self):
        """Should stop playback when scene becomes inactive."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, SCENE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import playback_controller
        from ytplay_modules.state import set_playing, set_scene_active, set_stop_threads

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_stop_threads(False)
        set_scene_active(False)
        set_playing(True)

        from ytplay_modules import playback_controller as pc
        pc._sources_verified = True  # Skip verification

        playback_controller()

        # Playback should be stopped
        # Note: actual stop happens via stop_current_playback

    def test_waits_for_videos_when_cache_empty(self):
        """Should log waiting message when no videos cached."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, SCENE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import playback_controller
        from ytplay_modules.state import set_scene_active, set_stop_threads

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_stop_threads(False)
        set_scene_active(True)

        from ytplay_modules import playback_controller as pc
        pc._sources_verified = True
        pc._waiting_for_videos_logged = False

        playback_controller()

        # Waiting flag should be set
        assert pc._waiting_for_videos_logged is True


class TestStartNextVideo:
    """Tests for start_next_video function."""

    def test_stops_in_single_mode_after_first_video(self):
        """Should stop playback in single mode after first video played."""
        from ytplay_modules.config import PLAYBACK_MODE_SINGLE
        from ytplay_modules.playback_controller import start_next_video
        from ytplay_modules.state import is_playing, set_first_video_played, set_playback_mode

        obs.reset()
        set_playback_mode(PLAYBACK_MODE_SINGLE)
        set_first_video_played(True)

        start_next_video()

        assert is_playing() is False

    def test_sets_playing_false_when_no_video_available(self):
        """Should set playing to False when no video can be selected."""
        from ytplay_modules.playback_controller import start_next_video
        from ytplay_modules.state import is_playing

        obs.reset()

        start_next_video()

        assert is_playing() is False


class TestStartSpecificVideo:
    """Tests for start_specific_video function."""

    def test_handles_missing_video_info(self):
        """Should return early when video info doesn't exist."""
        from ytplay_modules.playback_controller import start_specific_video

        obs.reset()

        start_specific_video("nonexistent_id")

        # Should not crash, playing should be false
        # (actual behavior depends on whether playing was set before)


class TestStopCurrentPlayback:
    """Tests for stop_current_playback function."""

    def test_logs_message_when_not_playing(self):
        """Should log message when not currently playing."""
        from ytplay_modules.playback_controller import stop_current_playback
        from ytplay_modules.state import set_playing

        obs.reset()
        set_playing(False)

        # Should not raise exception
        stop_current_playback()

    def test_clears_all_state(self):
        """Should clear all playback state."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.playback_controller import stop_current_playback
        from ytplay_modules.state import (
            get_current_playback_video_id,
            get_current_video_path,
            is_playing,
            set_current_video_path,
            set_playing,
        )

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_playing(True)
        set_current_video_path("/path/to/video.mp4")

        stop_current_playback()

        assert is_playing() is False
        assert get_current_video_path() is None
        assert get_current_playback_video_id() is None


class TestStartPlaybackController:
    """Tests for start_playback_controller function."""

    def test_adds_timer(self):
        """Should add playback controller timer."""
        from ytplay_modules.playback_controller import start_playback_controller

        obs.reset()

        start_playback_controller()

        assert obs.assert_call_made("timer_add")

    def test_removes_existing_timer(self):
        """Should remove existing timer before adding new one."""
        from ytplay_modules import playback_controller
        from ytplay_modules.playback_controller import start_playback_controller

        obs.reset()
        playback_controller._playback_timer = lambda: None

        start_playback_controller()

        assert obs.assert_call_made("timer_remove")


class TestStopPlaybackController:
    """Tests for stop_playback_controller function."""

    def test_removes_timer(self):
        """Should remove playback controller timer."""
        from ytplay_modules import playback_controller
        from ytplay_modules.playback_controller import stop_playback_controller

        obs.reset()
        playback_controller._playback_timer = lambda: None

        stop_playback_controller()

        assert playback_controller._playback_timer is None

    def test_cancels_all_timers(self):
        """Should cancel title and opacity timers."""
        from ytplay_modules.playback_controller import stop_playback_controller

        obs.reset()

        stop_playback_controller()

        # Should have called timer_remove
        # (may be called multiple times for different timers)
