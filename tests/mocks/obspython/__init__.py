"""
Mock obspython module for testing OBS YouTube Player outside of OBS runtime.

This module provides mock implementations of all OBS Python API functions and constants
used by the ytplay_modules package. The mock is configurable and tracks all calls for
verification in tests.
"""

from typing import Any, Callable, Optional
from unittest.mock import MagicMock
import threading

# ============================================================================
# OBS CONSTANTS
# ============================================================================

# Media states
OBS_MEDIA_STATE_NONE = 0
OBS_MEDIA_STATE_PLAYING = 1
OBS_MEDIA_STATE_OPENING = 2
OBS_MEDIA_STATE_BUFFERING = 3
OBS_MEDIA_STATE_PAUSED = 4
OBS_MEDIA_STATE_STOPPED = 5
OBS_MEDIA_STATE_ENDED = 6
OBS_MEDIA_STATE_ERROR = 7

# Frontend events
OBS_FRONTEND_EVENT_STREAMING_STARTING = 0
OBS_FRONTEND_EVENT_STREAMING_STARTED = 1
OBS_FRONTEND_EVENT_STREAMING_STOPPING = 2
OBS_FRONTEND_EVENT_STREAMING_STOPPED = 3
OBS_FRONTEND_EVENT_RECORDING_STARTING = 4
OBS_FRONTEND_EVENT_RECORDING_STARTED = 5
OBS_FRONTEND_EVENT_RECORDING_STOPPING = 6
OBS_FRONTEND_EVENT_RECORDING_STOPPED = 7
OBS_FRONTEND_EVENT_SCENE_CHANGED = 8
OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED = 9
OBS_FRONTEND_EVENT_TRANSITION_CHANGED = 10
OBS_FRONTEND_EVENT_TRANSITION_STOPPED = 11
OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED = 12
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED = 13
OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED = 14
OBS_FRONTEND_EVENT_PROFILE_CHANGED = 15
OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED = 16
OBS_FRONTEND_EVENT_EXIT = 17
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING = 18
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED = 19
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING = 20
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED = 21
OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED = 22
OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED = 23
OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED = 24
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP = 25
OBS_FRONTEND_EVENT_FINISHED_LOADING = 26
OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED = 27

# Text property types
OBS_TEXT_DEFAULT = 0
OBS_TEXT_PASSWORD = 1
OBS_TEXT_MULTILINE = 2
OBS_TEXT_INFO = 3

# Combo types
OBS_COMBO_TYPE_EDITABLE = 0
OBS_COMBO_TYPE_LIST = 1
OBS_COMBO_FORMAT_INT = 0
OBS_COMBO_FORMAT_FLOAT = 1
OBS_COMBO_FORMAT_STRING = 2

# ============================================================================
# MOCK STATE MANAGEMENT
# ============================================================================

class MockState:
    """Global state container for mock OBS environment."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all mock state to initial values."""
        self._lock = threading.Lock()

        # Sources registry: name -> MockSource
        self._sources: dict[str, "MockSource"] = {}

        # Current scene configuration
        self._current_scene_name: str = ""
        self._preview_scene_name: str = ""
        self._preview_program_mode: bool = False
        self._transition_duration: int = 300

        # Media state configuration
        self._media_state: int = OBS_MEDIA_STATE_NONE
        self._media_duration: int = 0
        self._media_time: int = 0

        # Timer tracking
        self._timers: list[tuple[Callable, int]] = []
        self._timer_callbacks: dict[int, Callable] = {}
        self._next_timer_id: int = 1

        # Event callback tracking
        self._frontend_callbacks: list[Callable] = []

        # Call tracking for verification
        self._call_log: list[tuple[str, tuple, dict]] = []

        # Nested scenes: parent_scene_name -> list of (source_name, source_type)
        self._nested_scenes: dict[str, list[tuple[str, str]]] = {}

# Global mock state instance
_state = MockState()


def reset():
    """Reset all mock state. Call this in test setup/teardown."""
    _state.reset()


def get_state() -> MockState:
    """Get the global mock state for configuration."""
    return _state


def log_call(func_name: str, *args, **kwargs):
    """Log a function call for test verification."""
    _state._call_log.append((func_name, args, kwargs))


def get_call_log() -> list:
    """Get the call log for verification."""
    return _state._call_log.copy()


def clear_call_log():
    """Clear the call log."""
    _state._call_log.clear()


# ============================================================================
# MOCK OBJECTS
# ============================================================================

class MockSource:
    """Mock OBS source object."""

    def __init__(self, name: str, source_type: str = "unknown"):
        self.name = name
        self.source_type = source_type
        self.settings: dict[str, Any] = {}
        self.filters: dict[str, "MockSource"] = {}
        self._released = False

    def __repr__(self):
        return f"MockSource(name={self.name!r}, type={self.source_type!r})"


class MockScene:
    """Mock OBS scene object."""

    def __init__(self, name: str):
        self.name = name
        self.items: list["MockSceneItem"] = []

    def __repr__(self):
        return f"MockScene(name={self.name!r})"


class MockSceneItem:
    """Mock OBS scene item object."""

    def __init__(self, source: MockSource, visible: bool = True):
        self.source = source
        self.visible = visible

    def __repr__(self):
        return f"MockSceneItem(source={self.source.name!r}, visible={self.visible})"


class MockData:
    """Mock OBS data/settings object."""

    def __init__(self, data: Optional[dict] = None):
        self._data = data.copy() if data else {}
        self._released = False

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def __repr__(self):
        return f"MockData({self._data})"


class MockProperties:
    """Mock OBS properties object."""

    def __init__(self):
        self._properties: dict[str, Any] = {}

    def __repr__(self):
        return f"MockProperties({list(self._properties.keys())})"


class MockPropertyList:
    """Mock OBS property list (for combo boxes)."""

    def __init__(self):
        self._items: list[tuple[str, Any]] = []

    def __repr__(self):
        return f"MockPropertyList({self._items})"


# ============================================================================
# STATE CONFIGURATION HELPERS
# ============================================================================

def set_current_scene_name(name: str):
    """Configure the current scene name for testing."""
    _state._current_scene_name = name


def set_preview_scene_name(name: str):
    """Configure the preview scene name for testing."""
    _state._preview_scene_name = name


def set_preview_program_mode(enabled: bool):
    """Configure studio (preview/program) mode for testing."""
    _state._preview_program_mode = enabled


def set_transition_duration(duration_ms: int):
    """Configure transition duration for testing."""
    _state._transition_duration = duration_ms


def set_media_state(state: int):
    """Configure media playback state for testing."""
    _state._media_state = state


def set_media_duration(duration_ms: int):
    """Configure media duration for testing."""
    _state._media_duration = duration_ms


def set_media_time(time_ms: int):
    """Configure media playback time for testing."""
    _state._media_time = time_ms


def create_source(name: str, source_type: str = "unknown", settings: Optional[dict] = None) -> MockSource:
    """Create a source in the mock environment."""
    source = MockSource(name, source_type)
    if settings:
        source.settings = settings.copy()
    _state._sources[name] = source
    return source


def add_nested_scene(parent_scene: str, nested_scene_name: str, visible: bool = True):
    """Add a nested scene source to a parent scene."""
    if parent_scene not in _state._nested_scenes:
        _state._nested_scenes[parent_scene] = []
    _state._nested_scenes[parent_scene].append((nested_scene_name, "scene", visible))


def get_source_text(source_name: str) -> Optional[str]:
    """Helper to get text content from a text source."""
    if source_name in _state._sources:
        return _state._sources[source_name].settings.get("text", "")
    return None


def fire_frontend_event(event: int):
    """Trigger a frontend event for all registered callbacks."""
    for callback in _state._frontend_callbacks:
        callback(event)


# ============================================================================
# OBS SOURCE FUNCTIONS
# ============================================================================

def obs_get_source_by_name(name: str) -> Optional[MockSource]:
    """Get a source by name."""
    log_call("obs_get_source_by_name", name)
    return _state._sources.get(name)


def obs_source_release(source: Optional[MockSource]):
    """Release a source reference."""
    log_call("obs_source_release", source)
    if source:
        source._released = True


def obs_source_get_name(source: Optional[MockSource]) -> str:
    """Get the name of a source."""
    log_call("obs_source_get_name", source)
    return source.name if source else ""


def obs_source_get_id(source: Optional[MockSource]) -> str:
    """Get the type ID of a source."""
    log_call("obs_source_get_id", source)
    return source.source_type if source else ""


def obs_source_get_settings(source: Optional[MockSource]) -> MockData:
    """Get source settings."""
    log_call("obs_source_get_settings", source)
    if source:
        return MockData(source.settings)
    return MockData()


def obs_source_update(source: Optional[MockSource], settings: Optional[MockData]):
    """Update source settings."""
    log_call("obs_source_update", source, settings)
    if source and settings:
        source.settings.update(settings._data)


def obs_source_create_private(source_id: str, name: str, settings: Optional[MockData]) -> MockSource:
    """Create a private source."""
    log_call("obs_source_create_private", source_id, name, settings)
    source = MockSource(name, source_id)
    if settings:
        source.settings = settings._data.copy()
    return source


def obs_source_get_filter_by_name(source: Optional[MockSource], filter_name: str) -> Optional[MockSource]:
    """Get a filter by name from a source."""
    log_call("obs_source_get_filter_by_name", source, filter_name)
    if source:
        return source.filters.get(filter_name)
    return None


def obs_source_filter_add(source: Optional[MockSource], filter_source: Optional[MockSource]):
    """Add a filter to a source."""
    log_call("obs_source_filter_add", source, filter_source)
    if source and filter_source:
        source.filters[filter_source.name] = filter_source


# ============================================================================
# OBS MEDIA SOURCE FUNCTIONS
# ============================================================================

def obs_source_media_get_state(source: Optional[MockSource]) -> int:
    """Get media playback state."""
    log_call("obs_source_media_get_state", source)
    return _state._media_state


def obs_source_media_get_duration(source: Optional[MockSource]) -> int:
    """Get media duration in milliseconds."""
    log_call("obs_source_media_get_duration", source)
    return _state._media_duration


def obs_source_media_get_time(source: Optional[MockSource]) -> int:
    """Get current media playback time in milliseconds."""
    log_call("obs_source_media_get_time", source)
    return _state._media_time


def obs_source_media_restart(source: Optional[MockSource]):
    """Restart media playback."""
    log_call("obs_source_media_restart", source)
    _state._media_time = 0
    _state._media_state = OBS_MEDIA_STATE_PLAYING


def obs_source_media_stop(source: Optional[MockSource]):
    """Stop media playback."""
    log_call("obs_source_media_stop", source)
    _state._media_state = OBS_MEDIA_STATE_STOPPED


# ============================================================================
# OBS SCENE FUNCTIONS
# ============================================================================

def obs_scene_from_source(source: Optional[MockSource]) -> Optional[MockScene]:
    """Get a scene from a source."""
    log_call("obs_scene_from_source", source)
    if source and source.source_type == "scene":
        scene = MockScene(source.name)
        # Add nested scene items if configured
        if source.name in _state._nested_scenes:
            for nested_name, nested_type, visible in _state._nested_scenes[source.name]:
                nested_source = MockSource(nested_name, nested_type)
                scene.items.append(MockSceneItem(nested_source, visible))
        return scene
    return None


def obs_scene_enum_items(scene: Optional[MockScene]) -> list[MockSceneItem]:
    """Enumerate items in a scene."""
    log_call("obs_scene_enum_items", scene)
    return scene.items if scene else []


def obs_sceneitem_visible(item: Optional[MockSceneItem]) -> bool:
    """Check if a scene item is visible."""
    log_call("obs_sceneitem_visible", item)
    return item.visible if item else False


def obs_sceneitem_get_source(item: Optional[MockSceneItem]) -> Optional[MockSource]:
    """Get the source of a scene item."""
    log_call("obs_sceneitem_get_source", item)
    return item.source if item else None


def sceneitem_list_release(items: list):
    """Release a scene item list."""
    log_call("sceneitem_list_release", items)


# ============================================================================
# OBS FRONTEND FUNCTIONS
# ============================================================================

def obs_frontend_get_current_scene() -> Optional[MockSource]:
    """Get the current scene source."""
    log_call("obs_frontend_get_current_scene")
    if _state._current_scene_name:
        source = MockSource(_state._current_scene_name, "scene")
        _state._sources[_state._current_scene_name] = source
        return source
    return None


def obs_frontend_get_current_preview_scene() -> Optional[MockSource]:
    """Get the current preview scene source."""
    log_call("obs_frontend_get_current_preview_scene")
    if _state._preview_scene_name:
        return MockSource(_state._preview_scene_name, "scene")
    return None


def obs_frontend_preview_program_mode_active() -> bool:
    """Check if studio mode (preview/program) is active."""
    log_call("obs_frontend_preview_program_mode_active")
    return _state._preview_program_mode


def obs_frontend_get_transition_duration() -> int:
    """Get the current transition duration in milliseconds."""
    log_call("obs_frontend_get_transition_duration")
    return _state._transition_duration


def obs_frontend_add_event_callback(callback: Callable):
    """Register a frontend event callback."""
    log_call("obs_frontend_add_event_callback", callback)
    _state._frontend_callbacks.append(callback)


# ============================================================================
# OBS DATA FUNCTIONS
# ============================================================================

def obs_data_create() -> MockData:
    """Create a new data/settings object."""
    log_call("obs_data_create")
    return MockData()


def obs_data_release(data: Optional[MockData]):
    """Release a data object."""
    log_call("obs_data_release", data)
    if data:
        data._released = True


def obs_data_get_string(data: Optional[MockData], name: str) -> str:
    """Get a string value from data."""
    log_call("obs_data_get_string", data, name)
    if data:
        return str(data.get(name, ""))
    return ""


def obs_data_get_bool(data: Optional[MockData], name: str) -> bool:
    """Get a boolean value from data."""
    log_call("obs_data_get_bool", data, name)
    if data:
        return bool(data.get(name, False))
    return False


def obs_data_get_int(data: Optional[MockData], name: str) -> int:
    """Get an integer value from data."""
    log_call("obs_data_get_int", data, name)
    if data:
        return int(data.get(name, 0))
    return 0


def obs_data_set_string(data: Optional[MockData], name: str, value: str):
    """Set a string value in data."""
    log_call("obs_data_set_string", data, name, value)
    if data:
        data.set(name, value)


def obs_data_set_bool(data: Optional[MockData], name: str, value: bool):
    """Set a boolean value in data."""
    log_call("obs_data_set_bool", data, name, value)
    if data:
        data.set(name, value)


def obs_data_set_int(data: Optional[MockData], name: str, value: int):
    """Set an integer value in data."""
    log_call("obs_data_set_int", data, name, value)
    if data:
        data.set(name, value)


def obs_data_set_default_string(data: Optional[MockData], name: str, value: str):
    """Set a default string value in data."""
    log_call("obs_data_set_default_string", data, name, value)
    if data and name not in data._data:
        data.set(name, value)


def obs_data_set_default_bool(data: Optional[MockData], name: str, value: bool):
    """Set a default boolean value in data."""
    log_call("obs_data_set_default_bool", data, name, value)
    if data and name not in data._data:
        data.set(name, value)


# ============================================================================
# OBS PROPERTIES FUNCTIONS
# ============================================================================

def obs_properties_create() -> MockProperties:
    """Create a new properties object."""
    log_call("obs_properties_create")
    return MockProperties()


def obs_properties_add_text(props: MockProperties, name: str, description: str, text_type: int) -> Any:
    """Add a text property."""
    log_call("obs_properties_add_text", props, name, description, text_type)
    if props:
        props._properties[name] = {"type": "text", "description": description, "text_type": text_type}
    return MagicMock()


def obs_properties_add_bool(props: MockProperties, name: str, description: str) -> Any:
    """Add a boolean property."""
    log_call("obs_properties_add_bool", props, name, description)
    if props:
        props._properties[name] = {"type": "bool", "description": description}
    return MagicMock()


def obs_properties_add_list(props: MockProperties, name: str, description: str, combo_type: int, combo_format: int) -> MockPropertyList:
    """Add a list property."""
    log_call("obs_properties_add_list", props, name, description, combo_type, combo_format)
    prop_list = MockPropertyList()
    if props:
        props._properties[name] = {"type": "list", "description": description, "list": prop_list}
    return prop_list


def obs_properties_add_button(props: MockProperties, name: str, description: str, callback: Callable) -> Any:
    """Add a button property."""
    log_call("obs_properties_add_button", props, name, description, callback)
    if props:
        props._properties[name] = {"type": "button", "description": description, "callback": callback}
    return MagicMock()


def obs_property_list_add_string(prop_list: MockPropertyList, name: str, value: str):
    """Add a string option to a list property."""
    log_call("obs_property_list_add_string", prop_list, name, value)
    if prop_list:
        prop_list._items.append((name, value))


# ============================================================================
# OBS TIMER FUNCTIONS
# ============================================================================

def timer_add(callback: Callable, interval_ms: int):
    """Add a timer callback."""
    log_call("timer_add", callback, interval_ms)
    with _state._lock:
        timer_id = _state._next_timer_id
        _state._next_timer_id += 1
        _state._timer_callbacks[timer_id] = callback
        _state._timers.append((callback, interval_ms))


def timer_remove(callback: Callable):
    """Remove a timer callback."""
    log_call("timer_remove", callback)
    with _state._lock:
        _state._timers = [(cb, interval) for cb, interval in _state._timers if cb != callback]
        # Remove from callbacks dict
        to_remove = [tid for tid, cb in _state._timer_callbacks.items() if cb == callback]
        for tid in to_remove:
            del _state._timer_callbacks[tid]


def get_active_timers() -> list[tuple[Callable, int]]:
    """Get list of active timers for testing."""
    return _state._timers.copy()


def execute_timer(callback: Callable):
    """Manually execute a timer callback for testing."""
    callback()


def execute_all_timers():
    """Execute all registered timer callbacks once."""
    for callback, _ in _state._timers.copy():
        try:
            callback()
        except Exception:
            pass


# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

def assert_source_exists(name: str) -> bool:
    """Assert that a source exists."""
    return name in _state._sources


def assert_call_made(func_name: str) -> bool:
    """Assert that a function was called."""
    return any(call[0] == func_name for call in _state._call_log)


def get_calls_for(func_name: str) -> list[tuple]:
    """Get all calls to a specific function."""
    return [(args, kwargs) for name, args, kwargs in _state._call_log if name == func_name]


def count_calls(func_name: str) -> int:
    """Count calls to a specific function."""
    return sum(1 for name, _, _ in _state._call_log if name == func_name)
