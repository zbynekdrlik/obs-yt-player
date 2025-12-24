"""
Persistent play history tracking across script restarts.
Stores played video IDs in a JSON file in the cache directory.
"""

import json
from pathlib import Path

from .logger import log


HISTORY_FILENAME = "play_history.json"


def get_history_path() -> Path:
    """Get path to play history file in cache directory."""
    # Import here to avoid circular import
    from .state import get_cache_dir

    return Path(get_cache_dir()) / HISTORY_FILENAME


def load_play_history() -> list[str]:
    """
    Load played video IDs from JSON file.

    Returns empty list if file doesn't exist or is corrupted.
    """
    path = get_history_path()
    if not path.exists():
        return []

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle both legacy list format and new dict format
            if isinstance(data, list):
                return data
            return data.get("played_videos", [])
    except (json.JSONDecodeError, OSError) as e:
        log(f"WARNING: Could not load play history: {e}")
        return []


def save_play_history(video_ids: list[str]) -> bool:
    """
    Save played video IDs to JSON file.

    Creates cache directory if it doesn't exist.
    Returns True on success, False on failure.
    """
    path = get_history_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"played_videos": video_ids}, f, indent=2)
        return True
    except OSError as e:
        log(f"ERROR: Could not save play history: {e}")
        return False


def clear_play_history() -> bool:
    """
    Clear the play history file.

    Returns True on success, False on failure.
    """
    return save_play_history([])
