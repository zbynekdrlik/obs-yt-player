# Logging System Update

## Overview
This document describes the simplified logging system for the OBS YouTube Player script.

## Changes from Original Design

### Removed
- DEBUG/NORMAL level distinction
- Debug enable/disable configuration option
- Level names in log output

### New Logging Format
```
[script_name] [timestamp] message
```

Example:
```
[ytfast.py] [2025-06-16 21:30:33] AcoustID match (confidence: 0.99): Elevation Worship - Praise
```

### Implementation

#### 1. Remove debug configuration from script properties
```python
def script_properties():
    """Define script properties shown in OBS UI."""
    props = obs.obs_properties_create()
    
    # Playlist URL text field
    obs.obs_properties_add_text(
        props, 
        "playlist_url", 
        "YouTube Playlist URL", 
        obs.OBS_TEXT_DEFAULT
    )
    
    # Cache directory text field
    obs.obs_properties_add_text(
        props,
        "cache_dir",
        "Cache Directory",
        obs.OBS_TEXT_DEFAULT
    )
    
    # Sync Now button
    obs.obs_properties_add_button(
        props,
        "sync_now",
        "Sync Playlist Now",
        sync_now_callback
    )
    
    # REMOVED: debug_enabled checkbox
    
    return props
```

#### 2. Simplified log function
```python
def log(message):
    """Log messages with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{SCRIPT_NAME}] [{timestamp}] {message}")
```

#### 3. Update all log calls
Change from:
```python
log("Message", "DEBUG")
log("Message", "NORMAL")
```

To:
```python
log("Message")
```

## Benefits
- Cleaner log output
- No redundant information
- Simpler code
- All messages are treated equally
- Easier to read and debug

## Migration Notes
When updating existing code:
1. Remove `debug_enabled` from global variables
2. Remove debug checkbox from script properties
3. Update log function signature
4. Remove level parameter from all log calls
5. Update script defaults to remove debug setting