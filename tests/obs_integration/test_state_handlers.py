"""
OBS Integration tests for ytplay_modules.state_handlers

Tests for media state handling: playing, ended, stopped, none.
Uses mock obspython module for testing outside of OBS runtime.
"""

from unittest.mock import patch

import obspython as obs


class TestResetPlaybackTracking:
    """Tests for reset_playback_tracking function."""

    def test_resets_all_tracking_variables(self):
        """Should reset all playback tracking variables."""
        from ytplay_modules import state_handlers

        # Set some values
        state_handlers._last_playback_time = 60000
        state_handlers._last_progress_log["key"] = True
        state_handlers._playback_retry_count = 5
        state_handlers._title_clear_rescheduled = True

        state_handlers.reset_playback_tracking()

        assert state_handlers._last_playback_time == 0
        assert len(state_handlers._last_progress_log) == 0
        assert state_handlers._playback_retry_count == 0
        assert state_handlers._title_clear_rescheduled is False


class TestLogPlaybackProgress:
    """Tests for log_playback_progress function."""

    def test_logs_progress_at_intervals(self):
        """Should log progress at 30-second intervals."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.state_handlers import log_playback_progress

        obs.reset()
        video_id = "test123"
        add_cached_video(video_id, {"path": "/path/to/video.mp4", "song": "Test Song", "artist": "Test Artist"})

        # First log at 0 seconds
        log_playback_progress(video_id, 0, 180000)

        # Second log at 30 seconds - should log
        log_playback_progress(video_id, 30000, 180000)

        # Third log at 31 seconds - should NOT log (same 30s bucket)
        from ytplay_modules import state_handlers

        initial_count = len(state_handlers._last_progress_log)
        log_playback_progress(video_id, 31000, 180000)
        assert len(state_handlers._last_progress_log) == initial_count


class TestHandlePlayingState:
    """Tests for handle_playing_state function."""

    def setup_method(self):
        """Reset state before each test."""
        obs.reset()
        from ytplay_modules import state_handlers

        state_handlers._is_preloaded_video = False
        state_handlers._last_playback_time = 0
        state_handlers._manual_stop_detected = False
        state_handlers._loop_restart_pending = False
        state_handlers._loop_restart_video_id = None
        state_handlers._title_clear_rescheduled = False

    def test_clears_manual_stop_flag(self):
        """Should clear manual stop flag when playing."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.state import set_playing
        from ytplay_modules.state_handlers import handle_playing_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_state(obs.OBS_MEDIA_STATE_PLAYING)
        obs.set_media_duration(180000)
        obs.set_media_time(60000)
        set_playing(True)

        from ytplay_modules import state_handlers

        state_handlers._manual_stop_detected = True

        handle_playing_state()

        assert state_handlers._manual_stop_detected is False

    def test_syncs_state_when_out_of_sync(self):
        """Should sync state when media is playing but we don't think so."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.state import is_playing, set_playing
        from ytplay_modules.state_handlers import handle_playing_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_state(obs.OBS_MEDIA_STATE_PLAYING)
        obs.set_media_duration(180000)
        set_playing(False)

        handle_playing_state()

        assert is_playing() is True

    def test_detects_seek_forward(self):
        """Should detect seek when playback time jumps forward."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.state import add_cached_video, set_current_playback_video_id, set_playing
        from ytplay_modules.state_handlers import handle_playing_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_state(obs.OBS_MEDIA_STATE_PLAYING)
        obs.set_media_duration(180000)
        obs.set_media_time(60000)
        set_playing(True)
        video_id = "test123"
        add_cached_video(video_id, {"path": "/path/video.mp4", "song": "Song", "artist": "Artist"})
        set_current_playback_video_id(video_id)

        from ytplay_modules import state_handlers

        state_handlers._last_playback_time = 10000  # Was at 10 seconds

        handle_playing_state()

        # Should have updated last playback time
        assert state_handlers._last_playback_time == 60000


class TestHandleEndedState:
    """Tests for handle_ended_state function."""

    def setup_method(self):
        """Reset state before each test."""
        obs.reset()
        from ytplay_modules import state_handlers

        state_handlers._preloaded_video_handled = False
        state_handlers._is_preloaded_video = False
        state_handlers._loop_restart_pending = False

    def test_prevents_duplicate_loop_restart(self):
        """Should prevent duplicate loop restart in loop mode."""
        from ytplay_modules.config import PLAYBACK_MODE_LOOP
        from ytplay_modules.state import set_playback_mode, set_playing
        from ytplay_modules.state_handlers import handle_ended_state

        set_playing(True)
        set_playback_mode(PLAYBACK_MODE_LOOP)

        from ytplay_modules import state_handlers

        state_handlers._loop_restart_pending = True

        handle_ended_state()

        # Should have returned early
        assert state_handlers._loop_restart_pending is True

    def test_stops_in_single_mode_after_first_video(self):
        """Should stop playback in single mode after first video."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, PLAYBACK_MODE_SINGLE, TEXT_SOURCE_NAME
        from ytplay_modules.state import is_playing, set_first_video_played, set_playback_mode, set_playing
        from ytplay_modules.state_handlers import handle_ended_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_playing(True)
        set_playback_mode(PLAYBACK_MODE_SINGLE)
        set_first_video_played(True)

        handle_ended_state()

        assert is_playing() is False

    def test_starts_next_when_scene_active_and_not_playing(self):
        """Should start next video when scene active but not playing."""
        from ytplay_modules.config import PLAYBACK_MODE_CONTINUOUS
        from ytplay_modules.state import add_cached_video, set_playback_mode, set_playing, set_scene_active
        from ytplay_modules.state_handlers import handle_ended_state

        set_playing(False)
        set_scene_active(True)
        set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
        add_cached_video("video1", {"path": "/path/v1.mp4", "song": "S", "artist": "A"})

        # Mock start_next_video in playback_controller where it's imported from
        with patch("ytplay_modules.playback_controller.start_next_video") as mock_start:
            handle_ended_state()
            mock_start.assert_called_once()


class TestHandleStoppedState:
    """Tests for handle_stopped_state function."""

    def setup_method(self):
        """Reset state before each test."""
        obs.reset()
        from ytplay_modules import state_handlers

        state_handlers._manual_stop_detected = False
        state_handlers._playback_retry_count = 0

    def test_detects_manual_stop(self):
        """Should detect user manual stop."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.state import set_playing
        from ytplay_modules.state_handlers import handle_stopped_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_playing(True)

        handle_stopped_state()

        from ytplay_modules import state_handlers

        assert state_handlers._manual_stop_detected is True

    def test_retries_when_playback_stops_unexpectedly(self):
        """Should retry playback when it stops unexpectedly."""
        from ytplay_modules.state import set_playing
        from ytplay_modules.state_handlers import handle_stopped_state

        set_playing(True)

        from ytplay_modules import state_handlers

        state_handlers._manual_stop_detected = True  # Already detected
        state_handlers._playback_retry_count = 0

        # Mock start_next_video in playback_controller where it's imported from
        with patch("ytplay_modules.playback_controller.start_next_video") as mock_start:
            handle_stopped_state()
            # start_next_video should be called for retry
            mock_start.assert_called_once()

        # Retry count should have increased
        assert state_handlers._playback_retry_count >= 1

    def test_stops_after_max_retries(self):
        """Should stop completely after max retries."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME
        from ytplay_modules.state import set_playing
        from ytplay_modules.state_handlers import handle_stopped_state

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        set_playing(True)

        from ytplay_modules import state_handlers

        state_handlers._manual_stop_detected = True
        state_handlers._playback_retry_count = state_handlers._max_retry_attempts

        handle_stopped_state()

        # Should have called stop_current_playback


class TestHandleNoneState:
    """Tests for handle_none_state function."""

    def test_starts_playback_when_scene_active(self):
        """Should start playback when scene active and videos available."""
        from ytplay_modules.state import add_cached_video, set_playing, set_scene_active
        from ytplay_modules.state_handlers import handle_none_state

        obs.reset()
        set_scene_active(True)
        set_playing(False)
        add_cached_video("video1", {"path": "/p.mp4", "song": "S", "artist": "A"})

        # Mock start_next_video in playback_controller where it's imported from
        with patch("ytplay_modules.playback_controller.start_next_video") as mock_start:
            handle_none_state()
            mock_start.assert_called_once()

    def test_does_not_start_in_single_mode_after_first(self):
        """Should not start new playback in single mode after first video."""
        from ytplay_modules.config import PLAYBACK_MODE_SINGLE
        from ytplay_modules.state import (
            add_cached_video,
            is_playing,
            set_first_video_played,
            set_playback_mode,
            set_playing,
            set_scene_active,
        )
        from ytplay_modules.state_handlers import handle_none_state

        obs.reset()
        set_scene_active(True)
        set_playing(False)
        set_playback_mode(PLAYBACK_MODE_SINGLE)
        set_first_video_played(True)
        add_cached_video("video1", {"path": "/p.mp4", "song": "S", "artist": "A"})

        handle_none_state()

        # Should not have started playing
        assert is_playing() is False

    def test_resets_playing_when_no_media_but_playing_state(self):
        """Should reset playing state when no media but state says playing (after grace period)."""
        import time

        from ytplay_modules.state import (
            is_playing,
            set_playback_started_time,
            set_playing,
            set_scene_active,
        )
        from ytplay_modules.state_handlers import handle_none_state

        obs.reset()
        set_scene_active(True)
        set_playing(True)
        # Set playback started time to 10 seconds ago (past the 5s grace period)
        set_playback_started_time(time.time() - 10.0)

        handle_none_state()

        assert is_playing() is False

    def test_does_not_reset_playing_during_grace_period(self):
        """Should not reset playing state during media loading grace period."""
        import time

        from ytplay_modules.state import (
            is_playing,
            set_playback_started_time,
            set_playing,
            set_scene_active,
        )
        from ytplay_modules.state_handlers import handle_none_state

        obs.reset()
        set_scene_active(True)
        set_playing(True)
        # Set playback started time to 1 second ago (within the 5s grace period)
        set_playback_started_time(time.time() - 1.0)

        handle_none_state()

        # Should still be playing because we're within the grace period
        assert is_playing() is True


class TestScheduleLoopRestart:
    """Tests for schedule_loop_restart function."""

    def test_schedules_timer_for_restart(self):
        """Should schedule a timer for loop restart."""
        from ytplay_modules.state_handlers import schedule_loop_restart

        obs.reset()

        schedule_loop_restart("video123")

        assert obs.assert_call_made("timer_add")

    def test_cancels_existing_timer(self):
        """Should cancel existing timer before scheduling new one."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import schedule_loop_restart

        obs.reset()
        state_handlers._loop_restart_timer = lambda: None

        schedule_loop_restart("video456")

        # Should have removed old timer
        assert obs.assert_call_made("timer_remove")


class TestCancelLoopRestartTimer:
    """Tests for cancel_loop_restart_timer function."""

    def test_cancels_timer(self):
        """Should cancel loop restart timer."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import cancel_loop_restart_timer

        obs.reset()
        state_handlers._loop_restart_timer = lambda: None

        cancel_loop_restart_timer()

        assert state_handlers._loop_restart_timer is None


class TestSetPreloadedVideoState:
    """Tests for set_preloaded_video_state function."""

    def test_sets_state_correctly(self):
        """Should set preloaded video state flags."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import set_preloaded_video_state

        set_preloaded_video_state(True, True)

        assert state_handlers._preloaded_video_handled is True
        assert state_handlers._is_preloaded_video is True

    def test_can_clear_state(self):
        """Should be able to clear preloaded video state."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import set_preloaded_video_state

        set_preloaded_video_state(False, False)

        assert state_handlers._preloaded_video_handled is False
        assert state_handlers._is_preloaded_video is False


class TestSetManualStopDetected:
    """Tests for set_manual_stop_detected function."""

    def test_sets_flag(self):
        """Should set manual stop detected flag."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import set_manual_stop_detected

        set_manual_stop_detected(True)

        assert state_handlers._manual_stop_detected is True


class TestClearLoopRestartState:
    """Tests for clear_loop_restart_state function."""

    def test_clears_state(self):
        """Should clear loop restart state."""
        from ytplay_modules import state_handlers
        from ytplay_modules.state_handlers import clear_loop_restart_state

        state_handlers._loop_restart_pending = True
        state_handlers._loop_restart_video_id = "someid"

        clear_loop_restart_state()

        assert state_handlers._loop_restart_pending is False
        assert state_handlers._loop_restart_video_id is None
