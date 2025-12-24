"""
OBS Integration tests for ytplay_modules.opacity_control

Tests for text fade effects and opacity management.
Uses mock obspython module for testing outside of OBS runtime.
"""

import pytest
from unittest.mock import patch, MagicMock

import obspython as obs


class TestEnsureOpacityFilter:
    """Tests for ensure_opacity_filter function."""

    def test_returns_true_if_already_created(self):
        """Should return True if filter already created."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import ensure_opacity_filter

        obs.reset()
        opacity_control._opacity_filter_created = True

        result = ensure_opacity_filter()

        assert result is True

    def test_returns_false_if_no_text_source(self):
        """Should return False if text source doesn't exist."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import ensure_opacity_filter

        obs.reset()
        opacity_control._opacity_filter_created = False

        result = ensure_opacity_filter()

        assert result is False

    def test_creates_filter_if_not_exists(self):
        """Should create filter if it doesn't exist."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import ensure_opacity_filter
        from ytplay_modules.config import TEXT_SOURCE_NAME

        obs.reset()
        opacity_control._opacity_filter_created = False
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        result = ensure_opacity_filter()

        assert result is True
        assert opacity_control._opacity_filter_created is True


class TestUpdateTextOpacity:
    """Tests for update_text_opacity function."""

    def test_does_nothing_if_no_source(self):
        """Should return early if text source doesn't exist."""
        from ytplay_modules.opacity_control import update_text_opacity

        obs.reset()

        # Should not raise exception
        update_text_opacity(50)

    def test_updates_opacity_value(self):
        """Should update opacity in filter settings."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import update_text_opacity
        from ytplay_modules.config import TEXT_SOURCE_NAME, OPACITY_FILTER_NAME

        obs.reset()
        # Create source with filter
        source = obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        filter_source = obs.MockSource(OPACITY_FILTER_NAME, "color_filter")
        source.filters[OPACITY_FILTER_NAME] = filter_source

        update_text_opacity(75)

        # Verify filter settings were updated
        assert obs.assert_call_made("obs_source_update")


class TestFadeInText:
    """Tests for fade_in_text function."""

    def test_starts_fade_in_transition(self):
        """Should start fade in transition."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import fade_in_text

        obs.reset()
        opacity_control._current_opacity = 0.0
        opacity_control._opacity_timer = None

        fade_in_text()

        assert obs.assert_call_made("timer_add")


class TestFadeOutText:
    """Tests for fade_out_text function."""

    def test_starts_fade_out_transition(self):
        """Should start fade out transition."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import fade_out_text

        obs.reset()
        opacity_control._current_opacity = 100.0
        opacity_control._opacity_timer = None
        opacity_control._fade_direction = None

        fade_out_text()

        assert obs.assert_call_made("timer_add")

    def test_does_nothing_if_already_at_zero(self):
        """Should not start fade if already at 0."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import fade_out_text

        obs.reset()
        obs.clear_call_log()
        opacity_control._current_opacity = 0.0

        fade_out_text()

        # Should not add timer
        assert not obs.assert_call_made("timer_add")

    def test_does_nothing_if_already_fading_out(self):
        """Should not start fade if already fading out."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import fade_out_text

        obs.reset()
        obs.clear_call_log()
        opacity_control._current_opacity = 50.0
        opacity_control._fade_direction = 'out'
        opacity_control._opacity_timer = lambda: None  # Timer exists

        fade_out_text()

        # Should not add another timer
        assert not obs.assert_call_made("timer_add")


class TestCancelOpacityTimer:
    """Tests for cancel_opacity_timer function."""

    def test_cancels_timer(self):
        """Should cancel opacity timer."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import cancel_opacity_timer

        obs.reset()
        opacity_control._opacity_timer = lambda: None

        cancel_opacity_timer()

        assert opacity_control._opacity_timer is None

    def test_handles_no_timer(self):
        """Should handle case when no timer exists."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import cancel_opacity_timer

        obs.reset()
        opacity_control._opacity_timer = None

        # Should not raise exception
        cancel_opacity_timer()


class TestGetCurrentOpacity:
    """Tests for get_current_opacity function."""

    def test_returns_current_opacity(self):
        """Should return current opacity value."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import get_current_opacity

        opacity_control._current_opacity = 75.0

        assert get_current_opacity() == 75.0


class TestSetCurrentOpacity:
    """Tests for set_current_opacity function."""

    def test_sets_opacity_value(self):
        """Should set current opacity value."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import set_current_opacity
        from ytplay_modules.config import TEXT_SOURCE_NAME, OPACITY_FILTER_NAME

        obs.reset()
        # Create source with filter for update_text_opacity
        source = obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        filter_source = obs.MockSource(OPACITY_FILTER_NAME, "color_filter")
        source.filters[OPACITY_FILTER_NAME] = filter_source

        set_current_opacity(50.0)

        assert opacity_control._current_opacity == 50.0


class TestSetPendingText:
    """Tests for set_pending_text function."""

    def test_sets_pending_text(self):
        """Should set pending text info."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import set_pending_text

        text_info = {"song": "Test", "artist": "Artist"}

        set_pending_text(text_info)

        assert opacity_control._pending_text == text_info


class TestIsFading:
    """Tests for is_fading function."""

    def test_returns_true_when_fading(self):
        """Should return True when timer is active."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import is_fading

        opacity_control._opacity_timer = lambda: None

        assert is_fading() is True

    def test_returns_false_when_not_fading(self):
        """Should return False when no timer."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import is_fading

        opacity_control._opacity_timer = None

        assert is_fading() is False


class TestStartOpacityTransition:
    """Tests for start_opacity_transition function."""

    def test_cancels_existing_timer(self):
        """Should cancel existing timer before starting new one."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import start_opacity_transition

        obs.reset()
        opacity_control._opacity_timer = lambda: None
        opacity_control._current_opacity = 0.0

        start_opacity_transition(100.0, 'in')

        assert obs.assert_call_made("timer_remove")

    def test_starts_new_transition(self):
        """Should start new opacity transition."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import start_opacity_transition

        obs.reset()
        opacity_control._opacity_timer = None
        opacity_control._current_opacity = 0.0

        start_opacity_transition(100.0, 'in')

        assert opacity_control._target_opacity == 100.0
        assert opacity_control._fade_direction == 'in'
        assert obs.assert_call_made("timer_add")


class TestOpacityTransitionCallback:
    """Tests for opacity_transition_callback function."""

    def test_updates_opacity_during_fade_in(self):
        """Should update opacity during fade in."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import opacity_transition_callback
        from ytplay_modules.config import TEXT_SOURCE_NAME, OPACITY_FILTER_NAME

        obs.reset()
        source = obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        filter_source = obs.MockSource(OPACITY_FILTER_NAME, "color_filter")
        source.filters[OPACITY_FILTER_NAME] = filter_source

        opacity_control._current_opacity = 50.0
        opacity_control._target_opacity = 100.0
        opacity_control._opacity_step = 10.0
        opacity_control._fade_direction = 'in'
        opacity_control._opacity_timer = opacity_transition_callback

        opacity_transition_callback()

        # Opacity should have increased
        assert opacity_control._current_opacity == 60.0

    def test_clamps_opacity_at_target(self):
        """Should clamp opacity when reaching target."""
        from ytplay_modules import opacity_control
        from ytplay_modules.opacity_control import opacity_transition_callback
        from ytplay_modules.config import TEXT_SOURCE_NAME, OPACITY_FILTER_NAME

        obs.reset()
        source = obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        filter_source = obs.MockSource(OPACITY_FILTER_NAME, "color_filter")
        source.filters[OPACITY_FILTER_NAME] = filter_source

        opacity_control._current_opacity = 95.0
        opacity_control._target_opacity = 100.0
        opacity_control._opacity_step = 10.0  # Would overshoot
        opacity_control._fade_direction = 'in'
        opacity_control._opacity_timer = opacity_transition_callback

        opacity_transition_callback()

        # Should be clamped to target
        assert opacity_control._current_opacity == 100.0
