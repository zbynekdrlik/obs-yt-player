# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🆕 New: Folder-Based Multi-Instance Support

The latest version introduces a **folder-based architecture** for running multiple YouTube players. Each instance lives in its own folder with complete isolation - no more state conflicts or import issues! See [Multi-Instance Setup](#multi-instance-setup-new-folder-based-approach) below.

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
- **Multi-Instance Support**: Run multiple independent players using folder-based isolation
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

#### Option A: Single Instance (Legacy)
1. Download `ytfast.py` and `ytfast_modules/` folder
2. Copy both to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Select `ytfast.py`

#### Option B: Folder-Based (Recommended for Multiple Instances)
1. Download the release package
2. Run `python migrate_to_folders.py` to convert to folder structure
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Select `yt-player-main/ytfast.py`

### 2. Configuration

In script properties, configure:
- **YouTube Playlist URL**: Your playlist URL
- **Cache Directory**: Where to store videos (auto-created)
- **Gemini API Key** (Optional): For enhanced metadata extraction (see below)
- **Playback Mode**: Choose between Continuous, Single, or Loop
- **Audio Only Mode**: Enable for minimal video quality with high audio quality

### 3. Scene Setup

1. Create a scene named `ytfast` (matching script name without .py)
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

## Multi-Instance Setup (NEW: Folder-Based Approach)

### Why Folder-Based?

The new folder-based approach provides:
- ✅ **Complete isolation** between instances (no state conflicts)
- ✅ **Simple setup** using the helper script
- ✅ **Easy maintenance** - update instances independently
- ✅ **Clear organization** - one folder per player

### Quick Setup with Helper Script

Create a new player instance in seconds:

```bash
python setup_new_instance.py main worship
```

This creates a complete `yt-player-worship/` instance with:
- Renamed script (`ytworship.py`)
- Renamed modules (`ytworship_modules/`)
- Updated imports and configuration
- Clean cache directory

### Folder Structure

```
obs-scripts/
├── yt-player-main/              # Main player
│   ├── ytfast.py
│   ├── ytfast_modules/
│   └── cache/
├── yt-player-worship/           # Worship music player
│   ├── ytworship.py
│   ├── ytworship_modules/
│   └── cache/
├── yt-player-kids/              # Kids content player
│   ├── ytkids.py
│   ├── ytkids_modules/
│   └── cache/
└── setup_new_instance.py        # Helper script
```

### Migration from Old Structure

If you're using the old single-file approach:

```bash
python migrate_to_folders.py
```

This will:
1. Create `yt-player-main/` directory
2. Move your existing files into it
3. Update your OBS script path
4. Preserve all your settings

See [docs/FOLDER_BASED_INSTANCES.md](docs/FOLDER_BASED_INSTANCES.md) for detailed information.

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

### Videos Not Playing?
1. **Check scene name** matches script name (without .py)
2. **Verify source names** are exactly `video` and `title`
3. **Confirm playlist URL** is valid and public
4. **Check logs** in `{cache_dir}/logs/` for errors

### Playback Mode Issues?
- Mode changes take effect immediately
- Current video continues in new mode
- Scene must be reactivated for some mode changes

### Metadata Problems?
- If using Gemini: Verify API key is correct
- Without Gemini: Videos will play with basic title parsing
- Files marked with `_gf` will retry Gemini on next startup
- Check logs for metadata extraction details

### Multi-Instance Problems?
- Ensure each instance is in its own folder
- Check that imports match folder names
- Verify scene names match script names
- Use helper script for reliable setup

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

### Single Instance (Legacy)
```
ytfast.py                  # Main OBS interface
ytfast_modules/
├── config.py             # Configuration and constants
├── logger.py             # Thread-safe logging system
├── state.py              # Global state management
└── [other modules]       # Additional functionality
```

### Folder-Based (Recommended)
```
yt-player-main/
├── ytfast.py             # Main OBS interface
├── ytfast_modules/       # All modules
└── cache/                # Video cache

setup_new_instance.py     # Helper for creating instances
migrate_to_folders.py     # Migration from old structure
```

## Recent Updates

### v4.0.0 - Folder-Based Architecture (Coming Soon)
- New folder-based approach for true multi-instance support
- Helper scripts for easy setup and migration
- Complete isolation between instances
- Simplified maintenance and updates

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

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check `/docs` folder for detailed guides
- **Logs**: Enable debug logging for troubleshooting
