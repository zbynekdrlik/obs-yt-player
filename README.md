# OBS YouTube Player 🎬

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🆕 Folder-Based Architecture (v4.0.0+)

**NEW**: The player now uses a **folder-based architecture** where each instance lives in its own folder. This provides complete isolation between multiple players - no more state conflicts or import issues!

### Default Structure
```
obs-scripts/
└── yt-player-main/              # Main player template
    ├── ytplay.py                # Script to load in OBS
    ├── ytplay_modules/          # All modules
    └── cache/                   # Video cache
```

## Key Features

### 🎬 Playback Modes
- **Continuous**: Plays through all cached videos randomly
- **Single**: Plays one video and stops (perfect for intros/outros)
- **Loop**: Repeats the current video indefinitely

### 🎵 Audio Excellence
- **Loudness normalization** to -14 LUFS (YouTube standard)
- **Professional audio processing** via FFmpeg
- **Audio-only mode** for minimal bandwidth usage
- **Gemini AI metadata** for accurate artist/song detection

### 📺 OBS Integration
- Seamless **Media Source** integration
- **Scene-aware playback** (only plays when scene is active)
- **Multi-instance support** via folder isolation
- **Metadata display** through Text Sources

### 🔧 Advanced Features
- **Background Processing**: All heavy tasks run in separate threads (no OBS freezing)
- **Multi-Instance Support**: Run multiple independent players using folder-based isolation
- **Nested Scene Playback**: Videos play even when scene is nested within other scenes
- **Scene Transition Support**: Proper handling with configurable delays
- **Comprehensive Logging**: Both OBS console and file-based logs for debugging

## Prerequisites

- **OBS Studio** with Python scripting support
- **Python 3.6+** (comes with OBS)
- **Windows** (yt-dlp and FFmpeg requirements)
- **FFmpeg** (automatically downloaded by the script)
- **Google Gemini API Key** (optional, for enhanced metadata)

## Installation

### 1. Download and Setup

#### For New Installations (Recommended)
1. Download the latest release
2. Copy the `yt-player-main/` folder to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Navigate to and select `yt-player-main/ytplay.py`

#### For Existing Users (Upgrading from v3.x)
If you have the old single-file setup (ytfast.py in root):
```bash
python migrate_to_folders.py
```
This will:
- Move your files to the new folder structure
- Preserve all your settings and cache
- Update your OBS script path

### 2. Configuration

In script properties, configure:

- **YouTube Playlist URL**: Your playlist (must be public or unlisted)
- **Cache Directory**: Where to store videos (default: `cache`)
- **Playback Mode**: Continuous, Single, or Loop
- **Audio Only Mode**: Check for minimal video quality
- **Gemini API Key**: Optional, for better metadata

### 3. Scene Setup

The script name determines the scene name. For example:
- Script: `ytplay.py` → Scene: `ytplay`
- Script: `ytworship.py` → Scene: `ytworship`

Create required OBS sources in your scene:

1. **Media Source** named `video`
   - Uncheck "Local File"
   - Leave other settings default

2. **Text Source** named `title` (optional)
   - Displays current song info

## Usage

### Basic Operation

1. **Load Script**: OBS automatically loads the script on startup
2. **Automatic Sync**: Playlist syncs every 15 minutes (when scene active)
3. **Manual Sync**: Click "Sync Playlist Now" button anytime
4. **Scene Activation**: Videos only download/play when scene is active

### Playback Modes Explained

- **Continuous** (default): Random playback through all videos
- **Single**: Plays one video then stops (resets on scene change)
- **Loop**: Repeats current video (switches videos on scene change)

### Progress Monitoring

Check the OBS Script Log for:
- Download progress with speed/ETA
- Sync status and video counts
- Metadata extraction results
- Any errors or warnings

## Multi-Instance Setup

### Creating Additional Instances

#### Method 1: Using the Batch File (Windows - Recommended)
```cmd
create_new_ytplayer.bat worship
```

#### Method 2: Using Python Script
```bash
python setup_new_instance.py worship
```

This creates:
```
obs-scripts/
├── yt-player-main/              # Original template
│   └── ytplay.py                # Scene: ytplay
└── yt-player-worship/           # New instance
    └── ytworship.py             # Scene: ytworship
```

### Benefits
- ✅ **Complete isolation** between instances
- ✅ **Simple setup** using helper scripts
- ✅ **Easy maintenance** - update instances independently
- ✅ **Clear organization** - one folder per player

See [docs/FOLDER_BASED_INSTANCES.md](docs/FOLDER_BASED_INSTANCES.md) for detailed information.

## Audio-Only Mode

Enable "Audio Only Mode" for:
- Minimal bandwidth usage (144p video)
- Maximum audio quality (192k)
- ~90% smaller file sizes
- Perfect for music-only streams

## Gemini AI Integration (Optional)

The script includes two metadata extraction methods:

1. **Built-in Parser**: Uses regex patterns (good for most titles)
2. **Gemini AI**: Advanced parsing for complex titles (recommended)

### Why Use Gemini?

While the built-in parser works well for standard formats like "Artist - Song", Gemini excels at:
- Complex formats: "Song by Artist (feat. Guest) [Live]"
- Non-standard separators: "Artist • Song | Album"
- Multiple artists and featured guests
- Removing channel names and extra info

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a free API key
3. Paste it in the script settings
4. Enjoy superior metadata extraction!

Note: The script works perfectly without a Gemini key - it will use the built-in parser which handles most common title formats well.

### Automatic Retry System

- Files that fail Gemini processing are marked with `_gf` suffix
- Script retries these files automatically on next startup
- If Gemini succeeds on retry, the file is renamed without the `_gf` marker
- This ensures your library improves over time without manual intervention

### Nested Scene Usage

Include YouTube player scenes within other scenes:

```
Main Stream Scene
├── Game Capture
├── Webcam
└── Nested Scene: ytworship (YouTube player)
```

The player detects nested scenes automatically and continues playback seamlessly.

## Troubleshooting

### Videos Not Playing?
- Check Media Source is named exactly `video`
- Ensure scene containing sources is active
- Verify playlist URL is accessible
- Check Script Log for errors

### High CPU Usage?
- Normal during initial sync/download
- Enable Audio-Only mode for lower resource usage
- Processing runs in background threads

### Metadata Not Showing?
- Text source must be named exactly `title`
- Gemini API key improves accuracy significantly
- Files marked with `_gf` will retry Gemini on next startup
- Check logs for metadata extraction details

### Multi-Instance Problems?
- Ensure each instance is in its own folder
- Check that imports match folder names
- Verify scene names match script names
- Use helper scripts for reliable setup

### Nested Scene Not Working?
- Ensure nested source is visible (eye icon)
- Source names must match exactly
- Check logs for scene detection info

### Download Errors?
- Usually temporary YouTube rate limits
- Failed downloads retry automatically
- Check your internet connection
- Verify FFmpeg is accessible

## Project Structure

### Folder-Based Architecture (v4.0.0+)
```
yt-player-main/
├── ytplay.py             # Main OBS interface
├── ytplay_modules/       # All modules
│   ├── config.py        # Configuration
│   ├── download.py      # Video downloading
│   ├── playback.py      # Playback control
│   └── ...              # Other modules
└── cache/                # Video cache

create_new_ytplayer.bat   # Windows batch file for instances
setup_new_instance.py     # Python script for instances
```

## Recent Updates

### v4.0.1 - Dynamic Script Detection
- Fixed config.py to dynamically detect script name
- Improved multi-instance support
- Added batch file for easy Windows setup

### v4.0.0 - Folder-Based Architecture
- **BREAKING**: Renamed from ytfast to ytplay
- New folder-based approach for true multi-instance support
- Helper scripts for easy setup and migration
- Complete isolation between instances
- Simplified maintenance and updates

### v3.4.1 - Documentation Clarity
- Clarified that Gemini API key is optional
- Added detailed explanation of why Gemini provides better results
- Improved metadata extraction documentation

### v3.4.0 - Audio-Only Mode
- New audio-only mode for bandwidth-conscious users
- Downloads minimal 144p video with high-quality 192k audio
- Significantly reduces file sizes and download times
- Perfect for audio-only streaming scenarios

## License

MIT License - see LICENSE file for details.
