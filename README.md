# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

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
- **True Multi-Instance Support** (v3.6.0): Run multiple scripts simultaneously without interference

### 🔧 Advanced Features
- **Background Processing**: All heavy tasks run in separate threads (no OBS freezing)
- **Multi-Instance Support**: Run multiple independent players with complete state isolation
- **Nested Scene Playback**: Videos play even when scene is nested within other scenes
- **Scene Transition Support**: Proper handling with configurable delays
- **Comprehensive Logging**: Both OBS console and file-based logs for debugging
- **Automatic Retry**: Failed metadata extractions retry on next startup

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
4. Select `ytplay.py`

### 2. Configuration

In script properties, configure:
- **YouTube Playlist URL**: Your playlist URL (no default - must be set)
- **Cache Directory**: Where to store videos (defaults to `ytplay-cache/`)
- **Gemini API Key** (Optional): For enhanced metadata extraction (see below)
- **Playback Mode**: Choose between Continuous, Single, or Loop
- **Audio Only Mode**: Enable for minimal video quality with high audio quality

### 3. Scene Setup

1. Create a scene named `ytplay` (matching script name without .py)
2. Add these sources to the scene:
   - **Media Source** named `video`
   - **Text Source** named `title` (for song info display)
3. Videos start playing when you switch to this scene!

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
- Uses Gemini 2.0 Flash with Google Search grounding for intelligent extraction
- Provides the most accurate artist/song detection available
- Free tier offers 15 requests/minute, 1500 requests/day (plenty for most users)
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

### Multi-Instance Setup

Run multiple independent players with complete state isolation (v3.6.0):

1. Copy and rename the script (e.g., `yt_worship.py`, `yt_ambient.py`)
2. Each instance automatically creates its own:
   - Scene name (matching the script name)
   - Cache directory (`yt_worship-cache/`, `yt_ambient-cache/`)
   - Settings and playlist configuration
   - Isolated state that doesn't interfere with other instances
3. All scripts share the common `ytplay_modules/` directory

Example structure:
```
obs-scripts/
├── ytplay.py              → Scene: ytplay
├── yt_worship.py          → Scene: yt_worship
├── yt_ambient.py          → Scene: yt_ambient
└── ytplay_modules/        → SHARED modules for all scripts
    ├── config.py
    ├── logger.py
    └── [other modules]
```

Benefits of shared modules:
- **Single update point**: Update modules once, all scripts benefit
- **Consistent behavior**: All scripts use the same core logic
- **Easy maintenance**: One set of modules to maintain
- **Simplified setup**: Just copy the main script file
- **Complete isolation**: Each script instance maintains its own state

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
5. Free tier = 15 requests/minute, 1500 requests/day (plenty for most users)

Note: The script works perfectly without a Gemini key - it will use the built-in title parser instead.

## Troubleshooting

### Videos Not Playing?
1. **Check playlist URL** is set (no default URL in v3.5.0+)
2. **Check scene name** matches script name (without .py)
3. **Verify source names** are exactly `video` and `title`
4. **Confirm playlist** is valid and public
5. **Check logs** in `{cache_dir}/logs/` for errors

### Playback Mode Issues?
- Mode changes take effect immediately
- Current video continues in new mode
- Scene must be reactivated for some mode changes

### Metadata Problems?
- If using Gemini: Verify API key is correct
- Without Gemini: Videos will play with basic title parsing
- Files marked with `_gf` will retry Gemini on next startup
- Check logs for metadata extraction details

### Multi-Instance Issues?
- Ensure each script has a unique filename
- Check that scene names match script names
- Verify logs show correct script identification
- Each instance should have separate cache directories

### Nested Scene Not Working?
- Ensure nested source is visible (eye icon)
- Source names must match exactly
- Check parent scene is active
- Look for "nested source" in logs

### Audio-Only Mode Questions?
- Check logs for "Audio-only mode" messages
- Verify videos show 144p resolution in logs
- File sizes should be significantly smaller
- Audio quality remains unchanged

## Project Structure

```
ytplay.py                  # Default OBS interface script
yt_worship.py             # Example additional instance
ytplay_modules/           # SHARED modules for all scripts
├── config.py             # Configuration and constants
├── logger.py             # Thread-safe logging system
├── state.py              # Script-isolated state management
├── playback.py           # Playback mode logic
├── scene.py              # Scene activation detection
├── playlist.py           # YouTube playlist sync
├── download.py           # Video downloading
├── normalize.py          # Audio normalization
├── metadata.py           # Metadata extraction
├── gemini_metadata.py    # Gemini AI integration
└── [other modules]       # Additional functionality
```

## Recent Updates

### v3.6.0 - True Multi-Instance Support
- **FIXED**: Complete state isolation between script instances
- **NEW**: Each script maintains its own isolated state
- **IMPROVED**: Proper script identification in all logs
- **ENHANCED**: Background threads correctly inherit script context
- **MAINTAINED**: Full backward compatibility with existing setups

### v3.5.0 - Common Modules Architecture
- **BREAKING**: Renamed default script from `ytfast.py` to `ytplay.py`
- **NEW**: All scripts now share common `ytplay_modules/` directory
- **CHANGE**: Default playlist URL is now empty (must be configured)
- **IMPROVED**: Simplified multi-instance setup - just copy main script
- **ENHANCED**: Better script identification in logs

### v3.4.1 - Documentation Clarity
- Clarified that Gemini API key is optional
- Added detailed explanation of why Gemini provides better results
- Documented _gf file naming behavior
- Improved metadata system documentation

### v3.4.0 - Audio-Only Mode
- Added option for minimal video quality downloads
- Preserves high audio quality while saving bandwidth
- Significantly reduces file sizes and download times
- Perfect for audio-only streaming scenarios

### v3.3.1 - Documentation Update
- Improved README with playback modes section
- Better feature organization and clarity
- Enhanced troubleshooting guide

### v3.3.0 - Nested Scene Playback
- Recursive scene detection for nested sources
- Support for multiple nesting levels
- Enhanced logging for scene activation

## Migration from v3.4.x

If upgrading from ytfast.py to the new architecture:

1. **Rename your script**: `ytfast.py` → `ytplay.py` (or keep ytfast.py if preferred)
2. **Rename modules folder**: `ytfast_modules/` → `ytplay_modules/`
3. **Update scene name**: Scene `ytfast` → Scene `ytplay` (or match your script name)
4. **Set playlist URL**: No default URL in v3.5.0+

Note: You can keep using `ytfast.py` as your script name - just ensure the modules are in `ytplay_modules/`

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check `/docs` folder for detailed guides
- **Logs**: Enable debug logging for troubleshooting
