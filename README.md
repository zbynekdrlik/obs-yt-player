# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🚀 Version 4.0.0 - Modular Architecture

Major architectural improvements for better multi-instance support and maintainability:
- **Shared Modules**: All script instances now share `ytplay_modules/` directory
- **Complete State Isolation**: Multiple scripts can run simultaneously without interference
- **Ultra-Minimal Main Script**: Main script reduced from 16KB to under 5KB
- **Backward Compatibility**: Existing `ytfast.py` users can continue without changes

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
- **Multi-Instance Support**: Run multiple independent players with complete isolation
- **Nested Scene Playback**: Videos play even when scene is nested within other scenes
- **Scene Transition Support**: Proper handling with configurable delays
- **Comprehensive Logging**: Both OBS console and file-based logs for debugging
- **Automatic Retry**: Failed metadata extractions retry on next startup
- **Configuration Warnings**: Clear feedback about missing setup requirements

## Requirements

- **Windows 10/11** (Windows-only script)
- **OBS Studio** with Python scripting support
- **Internet connection** for initial video downloads
- **Disk space** for video cache (varies by playlist size)
- **Google Gemini API key** (Optional but recommended - free tier available)

## Quick Start

### 1. Installation

1. Download the latest release (includes `ytplay.py` and `ytplay_modules/` folder)
2. Copy both to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Select `ytplay.py` (or `ytfast.py` for backward compatibility)

### 2. Configuration

In script properties, configure:
- **YouTube Playlist URL**: Your playlist URL (no default - must be configured)
- **Cache Directory**: Where to store videos (auto-created)
- **Gemini API Key** (Optional): For enhanced metadata extraction (see below)
- **Playback Mode**: Choose between Continuous, Single, or Loop
- **Audio Only Mode**: Enable for minimal video quality with high audio quality

Configuration warnings appear at the bottom of settings if anything is missing!

### 3. Scene Setup

1. Create a scene matching your script name (e.g., `ytplay` for `ytplay.py`)
2. Add these sources to the scene:
   - **Media Source** named `video`
   - **Text Source** named `title` (for song info display)
3. Videos start playing when you switch to this scene!

## 🆕 Migration from Previous Versions

### For ytfast.py Users
You have two options:

**Option A - No Changes Required** (Recommended for existing setups):
- The new version includes `ytfast.py` as a compatibility wrapper
- Your existing OBS scenes and settings continue working
- Benefits from all v4.0.0 improvements automatically

**Option B - Clean Migration**:
1. Rename your OBS scene from `ytfast` to `ytplay`
2. Remove `ytfast.py` from OBS Scripts
3. Add `ytplay.py` instead
4. All settings and cache will be preserved

### Shared Modules Architecture
- All scripts now share `ytplay_modules/` directory
- Updates to modules benefit all script instances
- No more copying files for multi-instance setups
- Each instance maintains independent state and settings

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

## Audio-Only Mode

Enable this option when you only need audio output from OBS:
- Downloads videos at minimal quality (144p) to save bandwidth
- Preserves the highest available audio quality
- Significantly reduces download time and storage usage
- Perfect for radio streams or audio-only broadcasts

Benefits:
- **80-90% smaller file sizes** compared to normal quality
- **Faster downloads** on limited bandwidth connections
- **Same high-quality audio** as normal mode
- **Lower CPU usage** during playback

## Metadata System

### Why Use Google Gemini? (Recommended)

While the script works perfectly without Gemini, using it provides significantly better metadata extraction:

- **Superior Accuracy**: Gemini uses AI with Google Search to understand complex video titles that simple parsers miss
- **International Support**: Works with videos in any language, including non-Latin scripts
- **Context Understanding**: Recognizes artists and songs even when titles use unusual formatting
- **Handles Edge Cases**: Correctly extracts metadata from titles like:
  - "HOLYGHOST | Sons Of Sunday" (reversed format)
  - "'COME RIGHT NOW' | Official Video" (quotes and annotations)
  - "Forever | Live At Chapel" (live performances)
  - Videos with multiple artists, remixes, or features

### 🤖 Google Gemini AI (Optional but Recommended)
- Uses Gemini 2.5 Flash with Google Search grounding for intelligent extraction
- Provides the most accurate artist/song detection available
- Free tier offers 2 requests/minute, 50 requests/day (plenty for most users)
- When not configured, script automatically uses title parser

### 📝 Smart Title Parser (Always Available)
- Built-in fallback that ensures the script always works
- Handles common patterns: "Artist - Song", "Song | Artist"
- While functional, it's less accurate than Gemini for complex titles
- Perfect for simple playlists or when Gemini isn't needed

### 🔄 File Naming & Automatic Retry
- Videos processed without Gemini (or when Gemini fails) are marked with `_gf` suffix
- Example: `song_artist_videoID_normalized_gf.mp4`
- On each startup, the script automatically retries Gemini extraction for `_gf` files
- If Gemini succeeds on retry, the file is renamed without the `_gf` marker
- This ensures your library improves over time without manual intervention

## Advanced Usage

### Multi-Instance Setup (v4.0.0 Simplified!)

Run multiple independent players with the new architecture:

1. Simply copy `ytplay.py` to new names (e.g., `music.py`, `bgm.py`)
2. All instances automatically share `ytplay_modules/`
3. Each instance maintains separate:
   - Settings and configuration
   - Cache directories
   - Playback state
   - Scene associations

Example structure:
```
obs-scripts/
├── ytplay.py          → Scene: ytplay
├── music.py           → Scene: music (copy of ytplay.py)
├── bgm.py             → Scene: bgm (copy of ytplay.py)
├── ytfast.py          → Scene: ytfast (backward compatibility)
└── ytplay_modules/    → SHARED by all scripts
    ├── config.py
    ├── main.py
    ├── state.py
    └── [other modules]
```

Benefits:
- Update modules once, all instances benefit
- No module duplication
- Complete state isolation
- Easy to create new instances (just copy 4KB file)

### Nested Scene Usage

Include YouTube player scenes within other scenes:

1. Set up your YouTube player scene as normal
2. In another scene, add a "Scene" source
3. Select your YouTube player scene
4. Videos play when the parent scene is active!

Perfect for:
- Picture-in-picture layouts
- Multi-camera setups with background music
- Complex scene compositions
- Dynamic streaming layouts

## Getting a Gemini API Key (Optional)

While not required, a Gemini API key significantly improves metadata accuracy:

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy key to OBS script settings
5. Free tier = 2 requests/minute, 50 requests/day (plenty for most users)

Note: The script works perfectly without a Gemini key - it will use the built-in title parser instead.

## Troubleshooting

### Configuration Warnings
v4.0.0 shows warnings at the bottom of settings for:
- Missing playlist URL
- Missing scene or sources
- Tools not ready (downloading)
- Cache directory issues

### Videos Not Playing?
1. **Check configuration warnings** in script settings
2. **Verify scene name** matches script name (without .py)
3. **Confirm source names** are exactly `video` and `title`
4. **Check logs** in `{cache_dir}/logs/` for errors

### Multi-Instance Issues?
- Each script should have unique filename
- Scene names must match script names
- Check logs for script identification
- Verify no state cross-contamination

### Playback Mode Issues?
- Mode changes take effect immediately
- Current video continues in new mode
- Scene must be reactivated for some mode changes

### Metadata Problems?
- If using Gemini: Verify API key is correct
- Without Gemini: Videos will play with basic title parsing
- Files marked with `_gf` will retry Gemini on next startup
- Check logs for metadata extraction details

## Project Structure (v4.0.0)

```
ytplay.py                  # Ultra-minimal main script (<5KB)
ytfast.py                  # Backward compatibility wrapper
ytplay_modules/            # SHARED modules directory
├── __init__.py           # Package initialization
├── main.py               # Main entry points
├── config.py             # Configuration (v4.0.0)
├── state.py              # Per-script state isolation
├── logger.py             # Thread-aware logging
├── ui.py                 # UI and warnings
├── playback.py           # Playback control
├── scene.py              # Scene management
├── playlist.py           # Playlist sync
├── download.py           # Video downloading
├── metadata.py           # Metadata extraction
└── [other modules]       # Additional functionality
```

## Recent Updates

### v4.0.0 - Modular Architecture Redesign
- Complete architectural overhaul for better multi-instance support
- Shared `ytplay_modules/` directory for all scripts
- Ultra-minimal main script (<5KB vs 16KB+)
- Full state isolation between instances
- Configuration warnings in UI
- Backward compatibility with ytfast.py
- No default playlist URL (must be user-configured)
- Improved thread safety and cleanup

### v3.4.4 - Documentation Clarity
- Clarified that Gemini API key is optional
- Added detailed explanation of why Gemini provides better results
- Documented _gf file naming behavior
- Improved metadata system documentation

### v3.4.0 - Audio-Only Mode
- Added option for minimal video quality downloads
- Preserves high audio quality while saving bandwidth
- Significantly reduces file sizes and download times
- Perfect for audio-only streaming scenarios

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check `/docs` folder for detailed guides
- **Logs**: Enable debug logging for troubleshooting
- **Multi-Instance**: See advanced usage for v4.0.0 setup
