# OBS YouTube Player Documentation Structure

## Overview
This document explains the relationship between all documentation files and the new modular code structure.

## Code Architecture (v3.0+)

### Main Script
- **ytfast.py** - Minimal main script containing only OBS interface functions

### Module Structure (`ytfast_modules/`)
- **__init__.py** - Package marker
- **config.py** - All configuration constants and settings
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
- **scene.py** - Scene management and OBS event handling
- **reprocess.py** - Automatic retry system for failed Gemini extractions

### Multi-Instance Support
When the script is renamed (e.g., `music.py`), the module folder automatically becomes `music_modules/`. This allows multiple independent instances with separate:
- Module folders
- Cache directories
- Settings
- Playlists

## Documentation Hierarchy

### Core Documentation (`/docs/`)
1. **01-overview.md** - Project purpose and high-level goals
2. **02-requirements.md** - Authoritative functional specification
3. **03-obs_api.md** - OBS-specific constraints and rules
4. **04-guidelines.md** - Coding style, logging guidelines, and development workflow

### Implementation Phases (`/phases/`)

#### Foundation Phases
1. **Phase-01-Scaffolding.md** - Basic script structure
2. **Phase-02-Dependency-Setup.md** - Tool download system (yt-dlp, FFmpeg)
3. **Phase-03-Playlist-Sync.md** - Cache-aware playlist synchronization with cleanup

#### Processing Pipeline Phases
4. **Phase-04-Video-Download.md** - Download videos with yt-dlp
5. **Phase-05-AcoustID-Metadata.md** - *(NOT IMPLEMENTED - Removed in v3.0)*
6. **Phase-06-iTunes-Metadata.md** - *(NOT IMPLEMENTED - Removed in v3.0)*
7. **Phase-07-Title-Parser-Fallback.md** - Smart YouTube title parsing (now primary fallback)
8. **Phase-08-Universal-Metadata-Cleaning.md** - Universal song title cleaning for all sources
9. **Phase-09-Audio-Normalization.md** - FFmpeg loudness normalization to -14 LUFS

#### Playback & Control Phases
10. **Phase-10-Playback-Control.md** - Random playback and media control
11. **Phase-11-Scene-Management.md** - Scene transition handling
12. **Phase-12-Simple-Polish.md** - Integration testing and optimization

#### Enhanced Features
13. **Phase-13-Gemini-Metadata.md** - Google Gemini AI as primary metadata source
14. **Phase-14-File-Based-Logging.md** - Comprehensive logging to files

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

### Metadata System (v3.0+)
The script uses a simplified metadata extraction system:
1. **Google Gemini AI** (Primary - Required)
   - Uses Gemini 2.5 Flash with Google Search grounding
   - Handles complex title patterns intelligently
   - Failed extractions marked with `_gf` suffix
2. **Smart Title Parser** (Fallback)
   - Activates when Gemini fails or is unavailable
   - Handles common YouTube title formats
3. **Automatic Retry**
   - Videos with `_gf` marker are retried on startup
   - Successful extraction results in file rename

### Version Management
- Version constant in `config.py`
- Current version: 3.0.12
- Each code change increments the version
- **MAJOR**: Significant changes (e.g., v3.0 for Gemini-only)
- **MINOR**: New features, phase implementations
- **PATCH**: Bug fixes, minor changes

### Cross-References
- Every phase references the requirements it implements
- All phases include testing sections
- Code must respect OBS API constraints
- Modules reference each other as needed

## Key Rules
1. Main script (`ytfast.py`) contains minimal code
2. All functionality in modules under `<scriptname>_modules/`
3. All heavy work in background threads
4. OBS API calls only on main thread
5. Increment version with every code output
6. Test before commit
7. Follow PEP-8 style
8. Use thread-aware logging

## Current Implementation Status (v3.0.12)
The implementation includes:
- ✅ Phase 1-4: Foundation and video downloading
- ❌ Phase 5-6: AcoustID and iTunes (removed in v3.0)
- ✅ Phase 7: Title parser (now primary fallback)
- ✅ Phase 8-11: Universal cleaning, normalization, playback, scene management
- ✅ Phase 13: Gemini metadata (now primary source)
- ✅ Phase 14: File-based logging
- ✅ Automatic retry system for failed Gemini extractions
- ✅ Simplified metadata pipeline with single primary source

All videos are processed through: download → Gemini/parser → universal cleaning → normalization → playback.