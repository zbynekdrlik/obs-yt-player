# OBS YouTube Player 🎬

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🆕 Multi-Instance Support (v4.0.7+)

The player now supports **multiple independent instances** through a clean folder-based architecture. Each instance runs completely isolated with its own playlist, cache, and settings.

### Quick Setup
```cmd
create_new_ytplayer.bat worship
```

This creates a new instance in seconds! See [Multi-Instance Setup](#multi-instance-setup) for details.

## Key Features

### 🎬 Playback Modes
- **Continuous**: Plays through all cached videos randomly
- **Single**: Plays one video and stops (perfect for intros/outros)
- **Loop**: Repeats the current video indefinitely

### 🎵 Audio Excellence
- **Loudness normalization** to -14 LUFS (YouTube standard)
- **Professional audio processing** via FFmpeg
- **Audio-only mode** for minimal bandwidth usage
- **Gemini AI metadata** for accurate artist/song detection (optional)

### 📺 OBS Integration
- Seamless **Media Source** integration
- **Scene-aware playback** (only plays when scene is active)
- **Multi-instance support** via folder isolation
- **Metadata display** through Text Sources

### 🔧 Advanced Features
- **Background Processing**: All heavy tasks run in separate threads (no OBS freezing)
- **Multi-Instance Support**: Run multiple independent players
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

1. Download the latest release or clone the repository
2. Copy the `yt-player-main/` folder to your OBS scripts directory
3. In OBS Studio: Tools → Scripts → Add Script (+)
4. Navigate to and select `yt-player-main/ytplay.py`

### 2. Configuration

In script properties, configure:

- **YouTube Playlist URL**: Your playlist (must be public or unlisted)
- **Cache Directory**: Where to store videos (default: `cache`)
- **Playback Mode**: Continuous, Single, or Loop
- **Audio Only Mode**: Check for minimal video quality
- **Gemini API Key**: Optional, for better metadata

### 3. Scene Setup

The script name determines the scene name:
- Script: `ytplay.py` → Scene: `ytplay`
- Script: `worship.py` → Scene: `worship`

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

Use the included batch file to create new instances in seconds:

```cmd
create_new_ytplayer.bat worship
```

This creates:
```
obs-yt-player/
├── yt-player-main/        # Original template
│   ├── ytplay.py          # Scene: ytplay
│   └── ytplay_modules/
└── yt-player-worship/     # New instance
    ├── worship.py         # Scene: worship
    └── worship_modules/
```

### What Happens:
1. Copies the template folder
2. Renames script and modules to match instance name
3. Cleans the cache directory
4. Shows setup instructions

### Benefits
- ✅ **Complete isolation** between instances
- ✅ **Simple setup** - one command creates everything
- ✅ **No manual configuration** - works immediately
- ✅ **Clear organization** - one folder per player

### Example Use Cases

**Different Content Types:**
```cmd
create_new_ytplayer.bat music      # General music
create_new_ytplayer.bat worship    # Worship songs
create_new_ytplayer.bat kids       # Kids content
create_new_ytplayer.bat ambient    # Background music
```

**Stream Scheduling:**
```cmd
create_new_ytplayer.bat morning    # Morning show
create_new_ytplayer.bat afternoon  # Afternoon content
create_new_ytplayer.bat evening    # Evening playlist
```

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

## Nested Scene Usage

Include YouTube player scenes within other scenes:

```
Main Stream Scene
├── Game Capture
├── Webcam
└── Nested Scene: worship (YouTube player)
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
- Scene names must match script names
- Use batch file for reliable setup
- Check logs for import errors

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

```
obs-yt-player/
├── yt-player-main/          # Template instance
│   ├── ytplay.py            # Main script
│   ├── ytplay_modules/      # All modules
│   │   ├── __init__.py      # Package marker
│   │   ├── config.py        # Dynamic configuration
│   │   ├── download.py      # Video downloading
│   │   ├── playback.py      # Playback control
│   │   └── ...              # Other modules
│   └── cache/               # Video cache
│
├── create_new_ytplayer.bat  # Instance creator
└── docs/                    # Documentation
    └── FOLDER_BASED_INSTANCES.md
```

## Recent Updates

### v4.0.7 - Multi-Instance Ready
- Improved batch file (no manual import updates needed)
- Fixed validation and naming issues
- All modules verified against main branch
- Ready for production use

### v4.0.0 - Folder-Based Architecture
- **BREAKING**: Renamed from ytfast to ytplay
- New folder-based approach for true multi-instance support
- Complete isolation between instances
- Dynamic module loading system

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

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.

## Support

If you encounter any issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the OBS Script Log for errors
3. Open an issue on GitHub with:
   - Your OBS version
   - Error messages from the log
   - Steps to reproduce the problem

## Acknowledgments

- **yt-dlp** - For reliable YouTube downloading
- **FFmpeg** - For audio processing and normalization
- **Google Gemini** - For AI-powered metadata extraction
- **OBS Studio** - For the amazing streaming platform
