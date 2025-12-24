"""
OBS Integration tests for ytplay_modules.media_control

Tests for media source operations and text source updates.
Uses mock obspython module for testing outside of OBS runtime.
"""


import obspython as obs


class TestGetCurrentVideoFromMediaSource:
    """Tests for get_current_video_from_media_source function."""

    def test_returns_none_when_source_not_found(self):
        """Should return None when media source doesn't exist."""
        from ytplay_modules.media_control import get_current_video_from_media_source

        obs.reset()

        result = get_current_video_from_media_source()

        assert result is None

    def test_returns_none_when_no_file_path(self):
        """Should return None when no file path in source."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_current_video_from_media_source

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {"local_file": ""})

        result = get_current_video_from_media_source()

        assert result is None

    def test_extracts_video_id_from_filename(self):
        """Should extract video ID from normalized filename."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_current_video_from_media_source
        from ytplay_modules.state import add_cached_video

        obs.reset()
        video_id = "abc123xyz"
        # Add video to cache so it can be found
        add_cached_video(video_id, {
            "path": f"/cache/Song_Artist_{video_id}_normalized.mp4",
            "song": "Song",
            "artist": "Artist"
        })
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {
            "local_file": f"/cache/Song_Artist_{video_id}_normalized.mp4"
        })

        result = get_current_video_from_media_source()

        assert result == video_id

    def test_returns_none_for_invalid_filename_format(self):
        """Should return None for non-normalized filename."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_current_video_from_media_source

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {
            "local_file": "/cache/some_random_video.mp4"
        })

        result = get_current_video_from_media_source()

        assert result is None


class TestForceDisableMediaLoop:
    """Tests for force_disable_media_loop function."""

    def test_disables_loop_when_enabled(self):
        """Should disable loop setting when it's enabled."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import force_disable_media_loop

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {"looping": True})

        force_disable_media_loop()

        # Check that looping was set to False
        source = obs._state._sources[MEDIA_SOURCE_NAME]
        assert source.settings.get("looping") is False

    def test_does_nothing_when_loop_disabled(self):
        """Should not update source when loop already disabled."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import force_disable_media_loop

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {"looping": False})
        obs.clear_call_log()

        force_disable_media_loop()

        # Should still release source
        assert obs.assert_call_made("obs_source_release")

    def test_handles_missing_source(self):
        """Should handle missing media source gracefully."""
        from ytplay_modules.media_control import force_disable_media_loop

        obs.reset()

        # Should not raise exception
        force_disable_media_loop()


class TestGetMediaState:
    """Tests for get_media_state function."""

    def test_returns_state_for_existing_source(self):
        """Should return media state for existing source."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_media_state

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_state(obs.OBS_MEDIA_STATE_PLAYING)

        result = get_media_state(MEDIA_SOURCE_NAME)

        assert result == obs.OBS_MEDIA_STATE_PLAYING

    def test_returns_none_state_for_missing_source(self):
        """Should return NONE state when source doesn't exist."""
        from ytplay_modules.media_control import get_media_state

        obs.reset()

        result = get_media_state("NonExistentSource")

        assert result == obs.OBS_MEDIA_STATE_NONE


class TestGetMediaDuration:
    """Tests for get_media_duration function."""

    def test_returns_duration_for_existing_source(self):
        """Should return duration for existing source."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_media_duration

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_duration(180000)  # 3 minutes

        result = get_media_duration(MEDIA_SOURCE_NAME)

        assert result == 180000

    def test_returns_zero_for_missing_source(self):
        """Should return 0 when source doesn't exist."""
        from ytplay_modules.media_control import get_media_duration

        obs.reset()

        result = get_media_duration("NonExistentSource")

        assert result == 0


class TestGetMediaTime:
    """Tests for get_media_time function."""

    def test_returns_time_for_existing_source(self):
        """Should return playback time for existing source."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import get_media_time

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source")
        obs.set_media_time(60000)  # 1 minute

        result = get_media_time(MEDIA_SOURCE_NAME)

        assert result == 60000

    def test_returns_zero_for_missing_source(self):
        """Should return 0 when source doesn't exist."""
        from ytplay_modules.media_control import get_media_time

        obs.reset()

        result = get_media_time("NonExistentSource")

        assert result == 0


class TestUpdateMediaSource:
    """Tests for update_media_source function."""

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        """Should return False when video file doesn't exist."""
        from ytplay_modules.media_control import update_media_source

        obs.reset()

        result = update_media_source("/nonexistent/file.mp4")

        assert result is False

    def test_updates_source_with_new_file(self, tmp_path):
        """Should update source with new video file."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import update_media_source

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {"local_file": ""})

        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"x" * 1024)

        result = update_media_source(str(video_file))

        assert result is True
        # Verify source was updated
        source = obs._state._sources[MEDIA_SOURCE_NAME]
        assert source.settings.get("local_file") == str(video_file)

    def test_returns_false_for_missing_source(self, tmp_path):
        """Should return False when media source doesn't exist."""
        from ytplay_modules.media_control import update_media_source

        obs.reset()

        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"x" * 1024)

        result = update_media_source(str(video_file))

        assert result is False

    def test_forces_reload_for_same_file(self, tmp_path):
        """Should use multi-step reload for same file."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import update_media_source

        obs.reset()
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"x" * 1024)

        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {
            "local_file": str(video_file)
        })

        result = update_media_source(str(video_file), force_reload=False)

        assert result is True
        # Verify timer was added for reload
        assert obs.assert_call_made("timer_add")


class TestUpdateTextSourceContent:
    """Tests for update_text_source_content function."""

    def test_updates_text_with_song_and_artist(self):
        """Should update text source with song and artist."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.media_control import update_text_source_content

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        result = update_text_source_content("Test Song", "Test Artist")

        assert result is True
        source = obs._state._sources[TEXT_SOURCE_NAME]
        assert source.settings.get("text") == "Test Song - Test Artist"

    def test_updates_text_with_song_only(self):
        """Should update with just song when artist is empty."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.media_control import update_text_source_content

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        result = update_text_source_content("Test Song", "")

        assert result is True
        source = obs._state._sources[TEXT_SOURCE_NAME]
        assert source.settings.get("text") == "Test Song"

    def test_adds_warning_when_gemini_failed(self):
        """Should add warning symbol when Gemini failed."""
        from ytplay_modules.config import TEXT_SOURCE_NAME
        from ytplay_modules.media_control import update_text_source_content

        obs.reset()
        obs.create_source(TEXT_SOURCE_NAME, "text_gdiplus")

        result = update_text_source_content("Song", "Artist", gemini_failed=True)

        assert result is True
        source = obs._state._sources[TEXT_SOURCE_NAME]
        assert "⚠" in source.settings.get("text", "")

    def test_returns_false_for_missing_source(self):
        """Should return False when text source doesn't exist."""
        from ytplay_modules.media_control import update_text_source_content

        obs.reset()

        result = update_text_source_content("Song", "Artist")

        assert result is False


class TestStopMediaSource:
    """Tests for stop_media_source function."""

    def test_stops_and_clears_media_source(self):
        """Should stop playback and clear file path."""
        from ytplay_modules.config import MEDIA_SOURCE_NAME
        from ytplay_modules.media_control import stop_media_source

        obs.reset()
        obs.create_source(MEDIA_SOURCE_NAME, "ffmpeg_source", {
            "local_file": "/path/to/video.mp4"
        })
        obs.set_media_state(obs.OBS_MEDIA_STATE_PLAYING)

        stop_media_source()

        # Verify media was stopped
        assert obs.assert_call_made("obs_source_media_stop")
        # Verify file was cleared
        source = obs._state._sources[MEDIA_SOURCE_NAME]
        assert source.settings.get("local_file") == ""

    def test_handles_missing_source(self):
        """Should handle missing source gracefully."""
        from ytplay_modules.media_control import stop_media_source

        obs.reset()

        # Should not raise exception
        stop_media_source()


class TestIsVideoNearEnd:
    """Tests for is_video_near_end function."""

    def test_returns_true_when_near_end(self):
        """Should return True when video is past threshold."""
        from ytplay_modules.media_control import is_video_near_end

        result = is_video_near_end(duration=100000, current_time=96000)

        assert result is True

    def test_returns_false_when_not_near_end(self):
        """Should return False when video is not near end."""
        from ytplay_modules.media_control import is_video_near_end

        result = is_video_near_end(duration=100000, current_time=50000)

        assert result is False

    def test_returns_false_for_zero_duration(self):
        """Should return False for zero duration."""
        from ytplay_modules.media_control import is_video_near_end

        result = is_video_near_end(duration=0, current_time=0)

        assert result is False

    def test_respects_custom_threshold(self):
        """Should respect custom threshold percentage."""
        from ytplay_modules.media_control import is_video_near_end

        # At 90%, not past 95% threshold
        result = is_video_near_end(duration=100000, current_time=90000, threshold_percent=95)
        assert result is False

        # At 90%, past 85% threshold
        result = is_video_near_end(duration=100000, current_time=90000, threshold_percent=85)
        assert result is True


class TestCancelMediaReloadTimer:
    """Tests for cancel_media_reload_timer function."""

    def test_cancels_pending_timer(self):
        """Should cancel pending reload timer."""
        from ytplay_modules import media_control

        obs.reset()
        media_control._media_reload_timer = lambda: None

        media_control.cancel_media_reload_timer()

        assert media_control._media_reload_timer is None

    def test_handles_no_timer(self):
        """Should handle case when no timer exists."""
        from ytplay_modules import media_control

        obs.reset()
        media_control._media_reload_timer = None

        # Should not raise exception
        media_control.cancel_media_reload_timer()
