"""
OBS Integration tests for ytplay_modules.title_manager

Tests for title display timing and scheduling.
Uses mock obspython module for testing outside of OBS runtime.
"""

from unittest.mock import patch

import obspython as obs


class TestTitleTimingConstants:
    """Tests for title timing constants."""

    def test_constants_are_defined(self):
        """Should have title timing constants defined."""
        from ytplay_modules.title_manager import SEEK_THRESHOLD, TITLE_CLEAR_BEFORE_END, TITLE_SHOW_AFTER_START

        assert TITLE_CLEAR_BEFORE_END == 3.5
        assert TITLE_SHOW_AFTER_START == 1.5
        assert SEEK_THRESHOLD == 5000


class TestCancelTitleTimers:
    """Tests for cancel_title_timers function."""

    def test_cancels_all_timers(self):
        """Should cancel all pending title timers."""
        from ytplay_modules import title_manager
        from ytplay_modules.title_manager import cancel_title_timers

        obs.reset()
        # Set up some timers
        title_manager._title_clear_timer = lambda: None
        title_manager._title_show_timer = lambda: None
        title_manager._duration_check_timer = lambda: None
        title_manager._pending_title_info = {"song": "Test"}
        title_manager._title_clear_scheduled = True

        cancel_title_timers()

        assert title_manager._title_clear_timer is None
        assert title_manager._title_show_timer is None
        assert title_manager._duration_check_timer is None
        assert title_manager._pending_title_info is None
        assert title_manager._title_clear_scheduled is False


class TestScheduleTitleClear:
    """Tests for schedule_title_clear function."""

    def test_schedules_timer_for_clear(self):
        """Should schedule timer for title clear."""
        from ytplay_modules.title_manager import schedule_title_clear

        obs.reset()

        # 60 seconds duration
        schedule_title_clear(60000)

        assert obs.assert_call_made("timer_add")

    def test_does_not_schedule_for_short_duration(self):
        """Should not schedule if clear time would be negative."""
        from ytplay_modules import title_manager
        from ytplay_modules.title_manager import schedule_title_clear

        obs.reset()
        title_manager._title_clear_scheduled = False

        # Very short duration (less than TITLE_CLEAR_BEFORE_END * 1000)
        schedule_title_clear(1000)

        # Should not schedule (clear_time_ms would be negative)
        assert title_manager._title_clear_scheduled is False


class TestScheduleTitleShow:
    """Tests for schedule_title_show function."""

    def test_schedules_timer_for_show(self):
        """Should schedule timer for title show."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import schedule_title_show

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        video_info = {"song": "Test Song", "artist": "Test Artist", "gemini_failed": False}

        schedule_title_show(video_info)

        assert obs.assert_call_made("timer_add")

    def test_stores_pending_title_info(self):
        """Should store pending title info."""
        from ytplay_modules import title_manager
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import schedule_title_show

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        video_info = {"song": "Test Song", "artist": "Test Artist"}

        schedule_title_show(video_info)

        assert title_manager._pending_title_info == video_info


class TestScheduleTitleClearFromCurrent:
    """Tests for schedule_title_clear_from_current function."""

    def test_schedules_based_on_remaining_time(self):
        """Should schedule based on remaining time."""
        from ytplay_modules.title_manager import schedule_title_clear_from_current

        obs.reset()

        # 10 seconds remaining
        schedule_title_clear_from_current(10000)

        assert obs.assert_call_made("timer_add")

    def test_fades_immediately_when_time_passed(self):
        """Should fade immediately when clear time has passed."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import schedule_title_clear_from_current

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        # Only 1 second remaining (less than TITLE_CLEAR_BEFORE_END)
        with patch("ytplay_modules.opacity_control.fade_out_text") as mock_fade:
            with patch("ytplay_modules.opacity_control.get_current_opacity", return_value=100):
                schedule_title_clear_from_current(1000)
                mock_fade.assert_called_once()


class TestScheduleTitleClearWithDelay:
    """Tests for schedule_title_clear_with_delay function."""

    def test_schedules_duration_check_timer(self):
        """Should schedule timer for duration check."""
        from ytplay_modules.title_manager import schedule_title_clear_with_delay

        obs.reset()

        schedule_title_clear_with_delay()

        assert obs.assert_call_made("timer_add")


class TestIsTitleClearScheduled:
    """Tests for is_title_clear_scheduled function."""

    def test_returns_scheduled_state(self):
        """Should return current scheduled state."""
        from ytplay_modules import title_manager
        from ytplay_modules.title_manager import is_title_clear_scheduled

        title_manager._title_clear_scheduled = True
        assert is_title_clear_scheduled() is True

        title_manager._title_clear_scheduled = False
        assert is_title_clear_scheduled() is False


class TestGetTitleClearTimer:
    """Tests for get_title_clear_timer function."""

    def test_returns_timer_reference(self):
        """Should return current timer reference."""
        from ytplay_modules import title_manager
        from ytplay_modules.title_manager import get_title_clear_timer

        timer_func = lambda: None
        title_manager._title_clear_timer = timer_func

        assert get_title_clear_timer() == timer_func


class TestGetPendingTitleInfo:
    """Tests for get_pending_title_info function."""

    def test_returns_pending_info(self):
        """Should return pending title info."""
        from ytplay_modules import title_manager
        from ytplay_modules.title_manager import get_pending_title_info

        info = {"song": "Test", "artist": "Artist"}
        title_manager._pending_title_info = info

        assert get_pending_title_info() == info


class TestUpdateTextSource:
    """Tests for update_text_source function."""

    def test_fades_out_first_if_visible(self):
        """Should fade out first if text is visible."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import update_text_source

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        with patch("ytplay_modules.opacity_control.get_current_opacity", return_value=100):
            with patch("ytplay_modules.opacity_control.fade_out_text") as mock_fade:
                with patch("ytplay_modules.opacity_control.set_pending_text") as mock_pending:
                    update_text_source("Song", "Artist")
                    mock_fade.assert_called_once()
                    mock_pending.assert_called_once()

    def test_updates_and_fades_in_if_not_visible(self):
        """Should update and fade in if text is not visible."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import update_text_source

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        with patch("ytplay_modules.opacity_control.get_current_opacity", return_value=0):
            with patch("ytplay_modules.media_control.update_text_source_content") as mock_update:
                with patch("ytplay_modules.opacity_control.fade_in_text") as mock_fade:
                    update_text_source("Song", "Artist")
                    mock_update.assert_called_once()
                    mock_fade.assert_called_once()


class TestClearTitleBeforeEndCallback:
    """Tests for clear_title_before_end_callback function."""

    def test_clears_timer_and_fades_out(self):
        """Should clear timer and fade out text."""
        from ytplay_modules import title_manager
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import clear_title_before_end_callback

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        title_manager._title_clear_timer = lambda: None

        with patch("ytplay_modules.opacity_control.fade_out_text") as mock_fade:
            clear_title_before_end_callback()
            mock_fade.assert_called_once()

        assert title_manager._title_clear_timer is None
        assert title_manager._title_clear_scheduled is False


class TestShowTitleAfterStartCallback:
    """Tests for show_title_after_start_callback function."""

    def test_shows_pending_title(self):
        """Should show pending title info."""
        from ytplay_modules import title_manager
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.title_manager import show_title_after_start_callback

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        title_manager._title_show_timer = lambda: None
        title_manager._pending_title_info = {"song": "Test Song", "artist": "Test Artist", "gemini_failed": False}

        with patch("ytplay_modules.media_control.update_text_source_content") as mock_update:
            with patch("ytplay_modules.opacity_control.fade_in_text") as mock_fade:
                show_title_after_start_callback()
                mock_update.assert_called_once_with("Test Song", "Test Artist", False)
                mock_fade.assert_called_once()

        assert title_manager._title_show_timer is None
        assert title_manager._pending_title_info is None
