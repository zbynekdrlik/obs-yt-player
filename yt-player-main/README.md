# OBS YouTube Player - Main Instance

This is the main/template YouTube player instance for OBS Studio.

## Quick Start

1. In OBS, add this script: **Tools → Scripts → `yt-player-main/ytplay.py`**
2. Create a scene named **`ytplay`**
3. Add required sources to your scene:
   - Media Source: **`ytplay_video`**
   - Text Source: **`ytplay_title`** (optional)
4. Configure your playlist URL in script properties

## OBS Source Setup

| Source Type | Name | Settings |
|-------------|------|----------|
| Media Source | `ytplay_video` | Uncheck "Local File" |
| Text Source | `ytplay_title` | Default settings |

## Creating Additional Instances

Use the batch script in the parent directory:

```cmd
cd ..
create_new_ytplayer.bat worship
```

This creates a new `yt-player-worship/` instance with:
- Script: `worship.py`
- Scene: `worship`
- Sources: `worship_video`, `worship_title`

## Directory Structure

```
yt-player-main/
├── ytplay.py              # Main script (load this in OBS)
├── ytplay_modules/        # Python modules
│   ├── config.py          # Configuration
│   ├── state.py           # Thread-safe state
│   ├── download.py        # Video downloading
│   └── ...                # Other modules
├── cache/                 # Downloaded videos
│   ├── logs/              # Log files
│   └── *.mp4              # Cached videos
└── README.md              # This file
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Scene name | `ytplay` | Derived from script name |
| Cache location | `cache/` | Relative to script |
| Modules | `ytplay_modules/` | Auto-detected |

## Full Documentation

See the [main README](../README.md) for:
- Complete installation guide
- Playback modes (Continuous/Single/Loop)
- Gemini AI integration
- Multi-instance setup
- Troubleshooting

## Version

This template is part of OBS YouTube Player v4.2.0+
