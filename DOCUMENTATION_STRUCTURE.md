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
1. **Phase-01-Scaffolding.md** - Basic script structure
2. **Phase-02-Dependency-Setup.md** - Tool download system
3. **Phase-03-Playlist-Sync.md** - YouTube playlist synchronization
4. **Phase-04-Serial-Processing.md** - Video processing pipeline
5. **Phase-05-Audio-Normalization.md** - FFmpeg loudness normalization
6. **Phase-06-Playback-Control.md** - OBS scene integration
7. **Phase-07-Stop-Playback.md** - Scene transition handling
8. **Phase-08-Final-Review.md** - Integration and polish

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