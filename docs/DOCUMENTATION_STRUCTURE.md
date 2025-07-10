# OBS YouTube Player Documentation Structure

## Overview
This document explains the relationship between all documentation files and the new modular code structure.

## Code Architecture (v4.0+)

### Main Script
- **ytplay.py** - Minimal main script containing only OBS interface functions (template instance)
- Scripts can be renamed for multiple instances (e.g., `worship.py`, `music.py`)

### Module Structure (`{scriptname}_modules/`)
- **__init__.py** - Package marker for Python imports
- **config.py** - All configuration constants with dynamic script detection
- **logger.py** - Thread-aware logging system with file output
- **state.py** - Thread-safe global state management
- **utils.py** - Shared utility functions
- **tools.py** - Tool download and management (yt-dlp, FFmpeg)
- **cache.py** - Cache directory scanning and cleanup
- **playlist.py** - Playlist synchronization logic
- **download.py** - Video downloading and processing pipeline
- **metadata.py** - Metadata extraction orchestration (Gemini + title parser)
- **gemini_metadata.py** - Google Gemini AI integration with Google Search grounding
- **normalize.py** - Audio normalization with FFmpeg
- **playback.py** - Playback control and random selection
- **playback_controller.py** - Advanced playback state management
- **media_control.py** - OBS media source control
- **title_manager.py** - Text source title updates
- **opacity_control.py** - Title fade effects
- **scene.py** - Scene management and OBS event handling
- **reprocess.py** - Automatic retry system for failed Gemini extractions
- **state_handlers.py** - Complex state change handlers
- **video_selector.py** - Random video selection logic

### Multi-Instance Support (v4.0+)
The script uses a **folder-based architecture** with dynamic imports:
- Each instance lives in its own folder (e.g., `yt-player-worship/`)
- Script name determines module folder: `worship.py` → `worship_modules/`
- All imports are relative within modules
- Complete isolation between instances
- Use `create_new_ytplayer.bat` for easy instance creation

### Unique Source Names (v4.1.0+)
To support multiple instances without OBS conflicts:
- Source names are prefixed with instance name
- `ytplay` instance: `ytplay_video` and `ytplay_title`
- `worship` instance: `worship_video` and `worship_title`
- Automatic detection based on script name

## Documentation Hierarchy

### Core Documentation (`/docs/`)
1. **01-overview.md** - Project purpose and high-level goals
2. **02-requirements.md** - Authoritative functional specification
3. **03-obs_api.md** - OBS-specific constraints and rules
4. **04-guidelines.md** - Coding style, logging guidelines, and development workflow
5. **12-playback-modes.md** - Detailed playback mode documentation
6. **FOLDER_BASED_INSTANCES.md** - Multi-instance architecture guide
7. **nested-scene-playback.md** - Nested scene support documentation
8. **nested-scene-update-summary.md** - Technical details of nested scene implementation

### Implementation Phases (`/phases/`)

#### Foundation Phases
1. **Phase-01-Scaffolding.md** - Basic script structure
2. **Phase-02-Dependency-Setup.md** - Tool download system (yt-dlp, FFmpeg)
3. **Phase-03-Playlist-Sync.md** - Cache-aware playlist synchronization with cleanup
4. **Phase-04-Video-Download.md** - Download videos with yt-dlp

#### Metadata & Processing Phases
5. **Phase-05-Gemini-Metadata.md** - Google Gemini AI as primary metadata source
6. **Phase-06-Title-Parser-Fallback.md** - Smart YouTube title parsing (fallback)
7. **Phase-07-Universal-Metadata-Cleaning.md** - Universal song title cleaning
8. **Phase-08-Audio-Normalization.md** - FFmpeg loudness normalization to -14 LUFS

#### Playback & Control Phases
9. **Phase-09-Playback-Control.md** - Random playback and media control
10. **Phase-10-Scene-Management.md** - Scene transition handling
11. **Phase-11-Simple-Polish.md** - Integration testing and optimization
12. **Phase-12-File-Based-Logging.md** - Comprehensive logging to files

## Development Workflow

### For Each Phase:
1. **Read Requirements**: Check relevant sections in `02-requirements.md`
2. **Review Constraints**: Ensure compliance with `03-obs_api.md`
3. **Follow Guidelines**: Apply rules from `04-guidelines.md`
4. **Update Version**: Increment `SCRIPT_VERSION` in `config.py`
5. **Implement**: Update relevant modules
6. **Test**: Follow testing steps in each phase
7. **Commit**: Only after successful testing

### Module Development Guidelines
- Each module has a single responsibility
- All shared state goes through `state.py` with thread-safe accessors
- Configuration constants stay in `config.py`
- All modules use the shared logger from `logger.py`
- Heavy processing happens in background threads
- OBS API calls only on main thread
- All imports within modules are relative (e.g., `from .logger import log`)

### Metadata System (v3.0+)
The script uses a simplified metadata extraction system:
1. **Google Gemini AI** (Primary - Optional)
   - Uses Gemini 1.5 Flash with Google Search grounding
   - Handles complex title patterns intelligently
   - Failed extractions marked with `_gf` suffix
2. **Smart Title Parser** (Fallback - Always Available)
   - Activates when Gemini fails or is not configured
   - Handles common YouTube title formats
3. **Automatic Retry**
   - Videos with `_gf` marker are retried on startup
   - Successful extraction results in file rename

### Version Management
- Version constant in `config.py`
- Current version: 4.1.0 (Unique source names for multi-instance)
- Each code change increments the version
- **MAJOR**: Significant changes (e.g., v4.0 for folder-based architecture)
- **MINOR**: New features, phase implementations
- **PATCH**: Bug fixes, minor changes

### Cross-References
- Every phase references the requirements it implements
- All phases include testing sections
- Code must respect OBS API constraints
- Modules reference each other as needed

## Key Rules
1. Main script (e.g., `ytplay.py`) contains minimal code
2. All functionality in modules under `{scriptname}_modules/`
3. All heavy work in background threads
4. OBS API calls only on main thread
5. Increment version with every code output
6. Test before commit
7. Follow PEP-8 style
8. Use thread-aware logging
9. All module imports are relative
10. Each instance is completely isolated
11. Source names must be unique (v4.1.0+)

## Current Implementation Status (v4.1.0)
The implementation includes:
- ✅ All phases 1-12 complete
- ✅ Folder-based multi-instance architecture
- ✅ Dynamic script name detection
- ✅ Relative imports throughout
- ✅ Complete isolation between instances
- ✅ Batch file for easy instance creation
- ✅ Gemini metadata (optional)
- ✅ Title parser fallback (always available)
- ✅ Automatic retry system for failed Gemini extractions
- ✅ Three playback modes (Continuous, Single, Loop)
- ✅ Audio-only mode option
- ✅ Nested scene support
- ✅ Comprehensive logging system
- ✅ Unique source names for multi-instance support

All videos are processed through: download → Gemini/parser → universal cleaning → normalization → playback.