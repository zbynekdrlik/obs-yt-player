"""Tests for play_history module - persistent play tracking across restarts."""

import json
from pathlib import Path

import pytest

from ytplay_modules import state
from ytplay_modules.play_history import (
    HISTORY_FILENAME,
    clear_play_history,
    get_history_path,
    load_play_history,
    save_play_history,
)


@pytest.fixture
def temp_history_file(temp_cache_dir):
    """Provide a temporary history file path."""
    state.set_cache_dir(str(temp_cache_dir))
    return temp_cache_dir / HISTORY_FILENAME


class TestGetHistoryPath:
    """Tests for get_history_path function."""

    def test_returns_path_in_cache_dir(self, temp_cache_dir):
        """Should return path to play_history.json in cache directory."""
        state.set_cache_dir(str(temp_cache_dir))
        path = get_history_path()
        assert path == temp_cache_dir / HISTORY_FILENAME

    def test_returns_pathlib_path(self, temp_cache_dir):
        """Should return a Path object, not a string."""
        state.set_cache_dir(str(temp_cache_dir))
        path = get_history_path()
        assert isinstance(path, Path)


class TestLoadPlayHistory:
    """Tests for load_play_history function."""

    def test_returns_empty_list_when_no_file(self, temp_history_file):
        """Should return empty list when history file doesn't exist."""
        result = load_play_history()
        assert result == []

    def test_loads_video_ids_from_file(self, temp_history_file):
        """Should load video IDs from JSON file."""
        video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0", "kJQP7kiw5Fk"]
        with open(temp_history_file, "w", encoding="utf-8") as f:
            json.dump({"played_videos": video_ids}, f)

        result = load_play_history()
        assert result == video_ids

    def test_handles_legacy_list_format(self, temp_history_file):
        """Should handle legacy format where file is just a list."""
        video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0"]
        with open(temp_history_file, "w", encoding="utf-8") as f:
            json.dump(video_ids, f)

        result = load_play_history()
        assert result == video_ids

    def test_returns_empty_list_on_corrupted_json(self, temp_history_file):
        """Should return empty list when JSON is corrupted."""
        with open(temp_history_file, "w", encoding="utf-8") as f:
            f.write("not valid json {{{")

        result = load_play_history()
        assert result == []

    def test_returns_empty_list_on_missing_key(self, temp_history_file):
        """Should return empty list when played_videos key is missing."""
        with open(temp_history_file, "w", encoding="utf-8") as f:
            json.dump({"other_key": "value"}, f)

        result = load_play_history()
        assert result == []

    def test_handles_empty_file(self, temp_history_file):
        """Should return empty list when file is empty."""
        with open(temp_history_file, "w", encoding="utf-8") as f:
            pass  # Create empty file

        result = load_play_history()
        assert result == []


class TestSavePlayHistory:
    """Tests for save_play_history function."""

    def test_saves_video_ids_to_file(self, temp_history_file):
        """Should save video IDs to JSON file."""
        video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0"]
        result = save_play_history(video_ids)

        assert result is True
        with open(temp_history_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["played_videos"] == video_ids

    def test_creates_cache_directory_if_needed(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        nested_cache = tmp_path / "nested" / "cache"
        state.set_cache_dir(str(nested_cache))

        result = save_play_history(["video1"])

        assert result is True
        assert nested_cache.exists()
        assert (nested_cache / HISTORY_FILENAME).exists()

    def test_overwrites_existing_file(self, temp_history_file):
        """Should overwrite existing history file."""
        # Write initial data
        save_play_history(["old_video1", "old_video2"])

        # Write new data
        new_ids = ["new_video1"]
        save_play_history(new_ids)

        with open(temp_history_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["played_videos"] == new_ids

    def test_saves_empty_list(self, temp_history_file):
        """Should save empty list correctly."""
        result = save_play_history([])

        assert result is True
        with open(temp_history_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["played_videos"] == []

    def test_uses_indented_json(self, temp_history_file):
        """Should save with indentation for readability."""
        save_play_history(["video1", "video2"])

        with open(temp_history_file, encoding="utf-8") as f:
            content = f.read()

        # Indented JSON has newlines
        assert "\n" in content


class TestClearPlayHistory:
    """Tests for clear_play_history function."""

    def test_clears_existing_history(self, temp_history_file):
        """Should clear existing play history."""
        save_play_history(["video1", "video2", "video3"])

        result = clear_play_history()

        assert result is True
        loaded = load_play_history()
        assert loaded == []

    def test_works_when_no_file_exists(self, temp_history_file):
        """Should succeed even when no history file exists."""
        result = clear_play_history()

        assert result is True
        loaded = load_play_history()
        assert loaded == []


class TestRoundTrip:
    """Integration tests for save/load cycle."""

    def test_save_and_load_preserves_data(self, temp_history_file):
        """Should preserve video IDs through save/load cycle."""
        original_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0", "kJQP7kiw5Fk"]

        save_play_history(original_ids)
        loaded_ids = load_play_history()

        assert loaded_ids == original_ids

    def test_multiple_save_load_cycles(self, temp_history_file):
        """Should handle multiple save/load cycles correctly."""
        for i in range(3):
            video_ids = [f"video_{i}_{j}" for j in range(5)]
            save_play_history(video_ids)
            loaded = load_play_history()
            assert loaded == video_ids

    def test_handles_special_characters_in_ids(self, temp_history_file):
        """Should handle video IDs with special characters."""
        # YouTube IDs can contain letters, numbers, dashes, and underscores
        special_ids = ["abc-def_123", "_-_-_-_-_-_", "ABCDEFGHIJK"]

        save_play_history(special_ids)
        loaded = load_play_history()

        assert loaded == special_ids
