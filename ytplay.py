"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads.
"""

import obspython as obs
import sys
import os
from pathlib import Path

# Script identification based on filename
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# IMPORTANT: All scripts share the same modules directory
MODULES_DIR = os.path.join(SCRIPT_DIR, "ytplay_modules")

# Create shared modules directory if it doesn't exist
Path(MODULES_DIR).mkdir(exist_ok=True)

# Add parent directory to Python path to enable package imports
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Import main entry points with error handling
import_error = None
try:
    from ytplay_modules.main import (
        script_description as _script_description,
        script_load as _script_load,
        script_unload as _script_unload,
        script_properties as _script_properties,
        script_defaults as _script_defaults,
        script_update as _script_update,
        script_save as _script_save,
        sync_now_callback
    )
    
    # Pass script context to all functions
    def script_description():
        return _script_description()
    
    def script_load(settings):
        return _script_load(settings, SCRIPT_PATH)
    
    def script_unload():
        return _script_unload(SCRIPT_PATH)
    
    def script_properties():
        return _script_properties(SCRIPT_PATH)
    
    def script_defaults(settings):
        return _script_defaults(settings, SCRIPT_PATH)
    
    def script_update(settings):
        return _script_update(settings, SCRIPT_PATH)
    
    def script_save(settings):
        return _script_save(settings, SCRIPT_PATH)
    
except ImportError as e:
    import_error = str(e)
    
    # Provide minimal functionality if modules can't be loaded
    def script_description():
        return f"Error loading ytplay_modules: {import_error}\n\nPlease ensure ytplay_modules directory exists with all required files."
    
    def script_load(settings):
        obs.script_log(obs.LOG_ERROR, f"[{SCRIPT_NAME}] Failed to load modules: {import_error}")
    
    def script_unload():
        pass
    
    def script_properties():
        props = obs.obs_properties_create()
        obs.obs_properties_add_text(
            props,
            "error",
            f"Error: {import_error}",
            obs.OBS_TEXT_INFO
        )
        return props
    
    def script_defaults(settings):
        pass
    
    def script_update(settings):
        pass
    
    def script_save(settings):
        pass
    
    def sync_now_callback(props, prop):
        return True
