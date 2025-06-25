# OBS YouTube Player (Windows)

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features AI-powered metadata extraction using Google Gemini.

## Key Features

### 🎬 Playback Modes
- **Continuous Mode** (default): Plays all videos randomly forever
- **Single Mode**: Plays one video then stops
- **Loop Mode**: Repeats the same video continuously

### 🎯 Core Functionality
- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists (on startup and manual trigger)
- **Local Caching**: Downloads and stores videos locally for reliable offline playback
- **Audio Normalization**: Normalizes all audio to -14 LUFS using FFmpeg for consistent volume
- **AI-Powered Metadata**: Google Gemini AI extracts accurate artist/song information
- **Smart Fallback**: Title parser handles cases when Gemini is unavailable
- **Audio-Only Mode**: Option to download minimal video quality (144p) while preserving high audio quality

### 🔧 Advanced Features
- **Background Processing**: All heavy tasks run in separate threads (no OBS freezing)
- **Multi-Instance Support**: Run multiple independent players by renaming the script
- **Nested Scene Playback**: Videos play even when scene is nested within other scenes
- **Scene Transition Support**: Proper handling with configurable delays
- **Comprehensive Logging**: Both OBS console and file-based logs for debugging
- **Automatic Retry**: Failed metadata extractions retry on next startup

## Requirements

- **Windows 10/11** (Windows-only script)
- **OBS Studio** with Python scripting support
- **Internet connection** for initial video downloads
- **Disk space** for video cache (varies by playlist size)
- **Google Gemini API key** for metadata extraction (free tier available)

## Quick Start

### 1. Installation

1. Download the latest release (includes `ytfast.py` and `ytfast_modules/` folder)
2. Copy both to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Select `ytfast.py`

### 2. Configuration

In script properties, configure:
- **YouTube Playlist URL**: Your playlist URL
- **Cache Directory**: Where to store videos (auto-created)
- **Gemini API Key**: Get free at https://aistudio.google.com/app/apikey
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

## Advanced Usage

### Multi-Instance Setup

Run multiple independent players:

1. Copy and rename the script (e.g., `music-chill.py`, `stream-bgm.py`)
2. Each instance automatically creates its own:
   - Module folder (`music-chill_modules/`)
   - Cache directory
   - Settings and playlist
3. Create matching scene names for each instance

Example structure:
```
obs-scripts/
├── ytfast.py              → Scene: ytfast
├── ytfast_modules/        → Modules for ytfast
├── music-chill.py         → Scene: music-chill
├── music-chill_modules/   → Modules for music-chill
└── stream-bgm.py          → Scene: stream-bgm
└── stream-bgm_modules/    → Modules for stream-bgm
```

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

## Metadata System

### 🤖 Google Gemini AI (Primary)
- Uses Gemini 2.0 Flash with Google Search grounding
- Extracts artist and song from video titles, descriptions, and context
- Handles complex formats like "Song | Artist" or multiple separators
- Especially accurate for music videos and international content

### 📝 Smart Parser (Fallback)
- Activates when Gemini is unavailable
- Parses common patterns: "Artist - Song", "Song | Artist"
- Ensures videos always play even without AI

### 🔄 Automatic Retry
- Failed extractions marked with `_gf` suffix
- Retried automatically on next OBS startup
- Successful extraction removes the suffix

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
- Verify Gemini API key is correct
- Check internet connection
- Failed extractions retry automatically
- Title parser ensures playback continues

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
ytfast.py                  # Main OBS interface
ytfast_modules/
├── config.py             # Configuration and constants
├── logger.py             # Thread-safe logging system
├── state.py              # Global state management
├── playback.py           # Playback mode logic
├── scene.py              # Scene activation detection
├── playlist.py           # YouTube playlist sync
├── download.py           # Video downloading
├── normalize.py          # Audio normalization
├── metadata.py           # Metadata extraction
├── gemini_metadata.py    # Gemini AI integration
└── [other modules]       # Additional functionality
```

## Getting a Gemini API Key

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy key to OBS script settings
5. Free tier = 2 requests/minute, 50 requests/day (plenty for most users)

## Recent Updates

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

### v3.0.12 - Streamlined Metadata
- Gemini AI as sole metadata source
- Automatic retry system
- Improved reliability

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check `/docs` folder for detailed guides
- **Logs**: Enable debug logging for troubleshooting
