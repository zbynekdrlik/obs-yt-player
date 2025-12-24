# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.2.0] - 2025-12-24

### Added
- Persistent play history tracking across script restarts
- Python 3.13 support in CI/CD pipeline
- Dependabot for automated dependency updates (pip + GitHub Actions)
- Automated GitHub releases on version tags (`v*.*.*`)
- Stricter test coverage thresholds (70% project, 80% patch)
- Comprehensive testing infrastructure with 462 tests
- GitHub Actions CI/CD with multi-platform testing

### Changed
- Branch protection via GitHub Rulesets with required status checks
- Coverage reporting via Codecov
- Wiki disabled (unused feature)
- Auto-delete branches on PR merge enabled

### Fixed
- Play history now persists to `cache/play_history.json`
- Stale entries cleaned when playlist changes between sessions

## [4.1.1] - 2025-12-20

### Fixed
- Pre-loaded video tracking for accurate state handling
- Test coverage improvements

## [4.1.0] - 2025-12-15

### Added
- Unique source names per instance (e.g., `ytplay_video`, `worship_video`)
- Batch script `update_all_instances.bat` for bulk updates

### Changed
- **BREAKING**: Source names now prefixed with instance name
- Improved multi-instance isolation

### Migration
- Rename OBS sources: `video` → `[instance]_video`, `title` → `[instance]_title`

## [4.0.7] - 2025-12-10

### Fixed
- Batch file improvements (no manual import updates needed)
- Validation and naming issues resolved
- All modules verified against main branch

## [4.0.0] - 2025-12-01

### Added
- Folder-based multi-instance architecture
- Dynamic module loading system
- Complete isolation between instances
- `create_new_ytplayer.bat` for instance creation

### Changed
- **BREAKING**: Renamed from `ytfast` to `ytplay`
- New folder structure: `yt-player-[name]/[name].py`

### Migration
- Rename script files and module folders
- Update OBS script references

## [3.4.1] - 2025-11-20

### Changed
- Clarified Gemini API key is optional in documentation
- Improved metadata extraction documentation

## [3.4.0] - 2025-11-15

### Added
- Audio-only mode for bandwidth-conscious users
- Downloads minimal 144p video with 192k audio
- Significantly smaller file sizes

## [3.3.3] - 2025-11-10

### Fixed
- Gemini metadata extraction for pipe-separated titles
- Improved title parsing patterns

## [3.3.2] - 2025-11-05

### Fixed
- Single mode autoplay issue
- Mark current video as first when switching to single mode

## [3.3.1] - 2025-11-01

### Fixed
- Removed debug code and unused variables
- Code cleanup

## [3.2.16] - 2025-10-25

### Added
- Playback behavior settings (Continuous/Single/Loop modes)
- Scene-aware mode switching

## [3.2.0] - 2025-10-15

### Added
- Nested scene playback support
- Automatic detection of nested scenes
- Seamless playback across scene hierarchies

## [3.0.0] - 2025-10-01

### Added
- Gemini-only metadata extraction
- Automatic retry system for failed extractions
- Google Search grounding for improved accuracy

### Changed
- Files marked with `_gf` suffix for Gemini failures
- Automatic retry on script startup

## [2.0.0] - 2025-09-15

### Added
- Loudness normalization to -14 LUFS
- FFmpeg two-pass processing
- Background thread processing

### Changed
- Video cache structure with normalized files

## [1.0.0] - 2025-09-01

### Added
- Initial release
- YouTube playlist synchronization
- OBS Media Source integration
- Basic metadata extraction from titles
- yt-dlp and FFmpeg auto-download

[Unreleased]: https://github.com/zbynekdrlik/obs-yt-player/compare/v4.2.0...HEAD
[4.2.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v4.1.1...v4.2.0
[4.1.1]: https://github.com/zbynekdrlik/obs-yt-player/compare/v4.1.0...v4.1.1
[4.1.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v4.0.7...v4.1.0
[4.0.7]: https://github.com/zbynekdrlik/obs-yt-player/compare/v4.0.0...v4.0.7
[4.0.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.4.1...v4.0.0
[3.4.1]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.4.0...v3.4.1
[3.4.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.3.3...v3.4.0
[3.3.3]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.3.2...v3.3.3
[3.3.2]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.3.1...v3.3.2
[3.3.1]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.2.16...v3.3.1
[3.2.16]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.2.0...v3.2.16
[3.2.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v3.0.0...v3.2.0
[3.0.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/zbynekdrlik/obs-yt-player/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/zbynekdrlik/obs-yt-player/releases/tag/v1.0.0
