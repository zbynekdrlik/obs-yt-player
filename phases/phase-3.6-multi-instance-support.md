# Phase 3.6: True Multi-Instance Support

## Overview
Implement proper state isolation to enable true multi-instance support, allowing multiple scripts to run simultaneously without state contamination.

## Current Problem (v3.5.9)
The `ytplay_modules/state.py` module uses global variables that are shared between all script instances. When users run multiple scripts (e.g., `ytplay.py` and `ytfast.py`), they overwrite each other's state, causing:
- Wrong script names in logs
- Configuration warnings showing incorrect values
- Scripts accessing each other's playlist URLs and settings

### Example of Current Problem
```
[ytplay.py] [2025-06-25 22:05:18] [ytfast] Starting playlist synchronization
[ytplay.py] [2025-06-25 22:05:18] [ytfast] Cache directory ready: C:\Users\zbynek\Documents\GitHub\obs-yt-player\ytplay-cache
```
Notice how ytplay.py is showing [ytfast] in its logs - this should not happen.

## Implementation Task

### Technical Requirements

#### 1. Analyze Current Architecture
- Review `ytplay_modules/state.py` and identify all global state variables
- Map out all modules that access state (logger.py, scene.py, playback.py, etc.)
- Document the current API (all get/set functions)

#### 2. Design New State Architecture
Choose and implement ONE of these approaches:

**Option A: Instance-Based State Objects**
```python
class ScriptState:
    def __init__(self, script_name, script_dir):
        self.script_name = script_name
        self.script_dir = script_dir
        self.playlist_url = ""
        self._lock = threading.Lock()
        # ... other state variables
```

**Option B: Script Registry Pattern**
```python
_script_states = {}  # {script_name: state_dict}

def get_state(script_name):
    return _script_states.get(script_name, {})
```

**Option C: Context Manager Pattern**
```python
class ScriptContext:
    _contexts = {}
    
    @classmethod
    def get_current(cls):
        # Determine current script from call stack or thread
        pass
```

### 3. Implementation Steps
1. Create new state management system that isolates each script instance
2. Maintain thread safety with proper locking
3. Preserve the existing API - all current get/set functions must continue to work
4. Update the main script (ytplay.py) to initialize script-specific state
5. Ensure background threads can access the correct script context
6. Update logger.py to always log with the correct script name
7. Test with multiple simultaneous script instances

### 4. Key Files to Modify
- `ytplay_modules/state.py` - Complete refactor
- `ytplay.py` - Initialize script-specific state
- `ytplay_modules/logger.py` - Update to use new state mechanism
- All modules using state getters/setters - Update if needed

### 5. Backward Compatibility
- Existing single-script setups must continue working without changes
- The public API (get/set functions) must remain the same
- Default behavior for single instances should be unchanged

### 6. Testing Requirements
Create test scenarios for:
- Single script instance (should work as before)
- Two different scripts (ytplay.py and ytfast.py) running simultaneously
- Three or more script instances
- Proper cleanup when scripts are removed
- Thread safety under concurrent access

### 7. Success Criteria
- Multiple scripts can run simultaneously without state contamination
- Each script maintains its own configuration independently
- Logs show correct script names for all instances
- Configuration warnings reflect each script's actual state
- No performance degradation for single-script use
- All existing features continue to work

### 8. Version and Documentation
- Increment version to 3.6.0 in `config.py`
- Update MIGRATION_NOTES.md to explain the fix
- Update PR #23 description with the solution
- Document any new APIs or patterns introduced

## Additional Implementation Notes
- The solution should be elegant and maintainable
- Consider future scalability (what if users want 10+ instances?)
- Maintain the project's coding style and conventions
- Add comprehensive comments explaining the new architecture
- Consider edge cases like script reload, OBS shutdown, etc.

## Deliverables
1. Refactored state.py with instance isolation
2. Updated main script with proper state initialization
3. All dependent modules updated to use new state mechanism
4. Comprehensive testing with multiple instances
5. Updated documentation and version bump to 3.6.0

## Timeline
This phase should be completed as part of the feature/common-modules-redesign branch before merging to main, as the current implementation doesn't truly support multi-instance operation.
