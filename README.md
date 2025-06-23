# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them randomly via Media Source with metadata display. Features AI-powered metadata extraction using Google Gemini.

## Features

- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists (on startup and manual trigger only)
- **Local Caching**: Downloads and stores videos locally for reliable playback
- **Audio Normalization**: Normalizes audio to -14 LUFS using FFmpeg
- **Random Playback**: Plays videos randomly without repeats
- **AI-Powered Metadata**: Google Gemini AI extracts accurate artist/song information
- **Smart Fallback**: Title parser handles cases when Gemini is unavailable
- **Background Processing**: All heavy tasks run in separate threads
- **OBS Integration**: Seamless integration with OBS Studio scenes and sources
- **Multi-Instance Support**: Rename script to run multiple instances with separate caches
- **Modular Architecture**: Clean, maintainable code structure with separated concerns
- **Scene Management**: Automatic start/stop based on scene activation
- **Transition Support**: Proper handling of scene transitions with configurable delays
- **File-Based Logging**: Comprehensive logging to both OBS console and individual log files
- **Automatic Retry**: Failed Gemini extractions are retried on next startup

## Requirements

- **Windows Operating System** (Windows 10/11 recommended)
- OBS Studio with Python scripting support
- Internet connection for initial video downloads
- Sufficient disk space for video cache
- Google Gemini API key (required for metadata extraction)

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
   - **Google Gemini API key** (get free key at https://makersuite.google.com/app/apikey)

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

## Metadata Extraction System

The script uses a streamlined metadata extraction system:

### Google Gemini AI (Primary)
- Uses Gemini 2.5 Flash with Google Search grounding
- Intelligently extracts artist and song from video context
- Handles complex title patterns:
  - "Song | Artist" format
  - Multiple pipe separators
  - Various YouTube title conventions
- Most accurate for worship/church music and international content
- **Free tier available** with generous limits

### Smart Title Parser (Fallback)
- Activates when Gemini is unavailable or fails
- Handles common patterns:
  - "Artist - Song"
  - "Song | Artist"
- Conservative fallback ensures videos always play

### Automatic Retry System
- Videos that fail Gemini extraction are marked with `_gf` in filename
- Automatically retried on next OBS startup
- Successfully extracted metadata results in file rename
- Ensures maximum metadata accuracy over time

### Universal Song Cleaning
All metadata sources apply cleaning to remove:
- (Official Video), [Live], (feat. Artist)
- (Official Audio), (Lyric Video)
- And many more annotations...

## Logging System

The script includes a comprehensive logging system:

### Log Files
- Located in `{cache_dir}/logs/` directory
- One log file per OBS session with timestamp-based naming
- Example: `ytfast_20250623_183209.log`
- Includes thread information for debugging
- Automatically cleaned up when script unloads

### Log Format
- Console logs: Standard OBS format with timestamps
- File logs: Enhanced format with thread identification
- Session headers and footers for easy navigation

## Scene Transitions

The script properly handles OBS scene transitions:
- **Transitioning TO the scene**: Video starts playing immediately
- **Transitioning FROM the scene**: Video continues until transition completes
- Works with any transition duration
- Supports both regular mode and Studio Mode

## Multi-Instance Setup

Run multiple instances by copying and renaming the script:

```
obs-scripts/
├── ytfast.py              → Scene: ytfast
├── ytfast_modules/        → Modules for ytfast.py
├── music-chill.py         → Scene: music-chill
├── music-chill_modules/   → Modules for music-chill.py
└── stream-bgm.py          → Scene: stream-bgm
└── stream-bgm_modules/    → Modules for stream-bgm.py
```

Each instance maintains its own playlist, cache, settings, and modules.

## Windows-Specific Features

The script is optimized for Windows with:
- Hidden console windows for background processes
- Automatic download of Windows binaries (yt-dlp.exe, ffmpeg.exe)
- Windows-compatible file path handling
- Native Windows subprocess management

## Project Structure

```
ytfast.py                    # Main entry point (minimal OBS interface)
ytfast_modules/
    __init__.py             # Package marker
    config.py               # Configuration constants
    logger.py               # Thread-aware logging with file output
    state.py                # Thread-safe global state
    utils.py                # Utility functions
    tools.py                # Tool download/management
    cache.py                # Cache scanning/cleanup
    playlist.py             # Playlist synchronization
    download.py             # Video downloading
    metadata.py             # Metadata extraction orchestration
    gemini_metadata.py      # Google Gemini AI integration
    normalize.py            # Audio normalization
    playback.py             # Playback control
    scene.py                # Scene management
    reprocess.py            # Gemini retry system
```

## Current Status

Version 3.0.12 - Gemini-Only Metadata:
- ✅ Complete foundation, processing, and playback system
- ✅ Google Gemini AI as primary metadata source
- ✅ Smart title parser as fallback
- ✅ Automatic retry for failed Gemini extractions
- ✅ File-based logging system
- ✅ Scene transition support
- ✅ Multi-instance capability
- ✅ Windows-optimized implementation

## Recent Updates

### v3.0.12 - Gemini-Only Metadata Branch
- Removed AcoustID and iTunes metadata sources
- Gemini AI is now the sole metadata extraction method
- Smart title parser provides fallback when Gemini fails
- Automatic retry system for failed extractions
- Simplified metadata pipeline for better reliability
- Files marked with `_gf` for Gemini failures
- Enhanced Google Search grounding in Gemini prompts

## Getting a Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in OBS script settings
5. Free tier includes generous limits for personal use

## Troubleshooting

### Gemini Metadata Failures
- Check your internet connection
- Verify API key is correct
- Failed extractions will retry automatically on restart
- Check logs in `{cache_dir}/logs/` for details

### No Videos Playing
- Ensure scene and source names match exactly
- Check that playlist URL is valid
- Verify cache directory has write permissions
- Review logs for download errors

## License

MIT License - see LICENSE file for details.