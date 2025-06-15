# Repository Restructuring Plan

## Current Issues
1. Phase 4 combines too many features (download, metadata, normalization)
2. Phase names in README don't match actual phase files
3. AcoustID implementation is Phase 9 but should come before normalization
4. Documentation cross-references are inconsistent

## Proposed New Phase Structure

### Foundation Phases
1. **Phase 01 - Scaffolding**: Basic script structure and OBS integration
2. **Phase 02 - Tool Management**: Download and verify yt-dlp, FFmpeg, fpcalc
3. **Phase 03 - Playlist Sync**: Fetch playlist, queue videos, manage cache

### Processing Pipeline Phases
4. **Phase 04 - Video Download**: Download videos with yt-dlp
5. **Phase 05 - Metadata Extraction**: AcoustID fingerprinting + YouTube title fallback
6. **Phase 06 - Audio Normalization**: FFmpeg loudnorm to -14 LUFS

### Playback Phases
7. **Phase 07 - Playback Control**: Random playback, media source control
8. **Phase 08 - Scene Management**: Handle scene transitions, stop on exit

### Finalization
9. **Phase 09 - Final Polish**: Testing, optimization, documentation

## Files to Update
1. All phase files (rename and restructure)
2. README.md (correct phase list)
3. DOCUMENTATION_STRUCTURE.md (update phase names)
4. Cross-references in all documentation

## Implementation Order
1. Create this plan
2. Rename/restructure phase files
3. Update content of each phase
4. Update README and docs
5. Verify all cross-references