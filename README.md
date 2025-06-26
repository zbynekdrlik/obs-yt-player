# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🚀 Version 4.0.0 - Modular Architecture

Major architectural redesign for improved multi-instance support and maintainability:
- **Ultra-minimal main script**: Only 2.7KB (was 16KB+)
- **Shared modules architecture**: All scripts use `ytplay_modules/`
- **Complete state isolation**: Run unlimited instances without conflicts
- **Backward compatibility**: Existing `ytfast.py` setups continue working

## Key Features

### 🎬 Playback Modes
- **Continuous Mode** (default): Plays all videos randomly forever
- **Single Mode**: Plays one video then stops
- **Loop Mode**: Repeats the same video continuously

### 🎯 Core Functionality
- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists (on startup and manual trigger)
- **Local Caching**: Downloads and stores videos locally for reliable offline playback
- **Audio Normalization**: Normalizes all audio to -14 LUFS using FFmpeg for consistent volume
- **AI-Powered Metadata** (Optional): Google Gemini AI extracts accurate artist/song information
- **Smart Title Parser**: Fallback parser ensures videos always play, even without Gemini
- **Audio-Only Mode**: Option to download minimal video quality (144p) while preserving high audio quality

### 🔧 Advanced Features
- **Background Processing**: All heavy tasks run in separate threads (no OBS freezing)
- **Multi-Instance Support**: Run multiple independent players by copying the script
- **Nested Scene Playback**: Videos play even when scene is nested within other scenes
- **Scene Transition Support**: Proper handling with configurable delays
- **Comprehensive Logging**: Both OBS console and file-based logs for debugging
- **Automatic Retry**: Failed metadata extractions retry on next startup
- **Configuration Warnings**: Real-time feedback for missing configuration

## Requirements

- **Windows 10/11** (Windows-only script)
- **OBS Studio** with Python scripting support
- **Internet connection** for initial video downloads
- **Disk space** for video cache (varies by playlist size)
- **Google Gemini API key** (Optional but recommended - free tier available)

## Quick Start

### 1. Installation

#### For New Users (v4.0.0)
1. Download `ytplay.py` and `ytplay_modules/` folder
2. Copy both to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Select `ytplay.py`
5. Create a scene named `ytplay`

#### For Existing Users (Upgrading from v3.x)
1. Download the new files (includes backward-compatible `ytfast.py`)
2. Your existing `ytfast` scene continues working
3. New shared modules improve performance and stability

### 2. Configuration

In script properties, configure:
- **YouTube Playlist URL**: Your playlist URL (no default - must be set)
- **Cache Directory**: Where to store videos (auto-created)
- **Gemini API Key** (Optional): For enhanced metadata extraction
- **Playback Mode**: Choose between Continuous, Single, or Loop
- **Audio Only Mode**: Enable for minimal video quality with high audio quality

Configuration warnings appear at the bottom if anything is missing!

### 3. Scene Setup

1. Create a scene matching your script name (e.g., `ytplay` for `ytplay.py`)
2. Add these sources to the scene:
   - **Media Source** named `video`
   - **Text Source** named `title` (for song info display)
3. Videos start playing when you switch to this scene!

## What's New in v4.0.0

### 🏗️ Modular Architecture
- Main script reduced from 16KB to 2.7KB
- All functionality moved to shared `ytplay_modules/`
- Zero-copy deployment: just rename the script to create new instances

### 🔐 Complete State Isolation
- Each script instance maintains independent state
- No more cross-contamination between instances
- Thread-safe context management

### 🎯 Improved User Experience
- Configuration warnings displayed in UI
- No confusing default playlist URL
- Better organized property layout
- Clear feedback for missing configuration

### 🔄 Migration Path
- Backward compatible with v3.x setups
- Existing `ytfast.py` users can upgrade seamlessly
- Option to migrate to cleaner `ytplay.py` naming

## Multi-Instance Setup (v4.0.0)

Running multiple players is now even easier:

1. Copy `ytplay.py` to a new name (e.g., `worship.py`, `bgm.py`)
2. All instances automatically share `ytplay_modules/`
3. Each gets its own cache, settings, and state
4. Create matching scene names for each script

Example structure:
```
obs-scripts/
├── ytplay.py            → Scene: ytplay
├── worship.py           → Scene: worship (copy of ytplay.py)
├── bgm.py              → Scene: bgm (copy of ytplay.py)
├── ytfast.py           → Scene: ytfast (backward compatibility)
└── ytplay_modules/     → SHARED by all scripts
    ├── config.py
    ├── state.py
    ├── playback.py
    └── [other modules]
```

## Playback Modes Explained

### 🔄 Continuous Mode (Default)
Perfect for background music streams:
- Plays videos randomly from your playlist
- Never repeats until all videos have played
- Continues forever while scene is active
- Stops when switching to another scene

### ▶️ Single Mode
Ideal for intro/outro videos:
- Plays one random video and stops
- Media source becomes blank after playback
- Switching scenes and back plays a new video
- Great for scheduled content breaks

### 🔁 Loop Mode
Best for ambient content or hold music:
- Randomly selects one video and repeats it
- Same video loops until scene becomes inactive
- New random video selected when scene reactivates
- Perfect for consistent background content

## Troubleshooting

### Configuration Warnings
The script now shows warnings at the bottom of settings for:
- Missing scene
- Missing media or text sources
- No playlist URL configured
- Tools not ready

### Videos Not Playing?
1. **Check configuration warnings** in script properties
2. **Verify scene name** matches script name (without .py)
3. **Confirm source names** are exactly `video` and `title`
4. **Check logs** in `{cache_dir}/logs/` for errors

### Multi-Instance Issues?
- Each instance needs its own scene
- Check logs to identify which instance has problems
- Verify no state contamination between instances
- Ensure all instances use shared `ytplay_modules/`

## Project Structure (v4.0.0)

```
ytplay.py                 # Ultra-minimal main script
ytplay_modules/           # Shared modules directory
├── main.py              # Entry point orchestration
├── config.py            # Configuration (v4.0.0)
├── state.py             # Isolated state management
├── ui.py                # Property definitions
├── logger.py            # Script-aware logging
├── playback.py          # Full playback control
├── metadata.py          # Gemini + fallback parsing
├── download.py          # yt-dlp integration
├── normalize.py         # Audio normalization
└── [other modules]      # Additional functionality
```

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check `/docs` folder for detailed guides
- **Logs**: Enable debug logging for troubleshooting
