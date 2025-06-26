# Phase 14: Modular Architecture Redesign

## Version Target: 4.0.0

## Overview
This phase aims to solve the recurring issues with multi-instance support by implementing a cleaner, more maintainable shared modules architecture. The key insight is to minimize the main script file and maximize the use of shared, well-isolated modules.

## Important Migration Notes

### Script Naming Convention Change
- **Current (main branch)**: Default script is `ytfast.py` with `ytfast_modules/`
- **New (v4.0.0)**: Default script will be `ytplay.py` with shared `ytplay_modules/`
- **Rationale**: More generic name that better represents the player functionality

### Configuration Improvements (from feature/common-modules-redesign)
- **Playlist URL**: No default URL - users must configure their own playlist
- **UI Enhancements**: 
  - Configuration warnings at bottom of settings
  - Better organized property layout
  - Clear visual feedback for missing configuration
  - Improved user experience overall

## Goals

### Primary Goals
1. **True Shared Modules**: All scripts share a single `ytplay_modules/` directory
2. **Complete Instance Isolation**: Each script instance maintains its own state without cross-contamination
3. **Minimal Main Script**: Keep ytplay.py as thin as possible (target: <5KB)
4. **Zero-Copy Architecture**: Eliminate the need to copy scripts - just rename and use

### Secondary Goals
1. **Simplified State Management**: Clean, dictionary-based state isolation
2. **Thread Safety**: Proper context management for background threads
3. **Configuration Warnings**: Per-script warning system without interference
4. **Dynamic Scene Detection**: Automatic scene name based on script filename
5. **User-Friendly Configuration**: Incorporate UI improvements from feature/common-modules-redesign

## Problems to Solve

### 1. State Cross-Contamination (Current Issues)
- **Problem**: Scripts share state, causing warnings and settings to leak between instances
- **Root Cause**: Global state management not properly isolated per script
- **Solution**: Complete state isolation using script path as unique key

### 2. Module Update Propagation
- **Problem**: When ytplay.py is copied to ytfast.py, updates to modules don't propagate
- **Root Cause**: Each script has its own module directory
- **Solution**: Shared `ytplay_modules/` directory for all scripts

### 3. Complex Main Script
- **Problem**: Main script is too large (16KB+), making it hard to maintain multiple copies
- **Root Cause**: Too much logic in the main script instead of modules
- **Solution**: Move ALL logic to modules, keep main script minimal

### 4. Default Configuration Issues
- **Problem**: Hardcoded playlist URL in main branch confuses users
- **Root Cause**: Legacy default configuration
- **Solution**: Empty defaults, clear warnings when not configured

## Proposed Architecture

### Directory Structure
```
obs-scripts/
├── ytplay.py              # NEW: Minimal main script (~5KB) - replaces ytfast.py
├── ytfast.py              # Just a copy of ytplay.py (for backward compatibility)
├── yt_worship.py          # Another copy for different use case
└── ytplay_modules/        # NEW: SHARED by all scripts (replaces individual *_modules/)
    ├── __init__.py
    ├── config.py          # Version and constants (no default playlist URL)
    ├── state.py           # State isolation manager
    ├── main.py            # Main entry points
    ├── ui.py              # UI property definitions with warnings
    └── [other modules]    # All other functionality
```

### Key Design Principles

#### 1. Ultra-Minimal Main Script
```python
# ytplay.py - Target size: <5KB (replaces 16KB+ ytfast.py)
import obspython as obs
import os
import sys

SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]

# Add modules path - always 'ytplay_modules' regardless of script name
sys.path.insert(0, os.path.join(os.path.dirname(SCRIPT_PATH), 'ytplay_modules'))

# Import main module
try:
    from main import (
        script_description, script_load, script_unload,
        script_properties, script_defaults, script_update,
        script_save, sync_now_callback
    )
    
    # Pass script context to all functions
    def wrapped_script_load(settings):
        script_load(settings, SCRIPT_PATH)
    
    # ... wrap other functions similarly
    
except ImportError as e:
    def script_description():
        return f"Error loading modules: {e}"
```

#### 2. State Isolation Strategy
- Use a dictionary with script path as key
- Each script gets its own isolated state container
- Thread-local storage for context propagation
- Cleanup on script unload

#### 3. Module Organization

##### Core Modules (Always Loaded)
- `config.py` - Constants and version (DEFAULT_PLAYLIST_URL = "")
- `state.py` - State isolation manager
- `logger.py` - Script-aware logging
- `main.py` - Entry point orchestration
- `ui.py` - Property definitions with warning system

##### Feature Modules (Lazy Loaded)
- Group by functionality
- Load only when needed
- Clear interfaces between modules

#### 4. Instance Detection
- Use script filename for scene name (ytplay → scene "ytplay")
- Use script path as unique identifier
- Automatic cache directory creation
- No hardcoded names

#### 5. Configuration Enhancements
- Configuration warnings displayed at bottom of settings
- Warnings for: Missing scene, Missing sources, No playlist URL, Tools not ready
- Clean, user-friendly interface
- No confusing default values

## Implementation Phases

### Phase 1: Create Ultra-Minimal Main Script
1. Extract ALL logic to modules
2. Main script only handles:
   - Path setup
   - Module import
   - Function wrapping with context
3. Target: <5KB file size

### Phase 2: Refactor State Management
1. Implement proper state isolation
2. Use script path as unique key
3. Add context propagation for threads
4. Ensure complete cleanup on unload

### Phase 3: Module Consolidation
1. Combine related small modules
2. Create clear module boundaries
3. Minimize inter-module dependencies
4. Use dependency injection where needed

### Phase 4: UI and Configuration Migration
1. Port UI improvements from feature/common-modules-redesign
2. Implement warning system
3. Remove all default configuration values
4. Enhance user experience

### Phase 5: Testing and Validation
1. Test with 3+ simultaneous scripts
2. Verify no state contamination
3. Test script add/remove scenarios
4. Validate thread cleanup
5. Ensure backward compatibility

## Migration Path for Users

### From main branch (ytfast.py):
1. **Option A - Automatic**:
   - We provide `ytfast.py` as a copy of `ytplay.py`
   - User's existing setup continues working
   - They benefit from shared modules immediately
   
2. **Option B - Clean migration**:
   - User renames their OBS scene from "ytfast" to "ytplay"
   - Uses the new `ytplay.py` script
   - Cleaner setup going forward

### From feature/common-modules-redesign:
- Direct upgrade path since naming is already aligned
- All UI improvements preserved
- State isolation issues finally resolved

## Module Design Guidelines

### 1. State Access
```python
# Always get state through context
from state import get_state

def some_function():
    state = get_state()  # Automatically uses correct script context
    return state.get('some_value')
```

### 2. Thread Safety
```python
# Set context at thread start
def background_thread(script_path):
    set_thread_script_context(script_path)
    # Now all state access uses correct context
```

### 3. Module Interfaces
```python
# Clear, minimal interfaces
class ModuleInterface:
    def initialize(self, script_path): pass
    def cleanup(self): pass
    def get_properties(self): pass
```

## Benefits of This Approach

1. **Maintainability**: Update modules once, all scripts benefit
2. **Simplicity**: Trivial to create new instances (just copy 5KB file)
3. **Isolation**: Complete separation between instances
4. **Flexibility**: Easy to add/remove features via modules
5. **Performance**: Shared modules reduce memory usage
6. **User Experience**: Clear configuration with helpful warnings

## Success Criteria

1. Main script size: <5KB (from 16KB+)
2. Zero cross-contamination between instances
3. Updates to modules immediately available to all scripts
4. Clean thread shutdown without errors
5. Each script maintains independent:
   - Configuration
   - State
   - Warnings
   - Cache
   - Logs
6. Improved user experience with clear configuration feedback

## Risk Mitigation

1. **Import Errors**: Comprehensive error handling in main script
2. **State Leaks**: Strict isolation enforcement
3. **Thread Issues**: Proper context management
4. **Module Dependencies**: Clear dependency graph
5. **Backwards Compatibility**: Provide ytfast.py copy for existing users
6. **User Confusion**: Clear migration documentation

## Next Steps

1. Create proof-of-concept ultra-minimal main script
2. Test state isolation with 3 instances
3. Port UI improvements from feature/common-modules-redesign
4. Gradually migrate functionality to shared modules
5. Extensive testing with multiple scenarios
6. Document migration process for users
7. Prepare backward compatibility layer (ytfast.py)