"""
OBS Integration tests for ytplay_modules.scene

Tests for scene management, nested scene detection, and frontend events.
Uses mock obspython module for testing outside of OBS runtime.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

# The conftest.py injects mock obspython before any imports
import obspython as obs


class TestVerifySceneSetup:
    """Tests for verify_scene_setup function."""

    def test_returns_early_when_scene_missing(self):
        """Should return early when scene doesn't exist."""
        from ytplay_modules.scene import verify_scene_setup

        # Ensure scene doesn't exist
        obs.reset()

        verify_scene_setup()

        # When scene is missing, we return early - timer_remove only called if scene exists
        # Check that obs_get_source_by_name was called
        assert obs.assert_call_made("obs_get_source_by_name")

    def test_checks_media_and_text_sources(self, capfd):
        """Should check for media and text sources."""
        from ytplay_modules.scene import verify_scene_setup
        from ytplay_modules.config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME

        obs.reset()
        # Create scene source
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)

        verify_scene_setup()

        # Verify it looked for the sources
        assert obs.assert_call_made("obs_get_source_by_name")

    def test_releases_sources_after_check(self):
        """Should properly release sources after checking."""
        from ytplay_modules.scene import verify_scene_setup
        from ytplay_modules.config import SCENE_NAME, MEDIA_SOURCE_NAME, TEXT_SOURCE_NAME

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")
        obs.set_current_scene_name(SCENE_NAME)

        verify_scene_setup()

        # Check that release was called
        assert obs.assert_call_made("obs_source_release")


class TestIsSceneVisibleNested:
    """Tests for is_scene_visible_nested function."""

    def test_returns_false_when_no_current_scene(self):
        """Should return False when no current scene."""
        from ytplay_modules.scene import is_scene_visible_nested

        obs.reset()
        obs.set_current_scene_name("")

        result = is_scene_visible_nested("TestScene")

        assert result is False

    def test_returns_false_when_no_scene_items(self):
        """Should return False when scene has no items."""
        from ytplay_modules.scene import is_scene_visible_nested

        obs.reset()
        obs.create_source("MainScene", "scene")
        obs.set_current_scene_name("MainScene")

        result = is_scene_visible_nested("NestedScene")

        assert result is False

    def test_finds_visible_nested_scene(self):
        """Should find scene when it's nested and visible."""
        from ytplay_modules.scene import is_scene_visible_nested
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        # Create parent scene with nested scene
        obs.create_source("ParentScene", "scene")
        obs.add_nested_scene("ParentScene", SCENE_NAME, visible=True)
        obs.set_current_scene_name("ParentScene")

        result = is_scene_visible_nested(SCENE_NAME)

        assert result is True

    def test_ignores_hidden_nested_scene(self):
        """Should ignore nested scene if it's not visible."""
        from ytplay_modules.scene import is_scene_visible_nested
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        obs.create_source("ParentScene", "scene")
        # Explicitly pass False for visible=False
        obs._state._nested_scenes["ParentScene"] = [(SCENE_NAME, "scene", False)]
        obs.set_current_scene_name("ParentScene")

        result = is_scene_visible_nested(SCENE_NAME)

        assert result is False


class TestIsSceneActiveOrNested:
    """Tests for is_scene_active_or_nested function."""

    def test_returns_true_when_scene_is_direct(self):
        """Should return True when scene is directly active."""
        from ytplay_modules.scene import is_scene_active_or_nested
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)

        result = is_scene_active_or_nested()

        assert result is True

    def test_returns_true_when_scene_is_nested(self):
        """Should return True when scene is nested in current scene."""
        from ytplay_modules.scene import is_scene_active_or_nested
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        obs.create_source("OtherScene", "scene")
        obs.add_nested_scene("OtherScene", SCENE_NAME, visible=True)
        obs.set_current_scene_name("OtherScene")

        result = is_scene_active_or_nested()

        assert result is True

    def test_returns_false_when_scene_not_active(self):
        """Should return False when scene is not active or nested."""
        from ytplay_modules.scene import is_scene_active_or_nested
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        obs.create_source("DifferentScene", "scene")
        obs.set_current_scene_name("DifferentScene")

        result = is_scene_active_or_nested()

        assert result is False


class TestVerifyInitialState:
    """Tests for verify_initial_state function."""

    def test_sets_scene_active_when_active(self):
        """Should set scene active when it is active."""
        from ytplay_modules.scene import verify_initial_state
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)

        verify_initial_state()

        assert is_scene_active() is True

    def test_sets_scene_inactive_when_not_active(self):
        """Should set scene inactive when it's not active."""
        from ytplay_modules.scene import verify_initial_state
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active, set_scene_active

        obs.reset()
        obs.set_current_scene_name("SomeOtherScene")
        # Pre-set to active
        set_scene_active(True)

        verify_initial_state()

        assert is_scene_active() is False


class TestGetPreviewSceneName:
    """Tests for get_preview_scene_name function."""

    def test_returns_preview_scene_name(self):
        """Should return the preview scene name."""
        from ytplay_modules.scene import get_preview_scene_name

        obs.reset()
        obs.set_preview_scene_name("PreviewScene")

        result = get_preview_scene_name()

        assert result == "PreviewScene"

    def test_returns_none_when_no_preview(self):
        """Should return None when no preview scene."""
        from ytplay_modules.scene import get_preview_scene_name

        obs.reset()
        obs.set_preview_scene_name("")

        result = get_preview_scene_name()

        assert result is None


class TestIsStudioModeActive:
    """Tests for is_studio_mode_active function."""

    def test_returns_true_when_studio_mode_active(self):
        """Should return True when studio mode is active."""
        from ytplay_modules.scene import is_studio_mode_active

        obs.reset()
        obs.set_preview_program_mode(True)

        result = is_studio_mode_active()

        assert result is True

    def test_returns_false_when_studio_mode_inactive(self):
        """Should return False when studio mode is inactive."""
        from ytplay_modules.scene import is_studio_mode_active

        obs.reset()
        obs.set_preview_program_mode(False)

        result = is_studio_mode_active()

        assert result is False


class TestOnFrontendEvent:
    """Tests for on_frontend_event handler."""

    def test_handles_scene_changed_event(self):
        """Should handle scene change event."""
        from ytplay_modules.scene import on_frontend_event
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)

        on_frontend_event(obs.OBS_FRONTEND_EVENT_SCENE_CHANGED)

        # Scene should now be detected as active
        assert is_scene_active() is True

    def test_handles_preview_change_event_in_studio_mode(self):
        """Should handle preview change in studio mode."""
        from ytplay_modules.scene import on_frontend_event
        from ytplay_modules.config import SCENE_NAME

        obs.reset()
        obs.set_preview_program_mode(True)
        obs.set_preview_scene_name(SCENE_NAME)
        obs.create_source("CurrentScene", "scene")
        obs.set_current_scene_name("CurrentScene")

        # Should not raise exception
        on_frontend_event(obs.OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED)

    def test_handles_transition_duration_changed(self):
        """Should handle transition duration change."""
        from ytplay_modules.scene import on_frontend_event

        obs.reset()
        obs.set_transition_duration(500)

        # Should not raise exception
        on_frontend_event(obs.OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED)

    def test_handles_obs_exit_event(self):
        """Should handle OBS exit event."""
        from ytplay_modules.scene import on_frontend_event
        from ytplay_modules.state import should_stop_threads

        obs.reset()

        on_frontend_event(obs.OBS_FRONTEND_EVENT_EXIT)

        # Stop threads should be set
        assert should_stop_threads() is True

    def test_handles_finished_loading_event(self):
        """Should handle finished loading event."""
        from ytplay_modules.scene import on_frontend_event
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)

        on_frontend_event(obs.OBS_FRONTEND_EVENT_FINISHED_LOADING)

        assert is_scene_active() is True

    def test_handles_exception_gracefully(self):
        """Should handle exceptions in event handler gracefully."""
        from ytplay_modules.scene import on_frontend_event

        obs.reset()
        # Set up invalid state that might cause issues
        obs.set_current_scene_name("")

        # Should not raise exception
        on_frontend_event(obs.OBS_FRONTEND_EVENT_SCENE_CHANGED)


class TestHandleSceneChange:
    """Tests for handle_scene_change function."""

    def test_activates_scene_when_becoming_active(self):
        """Should activate scene when it becomes active."""
        from ytplay_modules.scene import handle_scene_change
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active, set_scene_active

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)
        set_scene_active(False)  # Start inactive

        handle_scene_change()

        assert is_scene_active() is True

    def test_deactivates_scene_when_becoming_inactive(self):
        """Should deactivate scene when it becomes inactive."""
        from ytplay_modules.scene import handle_scene_change
        from ytplay_modules.config import SCENE_NAME
        from ytplay_modules.state import is_scene_active, set_scene_active

        obs.reset()
        obs.set_current_scene_name("OtherScene")
        set_scene_active(True)  # Start active
        obs.set_transition_duration(100)  # Short transition to trigger immediate deactivation

        handle_scene_change()

        assert is_scene_active() is False

    def test_resets_first_video_in_single_mode(self):
        """Should reset first video flag in single mode when scene activates."""
        from ytplay_modules.scene import handle_scene_change
        from ytplay_modules.config import SCENE_NAME, PLAYBACK_MODE_SINGLE
        from ytplay_modules.state import (
            set_scene_active, is_first_video_played,
            set_first_video_played, set_playback_mode
        )

        obs.reset()
        obs.create_source(SCENE_NAME, "scene")
        obs.set_current_scene_name(SCENE_NAME)
        set_scene_active(False)
        set_playback_mode(PLAYBACK_MODE_SINGLE)
        set_first_video_played(True)

        handle_scene_change()

        # First video flag should be reset
        assert is_first_video_played() is False


class TestHandleObsExit:
    """Tests for handle_obs_exit function."""

    def test_sets_stop_threads_flag(self):
        """Should set stop threads flag on exit."""
        from ytplay_modules.scene import handle_obs_exit
        from ytplay_modules.state import should_stop_threads

        obs.reset()

        handle_obs_exit()

        assert should_stop_threads() is True

    def test_cancels_pending_timers(self):
        """Should cancel pending deactivation timers."""
        from ytplay_modules import scene

        obs.reset()
        # Set up a pending timer
        scene._deactivation_timer = lambda: None

        scene.handle_obs_exit()

        # Timer should be cancelled
        assert scene._deactivation_timer is None
