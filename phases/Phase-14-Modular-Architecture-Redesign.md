# Phase 14: Modular Architecture Redesign

## ⚠️ CRITICAL IMPLEMENTATION NOTE ⚠️

**This phase MUST be implemented ON TOP OF the existing main branch functionality, NOT as a replacement.**

All existing features from the main branch (v3.4.x) must be preserved:
- Full video downloading with yt-dlp
- Gemini AI metadata extraction with fallback parsing
- Audio normalization to -14 LUFS
- Complete playback control (continuous, single, loop modes)
- Title display with opacity animation
- Audio-only mode support
- All error handling and edge cases

The goal is to REFACTOR the existing code into a modular architecture while maintaining 100% feature parity.

## Version Target: 4.0.0

## Overview
This phase aims to solve the recurring issues with multi-instance support by implementing a cleaner, more maintainable shared modules architecture. The key insight is to minimize the main script file and maximize the use of shared, well-isolated modules.

**Implementation Approach**: Take the existing ytfast.py and its modules from main branch and refactor them into the new architecture, preserving ALL functionality.

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
5. **100% Feature Parity**: All functionality from main branch must work identically

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
    ├── logger.py          # Thread-aware logging
    ├── tools.py           # yt-dlp and ffmpeg management
    ├── playlist.py        # YouTube playlist sync
    ├── download.py        # Video downloading with progress
    ├── metadata.py        # Gemini AI + fallback parsing
    ├── normalize.py       # Audio normalization (-14 LUFS)
    ├── playback.py        # Full playback control
    ├── scene.py           # OBS scene management
    ├── cache.py           # Cache registry and management
    ├── utils.py           # Utility functions
    └── reprocess.py       # Background reprocessing
```

### Migration Strategy from Main Branch

Each module in the new architecture should contain the FULL functionality from the corresponding main branch modules:

1. **download.py** - Must include:
   - Complete yt-dlp integration
   - Progress tracking with 50% milestone logging
   - Audio-only mode support
   - Windows subprocess handling
   - Error handling and timeouts

2. **playback.py** - Must include:
   - Full playback controller functionality
   - All sub-modules (media_control, opacity_control, title_manager, etc.)
   - Playback modes (continuous, single, loop)
   - State management for playing/paused/ended
   - Title animation with opacity filters

3. **metadata.py** - Must include:
   - Gemini API integration
   - Fallback title parsing
   - Metadata caching
   - Error handling and retry logic

4. **normalize.py** - Must include:
   - FFmpeg integration
   - -14 LUFS target processing
   - File management
   - Error handling

5. **All other modules** - Complete functionality, not placeholders

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

##### Feature Modules (With Full Functionality)
- All modules must contain complete implementations
- No placeholders or stubs
- Full error handling and edge cases
- Maintain exact behavior from main branch

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

### Phase 2: Migrate Existing Functionality
1. Copy ALL code from main branch ytfast_modules/
2. Refactor for state isolation (add script_path context)
3. Ensure ALL features work identically
4. No functionality should be lost or simplified

### Phase 3: State Management Refactor
1. Implement proper state isolation
2. Use script path as unique key
3. Add context propagation for threads
4. Ensure complete cleanup on unload

### Phase 4: Testing and Validation
1. Test single instance - must work exactly like main branch
2. Test with 3+ simultaneous scripts
3. Verify no state contamination
4. Test all features: download, metadata, normalize, playback
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

## Testing Checklist

Before Phase 14 is considered complete, ALL of these must work:

- [ ] Video downloading with yt-dlp
- [ ] Progress tracking (50% milestone)
- [ ] Audio-only mode
- [ ] Gemini metadata extraction
- [ ] Fallback title parsing
- [ ] Audio normalization to -14 LUFS
- [ ] Continuous playback mode
- [ ] Single playback mode
- [ ] Loop playback mode
- [ ] Title display with opacity fade
- [ ] Scene and source verification
- [ ] Cache management
- [ ] Tool downloading (yt-dlp, ffmpeg)
- [ ] Error handling for all edge cases
- [ ] Multi-instance support without conflicts
- [ ] Clean shutdown without errors

## Success Criteria

1. Main script size: <5KB (from 16KB+)
2. Zero cross-contamination between instances
3. **100% feature parity with main branch**
4. All existing functionality works identically
5. Clean thread shutdown without errors
6. Each script maintains independent:
   - Configuration
   - State
   - Warnings
   - Cache
   - Logs
7. Improved user experience with clear configuration feedback

## Risk Mitigation

1. **Feature Loss**: Test extensively against main branch
2. **Import Errors**: Comprehensive error handling in main script
3. **State Leaks**: Strict isolation enforcement
4. **Thread Issues**: Proper context management
5. **Module Dependencies**: Clear dependency graph
6. **Backwards Compatibility**: Provide ytfast.py copy for existing users

## Next Steps

1. Start with main branch as the base
2. Create ultra-minimal main script
3. Migrate ALL functionality from ytfast_modules/ to ytplay_modules/
4. Add state isolation without changing behavior
5. Test extensively to ensure feature parity
6. Document any behavioral differences (there should be none)
7. Prepare backward compatibility layer (ytfast.py)