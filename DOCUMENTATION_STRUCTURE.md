# OBS YouTube Player Documentation Structure

## Overview
This document explains the relationship between all documentation files.

## Documentation Hierarchy

### Core Documentation (`/docs/`)
1. **01-overview.md** - Project purpose and high-level goals
2. **02-requirements.md** - Authoritative functional specification (includes logging spec)
3. **03-obs_api.md** - OBS-specific constraints and rules
4. **04-guidelines.md** - Coding style, logging guidelines, and development workflow

### Implementation Phases (`/phases/`)

#### Foundation Phases
1. **Phase-01-Scaffolding.md** - Basic script structure
2. **Phase-02-Dependency-Setup.md** - Tool download system (yt-dlp, FFmpeg, fpcalc)
3. **Phase-03-Playlist-Sync.md** - YouTube playlist synchronization

#### Processing Pipeline Phases
4. **Phase-04-Video-Download.md** - Download videos with yt-dlp
5. **Phase-05-AcoustID-Metadata.md** - AcoustID fingerprinting
6. **Phase-06-iTunes-Metadata.md** - iTunes metadata as secondary source
7. **Phase-07-Title-Parser-Fallback.md** - Smart YouTube title parsing
8. **Phase-08-Audio-Normalization.md** - FFmpeg loudness normalization

#### Playback & Control Phases
9. **Phase-09-Playback-Control.md** - Random playback and media control
10. **Phase-10-Scene-Management.md** - Scene transition handling
11. **Phase-11-Final-Polish.md** - Integration testing and optimization

## Development Workflow

### For Each Phase:
1. **Read Requirements**: Check relevant sections in `02-requirements.md`
2. **Review Constraints**: Ensure compliance with `03-obs_api.md`
3. **Follow Guidelines**: Apply rules from `04-guidelines.md`
4. **Update Version**: Increment `SCRIPT_VERSION` according to changes
5. **Implement**: Output code in Markdown block
6. **Test**: Follow testing steps in each phase
7. **Commit**: Only after successful testing

### Logging System
The script uses a simplified, thread-aware logging system:
- Format: `[timestamp] message` or `[timestamp] [script_name] message`
- Single `log(message)` function with thread detection
- No debug levels or configuration
- See `04-guidelines.md` for implementation details

### Version Management
- Each code output must increment the script version
- PATCH: Bug fixes, minor changes
- MINOR: New features (most phases)
- MAJOR: Breaking changes

### Cross-References
- Every phase references the requirements it implements
- All phases include testing sections
- Code must respect OBS API constraints
- Output follows guidelines exactly

## Key Rules
1. Single Python file output (`ytfast.py`)
2. All heavy work in background threads
3. OBS API calls only on main thread
4. Increment version with every code output
5. Test before commit
6. Follow PEP-8 style
7. Use simplified, thread-aware logging

## Phase Dependencies
- Phase 1-3: Foundation (can run but no videos)
- Phase 4: Adds downloading capability
- Phase 5: Adds AcoustID metadata extraction
- Phase 6: Adds iTunes metadata search
- Phase 7: Adds smart title parsing fallback
- Phase 8: Adds audio normalization
- Phase 9: Adds playback functionality
- Phase 10: Adds scene transition handling
- Phase 11: Final polish and optimization

Each phase builds on previous phases, creating a complete system.

## Current Implementation Status
As of version 1.3.6:
- ✅ Phase 1: Scaffolding complete
- ✅ Phase 2: Tool management complete
- ✅ Phase 3: Playlist sync complete
- ✅ Phase 4: Video download (partial - downloads to temp files)
- ⏳ Phase 5-11: To be implemented

The logging system has been simplified and made thread-aware for multi-instance support.
