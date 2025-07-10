# OBS YouTube Player 🎬

A Windows-only OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them with multiple playback modes. Features optional AI-powered metadata extraction using Google Gemini for superior artist/song detection.

## 🆕 Multi-Instance Support (v4.1.0+)

The player now supports **multiple independent instances** through a clean folder-based architecture. Each instance runs completely isolated with its own playlist, cache, and settings.

### Quick Setup
```cmd
create_new_ytplayer.bat worship
```

This creates a new instance in seconds - no questions asked! See [Multi-Instance Setup](#multi-instance-setup) for details.

**⚠️ BREAKING CHANGE in v4.1.0**: Source names are now prefixed with the instance name to avoid OBS conflicts. See [Migration Guide](#migration-from-v40x-to-v41x) below.

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

Create required OBS sources in your scene (v4.1.0+ naming):

1. **Media Source** named `[instance]_video`
   - For `ytplay.py`: name it `ytplay_video`
   - For `worship.py`: name it `worship_video`
   - Uncheck "Local File"
   - Leave other settings default

2. **Text Source** named `[instance]_title` (optional)
   - For `ytplay.py`: name it `ytplay_title`
   - For `worship.py`: name it `worship_title`
   - Displays current song info

## Migration from v4.0.x to v4.1.x

Version 4.1.0 introduces unique source names to support multiple instances properly. You need to update your OBS scenes:

### Old naming (v4.0.x):
- Media Source: `video`
- Text Source: `title`

### New naming (v4.1.0+):
- Media Source: `[instance]_video`
- Text Source: `[instance]_title`

### Migration Steps:
1. Update to v4.1.0
2. In each OBS scene, rename your sources:
   - `video` → `ytplay_video` (for main instance)
   - `title` → `ytplay_title` (for main instance)
   - For other instances: use their script name prefix
3. Test that videos play correctly

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

**🆕 v2.2.4 - Simplified!** No more prompts - just run:

```cmd
create_new_ytplayer.bat worship
```

This creates a new instance in the parent directory (outside the git repository for safety):
```
C:\OBS-Scripts\
├── obs-yt-player\              # Git repository
│   └── yt-player-main\         # Template
│
└── yt-player-worship\          # New instance (safe from git!)
    ├── worship.py              # Scene: worship
    └── worship_modules\
```

#### Advanced Options:
```cmd
# Create in repository (not recommended - git may delete it!)
create_new_ytplayer.bat test /repo

# Create in custom location
create_new_ytplayer.bat kids /path:D:\OBS\Instances
```

### What Happens:
1. Copies the template folder to parent directory (default)
2. Renames script and modules to match instance name
3. Cleans the cache directory
4. Shows setup instructions
5. **No prompts** - just works!

### Updating All Instances

**🆕 v2.2.1 - Simplified!** Update all instances without interruption:

```cmd
update_all_instances.bat
```

This automatically:
1. Pulls latest changes from GitHub
2. Searches current and parent directories
3. Updates all instances from template
4. Preserves cache and configuration
5. Shows summary - **no prompts!**

#### Advanced Options:
```cmd
# Bring back the old confirmation prompt
update_all_instances.bat /confirm

# Skip parent directory search
update_all_instances.bat /noparent

# Add custom search location
update_all_instances.bat /path:D:\OBS\Instances
```

### Safety Features

The batch scripts are designed to keep your instances safe:
- **Default to parent directory** - Instances created outside git repository
- **Automatic search** - Finds instances in common locations
- **Preserve user data** - Cache and config never deleted during updates
- **Clear feedback** - Shows exactly what's happening

### Instance Source Naming (v4.1.0+)
Each instance automatically uses unique source names:
- `ytplay` instance: `ytplay_video` and `ytplay_title`
- `worship` instance: `worship_video` and `worship_title`
- `kids` instance: `kids_video` and `kids_title`

### Benefits
- ✅ **Complete isolation** between instances
- ✅ **Simple setup** - one command creates everything
- ✅ **No manual configuration** - works immediately
- ✅ **Clear organization** - one folder per player
- ✅ **No source conflicts** - unique names per instance (v4.1.0+)
- ✅ **Git-safe by default** - instances created outside repository

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
- Check Media Source is named exactly `[instance]_video` (e.g., `ytplay_video`)
- Ensure scene containing sources is active
- Verify playlist URL is accessible
- Check Script Log for errors

### Migration Issues (v4.0.x → v4.1.0)?
- Make sure to rename sources in OBS scenes
- Old: `video` → New: `ytplay_video`
- Old: `title` → New: `ytplay_title`
- Each instance needs its own prefix

### High CPU Usage?
- Normal during initial sync/download
- Enable Audio-Only mode for lower resource usage
- Processing runs in background threads

### Metadata Not Showing?
- Text source must be named exactly `[instance]_title`
- Gemini API key improves accuracy significantly
- Files marked with `_gf` will retry Gemini on next startup
- Check logs for metadata extraction details

### Multi-Instance Problems?
- Ensure each instance is in its own folder
- Scene names must match script names
- Source names must use instance prefix (v4.1.0+)
- Use batch file for reliable setup
- Check logs for import errors

### Batch Script Issues?
- Make sure you're in the repository directory
- Template folder `yt-player-main` must exist
- For custom locations, use full paths
- Check file permissions if errors occur

### Nested Scene Not Working?
- Ensure nested source is visible (eye icon)
- Source names must match exactly (with prefix)
- Check logs for scene detection info

### Download Errors?
- Usually temporary YouTube rate limits
- Failed downloads retry automatically
- Check your internet connection
- Verify FFmpeg is accessible

## Project Structure

```
obs-yt-player/
├── yt-player-main/             # Template instance
│   ├── ytplay.py               # Main script
│   ├── ytplay_modules/         # All modules
│   │   ├── __init__.py         # Package marker
│   │   ├── config.py           # Dynamic configuration
│   │   ├── download.py         # Video downloading
│   │   ├── playback.py         # Playback control
│   │   └── ...                 # Other modules
│   └── cache/                  # Video cache
│
├── create_new_ytplayer.bat     # Instance creator (v2.2.4)
├── update_all_instances.bat    # Bulk updater (v2.2.1)
└── docs/                       # Documentation
    └── FOLDER_BASED_INSTANCES.md
```

## Recent Updates

### v4.2.0 - Simplified Batch Scripts
- **NEW**: No-prompt operation by default for both scripts
- `create_new_ytplayer.bat` v2.2.4: Creates instances in parent directory automatically
- `update_all_instances.bat` v2.2.1: Updates all instances without interruption
- Added command-line options for advanced users
- Fixed character encoding for Windows console
- Improved safety with parent directory defaults

### v4.1.0 - Unique Source Names
- **BREAKING**: Source names now prefixed with instance name
- Fixes OBS limitation where sources must have globally unique names
- Enables true multi-instance support without conflicts
- Automatic detection based on script name

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
