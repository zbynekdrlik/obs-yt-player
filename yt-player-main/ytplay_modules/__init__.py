"""
OBS YouTube Player modules package.
"""

# This file makes the directory a Python package
# Import all modules to make them easily accessible

from . import (
    cache,
    config,
    download,
    gemini_metadata,
    logger,
    media_control,
    metadata,
    normalize,
    opacity_control,
    playback,
    playback_controller,
    playlist,
    reprocess,
    scene,
    state,
    state_handlers,
    title_manager,
    tools,
    utils,
    video_selector,
)

__all__ = [
    "cache",
    "config",
    "download",
    "gemini_metadata",
    "logger",
    "media_control",
    "metadata",
    "normalize",
    "opacity_control",
    "playback",
    "playback_controller",
    "playlist",
    "reprocess",
    "scene",
    "state",
    "state_handlers",
    "title_manager",
    "tools",
    "utils",
    "video_selector",
]
