"""
Unit tests for ytplay_modules.video_selector

Tests for video selection logic and playback modes.
Target: 100% coverage
"""



class TestSelectNextVideo:
    """Tests for select_next_video function."""

    def test_returns_none_when_no_videos(self):
        """Should return None when no cached videos."""
        from ytplay_modules.state import get_cached_videos
        from ytplay_modules.video_selector import select_next_video

        # Ensure cache is empty (reset happens in conftest)
        assert len(get_cached_videos()) == 0

        result = select_next_video()
        assert result is None

    def test_selects_video_when_available(self):
        """Should select a video when cache has videos."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import select_next_video

        add_cached_video("test_vid1", {
            "path": "/cache/test1.mp4",
            "song": "Test Song",
            "artist": "Test Artist"
        })

        result = select_next_video()
        assert result == "test_vid1"

    def test_single_video_always_selected(self):
        """When only one video, always return it."""
        from ytplay_modules.state import add_cached_video, clear_played_videos
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        add_cached_video("only_video", {
            "path": "/cache/only.mp4",
            "song": "Only Song",
            "artist": "Only Artist"
        })

        # Select multiple times
        for _ in range(5):
            result = select_next_video()
            assert result == "only_video"

    def test_random_selection_from_multiple(self):
        """Should select from multiple available videos."""
        from ytplay_modules.state import add_cached_video, clear_played_videos
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        video_ids = ["vid_a", "vid_b", "vid_c"]
        for vid_id in video_ids:
            add_cached_video(vid_id, {
                "path": f"/cache/{vid_id}.mp4",
                "song": f"Song {vid_id}",
                "artist": f"Artist {vid_id}"
            })

        result = select_next_video()
        assert result in video_ids

    def test_no_repeat_until_all_played(self):
        """Should not repeat videos until all have been played."""
        from ytplay_modules.state import add_cached_video, clear_played_videos
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        video_ids = ["no_repeat_a", "no_repeat_b", "no_repeat_c"]
        for vid_id in video_ids:
            add_cached_video(vid_id, {
                "path": f"/cache/{vid_id}.mp4",
                "song": f"Song {vid_id}",
                "artist": f"Artist {vid_id}"
            })

        selected = []
        for _ in range(3):
            result = select_next_video()
            assert result not in selected, f"{result} was already selected"
            selected.append(result)

        assert set(selected) == set(video_ids)

    def test_reset_played_list_when_all_played(self):
        """Should reset played list after all videos played."""
        from ytplay_modules.state import add_cached_video, clear_played_videos
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        video_ids = ["reset_a", "reset_b"]
        for vid_id in video_ids:
            add_cached_video(vid_id, {
                "path": f"/cache/{vid_id}.mp4",
                "song": f"Song {vid_id}",
                "artist": f"Artist {vid_id}"
            })

        # Play all videos
        select_next_video()
        select_next_video()

        # At this point all are played, next select should reset
        result = select_next_video()
        assert result in video_ids

    def test_loop_mode_returns_loop_video(self):
        """In loop mode, should return the loop video if set."""
        from ytplay_modules.config import PLAYBACK_MODE_LOOP
        from ytplay_modules.state import add_cached_video, clear_played_videos, set_loop_video_id, set_playback_mode
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        add_cached_video("loop_vid", {
            "path": "/cache/loop.mp4",
            "song": "Loop Song",
            "artist": "Loop Artist"
        })
        add_cached_video("other_vid", {
            "path": "/cache/other.mp4",
            "song": "Other Song",
            "artist": "Other Artist"
        })

        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_loop_video_id("loop_vid")

        # Should always return loop video
        for _ in range(3):
            result = select_next_video()
            assert result == "loop_vid"

    def test_loop_mode_sets_loop_video_if_not_set(self):
        """In loop mode, should set loop video on first selection."""
        from ytplay_modules.config import PLAYBACK_MODE_LOOP
        from ytplay_modules.state import (
            add_cached_video,
            clear_played_videos,
            get_loop_video_id,
            set_loop_video_id,
            set_playback_mode,
        )
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_loop_video_id(None)  # Clear any existing loop video

        add_cached_video("auto_loop", {
            "path": "/cache/auto_loop.mp4",
            "song": "Auto Loop",
            "artist": "Artist"
        })

        set_playback_mode(PLAYBACK_MODE_LOOP)

        result = select_next_video()
        assert result == "auto_loop"
        assert get_loop_video_id() == "auto_loop"

    def test_loop_mode_with_missing_loop_video(self):
        """Loop mode should handle missing loop video gracefully."""
        from ytplay_modules.config import PLAYBACK_MODE_LOOP
        from ytplay_modules.state import add_cached_video, clear_played_videos, set_loop_video_id, set_playback_mode
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_loop_video_id("missing_video")  # Set loop to non-existent video

        add_cached_video("fallback_vid", {
            "path": "/cache/fallback.mp4",
            "song": "Fallback",
            "artist": "Artist"
        })

        set_playback_mode(PLAYBACK_MODE_LOOP)

        # Should fall through to normal selection since loop video not in cache
        result = select_next_video()
        assert result == "fallback_vid"

    def test_continuous_mode(self):
        """Continuous mode should cycle through videos."""
        from ytplay_modules.config import PLAYBACK_MODE_CONTINUOUS
        from ytplay_modules.state import add_cached_video, clear_played_videos, set_playback_mode
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_playback_mode(PLAYBACK_MODE_CONTINUOUS)

        add_cached_video("cont_a", {"path": "/a.mp4", "song": "A", "artist": "A"})
        add_cached_video("cont_b", {"path": "/b.mp4", "song": "B", "artist": "B"})

        # Should select different videos
        results = [select_next_video(), select_next_video()]
        assert len(set(results)) == 2  # Both should be different


class TestValidateVideoFile:
    """Tests for validate_video_file function."""

    def test_returns_false_for_nonexistent_video_info(self):
        """Should return False if video ID has no info."""
        from ytplay_modules.video_selector import validate_video_file

        result = validate_video_file("nonexistent_id")
        assert result is False

    def test_returns_false_for_missing_file(self):
        """Should return False if video file doesn't exist."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import validate_video_file

        add_cached_video("missing_file_vid", {
            "path": "/nonexistent/path/video.mp4",
            "song": "Test",
            "artist": "Test"
        })

        result = validate_video_file("missing_file_vid")
        assert result is False

    def test_returns_true_for_existing_file(self, tmp_path):
        """Should return True if video file exists."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import validate_video_file

        # Create a temporary file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"x" * 1024)

        add_cached_video("existing_file_vid", {
            "path": str(video_file),
            "song": "Test",
            "artist": "Test"
        })

        result = validate_video_file("existing_file_vid")
        assert result is True


class TestGetVideoDisplayInfo:
    """Tests for get_video_display_info function."""

    def test_returns_defaults_for_nonexistent_video(self):
        """Should return default values for unknown video."""
        from ytplay_modules.video_selector import get_video_display_info

        result = get_video_display_info("unknown_vid_id")

        assert result["song"] == "Unknown Song"
        assert result["artist"] == "Unknown Artist"
        assert result["gemini_failed"] is False

    def test_returns_video_metadata(self):
        """Should return video metadata from cache."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import get_video_display_info

        add_cached_video("display_info_vid", {
            "path": "/cache/test.mp4",
            "song": "My Song Title",
            "artist": "My Artist Name",
            "gemini_failed": True
        })

        result = get_video_display_info("display_info_vid")

        assert result["song"] == "My Song Title"
        assert result["artist"] == "My Artist Name"
        assert result["gemini_failed"] is True

    def test_handles_missing_metadata_fields(self):
        """Should handle missing metadata with defaults."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import get_video_display_info

        # Video with minimal info
        add_cached_video("minimal_info_vid", {
            "path": "/cache/test.mp4"
        })

        result = get_video_display_info("minimal_info_vid")

        assert result["song"] == "Unknown Song"
        assert result["artist"] == "Unknown Artist"
        assert result["gemini_failed"] is False

    def test_handles_partial_metadata(self):
        """Should handle partially filled metadata."""
        from ytplay_modules.state import add_cached_video
        from ytplay_modules.video_selector import get_video_display_info

        add_cached_video("partial_info_vid", {
            "path": "/cache/test.mp4",
            "song": "Only Song"
            # Missing artist and gemini_failed
        })

        result = get_video_display_info("partial_info_vid")

        assert result["song"] == "Only Song"
        assert result["artist"] == "Unknown Artist"
        assert result["gemini_failed"] is False


class TestPlaybackModeIntegration:
    """Integration tests for different playback modes."""

    def test_single_mode_behavior(self):
        """Single mode should be handled by playback controller, not selector."""
        from ytplay_modules.config import PLAYBACK_MODE_SINGLE
        from ytplay_modules.state import add_cached_video, clear_played_videos, set_playback_mode
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_playback_mode(PLAYBACK_MODE_SINGLE)

        add_cached_video("single_vid", {
            "path": "/cache/single.mp4",
            "song": "Single",
            "artist": "Artist"
        })

        # Video selector still selects, single mode is handled at playback level
        result = select_next_video()
        assert result == "single_vid"

    def test_mode_switching(self):
        """Should handle switching between modes."""
        from ytplay_modules.config import PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_LOOP
        from ytplay_modules.state import (
            add_cached_video,
            clear_played_videos,
            set_loop_video_id,
            set_playback_mode,
        )
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_loop_video_id(None)

        add_cached_video("switch_a", {"path": "/a.mp4", "song": "A", "artist": "A"})
        add_cached_video("switch_b", {"path": "/b.mp4", "song": "B", "artist": "B"})

        # Start in continuous mode
        set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
        result1 = select_next_video()
        assert result1 in ["switch_a", "switch_b"]

        # Switch to loop mode
        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_loop_video_id("switch_a")

        result2 = select_next_video()
        assert result2 == "switch_a"  # Should return loop video

        # Switch back to continuous
        set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
        # Should resume normal selection (not always loop)


class TestRandomnessAndDistribution:
    """Tests for random selection distribution."""

    def test_selection_covers_all_videos(self):
        """All videos should eventually be selected over many iterations."""
        from ytplay_modules.config import PLAYBACK_MODE_CONTINUOUS
        from ytplay_modules.state import add_cached_video, clear_played_videos, set_playback_mode
        from ytplay_modules.video_selector import select_next_video

        clear_played_videos()
        set_playback_mode(PLAYBACK_MODE_CONTINUOUS)

        video_ids = [f"dist_vid_{i}" for i in range(5)]
        for vid_id in video_ids:
            add_cached_video(vid_id, {
                "path": f"/cache/{vid_id}.mp4",
                "song": f"Song {vid_id}",
                "artist": "Artist"
            })

        selected_set = set()
        # Select enough times to cover all videos at least once
        for _ in range(20):
            result = select_next_video()
            selected_set.add(result)
            if selected_set == set(video_ids):
                break

        assert selected_set == set(video_ids), "Not all videos were selected"
