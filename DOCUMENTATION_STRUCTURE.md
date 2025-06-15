# OBS YouTube Player Documentation Structure

## Overview
This document explains the relationship between all documentation files.

## Documentation Hierarchy

### Core Documentation (`/docs/`)
1. **01-overview.md** - Project purpose and high-level goals
2. **02-requirements.md** - Authoritative functional specification
3. **03-obs_api.md** - OBS-specific constraints and rules
4. **04-guidelines.md** - Coding style and development workflow

### Implementation Phases (`/phases/`)

#### Foundation Phases
1. **Phase-01-Scaffolding.md** - Basic script structure
2. **Phase-02-Dependency-Setup.md** - Tool download system (yt-dlp, FFmpeg, fpcalc)
3. **Phase-03-Playlist-Sync.md** - YouTube playlist synchronization

#### Processing Pipeline Phases
4. **Phase-04-Video-Download.md** - Download videos with yt-dlp
5. **Phase-05-Metadata-Extraction.md** - AcoustID fingerprinting + fallback
6. **Phase-06-Audio-Normalization.md** - FFmpeg loudness normalization

#### Playback & Control Phases
7. **Phase-07-Playback-Control.md** - Random playback and media control
8. **Phase-08-Scene-Management.md** - Scene transition handling
9. **Phase-09-Final-Polish.md** - Integration testing and optimization

### Legacy/Deprecated Phases
- **Phase-04-Serial-Processing.md** - Split into phases 4, 5, 6
- **Phase-05-Audio-Normalization.md** (old) - Now Phase 06
- **Phase-06-Playback-Control.md** (old) - Now Phase 07
- **Phase-07-Stop-Playback.md** - Merged into Phase 08
- **Phase-08-Final-Review.md** - Now Phase 09
- **Phase-09-AcoustID-Metadata.md** - Merged into Phase 05

## Development Workflow

### For Each Phase:
1. **Read Requirements**: Check relevant sections in `02-requirements.md`
2. **Review Constraints**: Ensure compliance with `03-obs_api.md`
3. **Follow Guidelines**: Apply rules from `04-guidelines.md`
4. **Update Version**: Increment `SCRIPT_VERSION` according to changes
5. **Implement**: Output code in Markdown block
6. **Test**: Follow testing steps in each phase
7. **Commit**: Only after successful testing

### Version Management
- Each phase implementation should increment the script version
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
4. Increment version with each phase
5. Test before commit
6. Follow PEP-8 style

## Phase Dependencies
- Phase 1-3: Foundation (can run but no videos)
- Phase 4: Adds downloading capability
- Phase 5: Adds metadata extraction
- Phase 6: Adds audio normalization
- Phase 7: Adds playback functionality
- Phase 8: Adds scene transition handling
- Phase 9: Final polish and optimization

Each phase builds on previous phases, creating a complete system.