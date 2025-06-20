# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them randomly via Media Source with metadata display. All processing runs in background threads to keep OBS responsive.

## Features

- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists (on startup and manual trigger only)
- **Local Caching**: Downloads and stores videos locally for reliable playback
- **Audio Normalization**: Normalizes audio to -14 LUFS using FFmpeg
- **Random Playback**: Plays videos randomly without repeats
- **Metadata Display**: Shows song and artist information via Text Source
- **Background Processing**: All heavy tasks run in separate threads
- **OBS Integration**: Seamless integration with OBS Studio scenes and sources
- **Multi-Instance Support**: Rename script to run multiple instances with separate caches
- **Modular Architecture**: Clean, maintainable code structure with separated concerns
- **Scene Management**: Automatic start/stop based on scene activation
- **Transition Support**: Proper handling of scene transitions with configurable delays
- **Google Gemini AI Integration**: Optional AI-powered metadata extraction for accurate artist/song identification

## Requirements

- **Windows Operating System** (Windows 10/11 recommended)
- OBS Studio with Python scripting support
- Internet connection for initial video downloads
- Sufficient disk space for video cache
- (Optional) Google Gemini API key for enhanced metadata extraction

## Installation

1. Download the latest release (includes `ytfast.py` and `ytfast_modules/` folder)
2. Copy both the script and modules folder to your OBS scripts directory
3. (Optional) Rename the script for multiple instances (e.g., `music1.py`, `bgm-stream.py`)
   - The modules folder will be automatically named to match (e.g., `music1_modules/`)
4. In OBS Studio, go to Tools → Scripts
5. Click the "+" button and select your script
6. Configure the script properties:
   - Set your YouTube playlist URL
   - Cache directory (defaults to `<script_location>/<scriptname>-cache/`)
   - (Optional) Google Gemini API key for better metadata extraction

## Usage

1. Create a scene with the same name as your script (without .py extension)
   - For `ytfast.py` → create scene named `ytfast`
   - For `music-player.py` → create scene named `music-player`
2. Add a Media Source named `video` to the scene
3. Add a Text Source named `title` for metadata display
4. The script will sync playlist once on startup
5. Click "Sync Playlist Now" to manually update the playlist
6. Switch to your scene to begin random playback
7. Switch away from scene to automatically stop playback

## Metadata Extraction

The script uses a sophisticated metadata extraction system with multiple fallback sources:

1. **Google Gemini AI** (Primary - Optional)
   - Uses advanced AI to intelligently extract artist and song from video titles
   - Handles complex titles with featuring artists, remixes, and special editions
   - Requires API key (get free key at https://makersuite.google.com/app/apikey)
   - Most accurate for worship/church music and international content

2. **AcoustID** (Secondary)
   - Audio fingerprinting technology
   - Matches against MusicBrainz database
   - Good for commercially released music

3. **iTunes API** (Tertiary)
   - Searches Apple's music catalog
   - Fast and reliable for mainstream music

4. **Smart Title Parser** (Fallback)
   - Intelligent parsing of YouTube video titles
   - Handles common patterns like "Artist - Song" and "Song | Artist"

All sources apply universal song title cleaning to remove annotations like:
- (Official Video), [Live], (feat. Artist)
- (Official Audio), (Lyric Video)
- And many more...

## Scene Transitions

The script properly handles OBS scene transitions:
- **Transitioning TO the scene**: Video starts playing immediately as the transition begins
- **Transitioning FROM the scene**: Video continues playing until the transition completes
- Works with any transition duration (tested up to 5+ seconds)
- Supports both regular mode and Studio Mode (preview/program)

## Multi-Instance Setup

You can run multiple instances by copying and renaming the script:

```
obs-scripts/
├── ytfast.py              → Scene: ytfast, Cache: ./ytfast-cache/
├── ytfast_modules/        → Modules for ytfast.py
├── music-chill.py         → Scene: music-chill, Cache: ./music-chill-cache/
├── music-chill_modules/   → Modules for music-chill.py
└── stream-bgm.py          → Scene: stream-bgm, Cache: ./stream-bgm-cache/
└── stream-bgm_modules/    → Modules for stream-bgm.py
```

Each instance maintains its own playlist, cache, settings, and module folder.

## Windows-Specific Features

The script is optimized for Windows with:
- Hidden console windows for background processes
- Automatic download of Windows binaries (yt-dlp.exe, ffmpeg.exe, fpcalc.exe)
- Windows-compatible file path handling
- Native Windows subprocess management

## Project Structure

### Script Architecture

```
ytfast.py                    # Main entry point (minimal OBS interface)
ytfast_modules/
    __init__.py             # Package marker
    config.py               # Configuration constants
    logger.py               # Thread-aware logging
    state.py                # Thread-safe global state
    utils.py                # Utility functions
    tools.py                # Tool download/management (Windows binaries)
    cache.py                # Cache scanning/cleanup
    playlist.py             # Playlist synchronization
    download.py             # Video downloading
    metadata.py             # Metadata extraction (Gemini, AcoustID, iTunes, parsing)
    gemini_metadata.py      # Google Gemini AI integration
    normalize.py            # Audio normalization
    playback.py             # Playback control
    scene.py                # Scene management and transition handling
```

### Documentation

This project follows a phased development approach. See the `docs/` directory for detailed implementation specifications and the `phases/` directory for step-by-step development guides.

## Development Phases

The project is organized into logical implementation phases:

### Foundation
1. **Phase 01**: Scaffolding - Basic script structure and OBS integration
2. **Phase 02**: Tool Management - Download and verify Windows binaries
3. **Phase 03**: Playlist Sync - Fetch playlist, queue videos, manage cache

### Processing Pipeline
4. **Phase 04**: Video Download - Download videos with yt-dlp
5. **Phase 05**: AcoustID Metadata - Audio fingerprinting for accurate metadata
6. **Phase 06**: iTunes Metadata - Secondary metadata source via iTunes API
7. **Phase 07**: Title Parser Fallback - Smart YouTube title parsing when online sources fail
8. **Phase 08**: Universal Metadata Cleaning - Clean song titles from all sources
9. **Phase 09**: Audio Normalization - FFmpeg loudnorm to -14 LUFS

### Playback & Control
10. **Phase 10**: Playback Control - Random playback, media source control
11. **Phase 11**: Scene Management - Handle scene transitions, cleanup on exit
12. **Phase 12**: Final Polish - Testing, optimization, documentation

### Enhanced Features
13. **Phase 13**: Google Gemini AI Integration - AI-powered metadata extraction

Each phase builds upon the previous one, ensuring a systematic and maintainable development process.

## Current Status

Version 2.5.5 - Google Gemini AI Integration:
- ✅ Phases 1-11: Complete foundation, processing, playback, and scene management
- ✅ Phase 13: Google Gemini AI integration for enhanced metadata extraction
- ✅ Modular code structure with separated concerns
- ✅ Windows-optimized with platform-specific code removed
- ⏳ Phase 12: Final polish and optimization to be implemented

## Recent Updates

### v2.5.5 - Gemini API Endpoint Update
- Updated to use the latest `gemini-2.0-flash` model endpoint
- Fixed 404 errors with deprecated API endpoints

### v2.5.0 - Google Gemini AI Integration
- Added optional Google Gemini AI for intelligent metadata extraction
- Gemini is now the primary metadata source when API key is configured
- Handles complex video titles with high accuracy
- Particularly effective for worship/church music and international content
- Falls back to AcoustID, iTunes, and parsing when Gemini is not available

### v2.3.8 - Stop Button Removed
- Removed manual stop button functionality for cleaner interface
- Playback control is now fully automatic based on scene activation

### v2.3.7 - Transition Support
- Added proper scene transition handling using correct OBS events
- Transition detection with duration-aware delays
- Support for both regular mode and Studio Mode
- Fixed API compatibility issues with non-existent events

## License

MIT License - see LICENSE file for details.
