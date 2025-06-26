"""
OBS YouTube Player - Syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), 
and plays them randomly via Media Source. Features optional AI-powered metadata extraction using Google Gemini 
for superior artist/song detection. All processing runs in background threads.
"""

import obspython as obs
import os
import sys
import traceback

# Script identity based on filename
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# Always use ytplay_modules regardless of script name
MODULES_DIR = os.path.join(os.path.dirname(SCRIPT_PATH), 'ytplay_modules')

# Add modules to path
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# Import error handling
_import_error = None

try:
    from main import (
        script_description as _script_description,
        script_load as _script_load,
        script_unload as _script_unload,
        script_properties as _script_properties,
        script_defaults as _script_defaults,
        script_update as _script_update,
        script_save as _script_save,
        sync_now_callback as _sync_now_callback
    )
except ImportError as e:
    _import_error = str(e)
    # Provide fallback functions
    def _script_description():
        return f"Error loading modules: {_import_error}"
    
    def _script_load(settings):
        print(f"[{SCRIPT_NAME}] Failed to load modules: {_import_error}")
    
    def _script_unload():
        pass
    
    def _script_properties():
        props = obs.obs_properties_create()
        obs.obs_properties_add_text(
            props,
            "error",
            f"Module Error: {_import_error}",
            obs.OBS_TEXT_INFO
        )
        return props
    
    def _script_defaults(settings):
        pass
    
    def _script_update(settings):
        pass
    
    def _script_save(settings):
        pass
    
    def _sync_now_callback(props, prop):
        return True

# OBS API functions - pass script context
def script_description():
    """Return script description for OBS."""
    return __doc__.strip()

def script_load(settings):
    """Called when script is loaded."""
    try:
        _script_load(settings, SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_load: {e}")
        traceback.print_exc()

def script_unload():
    """Called when script is unloaded."""
    try:
        _script_unload(SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_unload: {e}")
        traceback.print_exc()

def script_properties():
    """Define script properties shown in OBS UI."""
    try:
        return _script_properties(SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_properties: {e}")
        traceback.print_exc()
        props = obs.obs_properties_create()
        obs.obs_properties_add_text(
            props,
            "error",
            f"Error: {e}",
            obs.OBS_TEXT_INFO
        )
        return props

def script_defaults(settings):
    """Set default values for script properties."""
    try:
        _script_defaults(settings, SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_defaults: {e}")
        traceback.print_exc()

def script_update(settings):
    """Called when script properties are updated."""
    try:
        _script_update(settings, SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_update: {e}")
        traceback.print_exc()

def script_save(settings):
    """Called when OBS is saving data."""
    try:
        _script_save(settings, SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in script_save: {e}")
        traceback.print_exc()

def sync_now_callback(props, prop):
    """Callback for Sync Now button."""
    try:
        return _sync_now_callback(props, prop, SCRIPT_PATH)
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error in sync_now_callback: {e}")
        traceback.print_exc()
        return True
