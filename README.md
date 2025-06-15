# OBS YouTube Player

An OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them randomly via Media Source with metadata display. All processing runs in background threads to keep OBS responsive.

## Features

- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists (on startup and manual trigger only)
- **Local Caching**: Downloads and stores videos locally for reliable playback
- **Audio Normalization**: Normalizes audio to -14 LUFS using FFmpeg
- **Random Playback**: Plays videos randomly without repeats
- **Metadata Display**: Shows song and artist information via Text Source
- **Background Processing**: All heavy tasks run in separate threads
- **OBS Integration**: Seamless integration with OBS Studio scenes and sources
- **Multi-Instance Support**: Rename script to run multiple instances with separate caches

## Requirements

- OBS Studio with Python scripting support
- Internet connection for initial video downloads
- Sufficient disk space for video cache

## Installation

1. Download `ytfast.py` from the releases
2. (Optional) Rename the script for multiple instances (e.g., `music1.py`, `bgm-stream.py`)
3. In OBS Studio, go to Tools → Scripts
4. Click the "+" button and select your script
5. Configure the script properties:
   - Set your YouTube playlist URL
   - Cache directory (defaults to `<script_location>/<scriptname>-cache/`)
   - Enable debug logging if needed

## Usage

1. Create a scene with the same name as your script (without .py extension)
   - For `ytfast.py` → create scene named `ytfast`
   - For `music-player.py` → create scene named `music-player`
2. Add a Media Source named `video` to the scene
3. Add a Text Source named `title` for metadata display
4. The script will sync playlist once on startup
5. Click "Sync Playlist Now" to manually update the playlist
6. Switch to your scene to begin random playback

## Multi-Instance Setup

You can run multiple instances by copying and renaming the script:

```
obs-scripts/
├── ytfast.py          → Scene: ytfast, Cache: ./ytfast-cache/
├── music-chill.py     → Scene: music-chill, Cache: ./music-chill-cache/
└── stream-bgm.py      → Scene: stream-bgm, Cache: ./stream-bgm-cache/
```

Each instance maintains its own playlist, cache, and settings.

## Project Structure

This project follows a phased development approach. See the `docs/` directory for detailed implementation specifications and the `phases/` directory for step-by-step development guides.

## Development Phases

The project is organized into logical implementation phases:

### Foundation
1. **Phase 01**: Scaffolding - Basic script structure and OBS integration
2. **Phase 02**: Tool Management - Download and verify yt-dlp, FFmpeg, fpcalc
3. **Phase 03**: Playlist Sync - Fetch playlist, queue videos, manage cache

### Processing Pipeline
4. **Phase 04**: Video Download - Download videos with yt-dlp
5. **Phase 05**: Metadata Extraction - AcoustID fingerprinting + YouTube title fallback
6. **Phase 06**: Audio Normalization - FFmpeg loudnorm to -14 LUFS

### Playback & Control
7. **Phase 07**: Playback Control - Random playback, media source control
8. **Phase 08**: Scene Management - Handle scene transitions, stop on exit
9. **Phase 09**: Final Polish - Testing, optimization, documentation

Each phase builds upon the previous one, ensuring a systematic and maintainable development process.

## License

MIT License - see LICENSE file for details.