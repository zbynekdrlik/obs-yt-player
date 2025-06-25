# Multi-Script Setup Guide

## Overview
The OBS YouTube Player architecture supports running multiple script instances simultaneously, each with its own playlist, cache, and configuration. This guide explains how to set up `ytfast.py` and create additional scripts like `yt_worship.py`.

## How Multi-Script Support Works

### 1. Script-Specific Naming Convention
Each script automatically creates its own ecosystem based on the script filename:
- **Script Name**: `ytfast.py` → Scene name: `ytfast`
- **Modules Directory**: `ytfast_modules/`
- **Default Cache**: `ytfast-cache/`
- **Log Identification**: `[ytfast]` in logs

### 2. Automatic Isolation
- Each script maintains separate:
  - YouTube playlist URL
  - Cache directory for videos
  - Media and text sources in OBS
  - Playback state and settings
  - Module directories

## Setting Up Multiple Scripts

### Step 1: Create New Script File
To create a worship music player alongside ytfast:
1. Copy `ytfast.py` to `yt_worship.py`
2. The script will automatically:
   - Use scene name `yt_worship`
   - Create `yt_worship_modules/` directory
   - Default to `yt_worship-cache/` for videos

### Step 2: Configure Each Script in OBS
1. Add both scripts to OBS:
   - Scripts → Add → `ytfast.py`
   - Scripts → Add → `yt_worship.py`

2. Configure different playlists:
   - **ytfast**: Your regular music playlist
   - **yt_worship**: Your worship music playlist

### Step 3: Scene Setup
OBS will automatically create scenes for each script:
- Scene `ytfast` with sources:
  - Media Source: `video`
  - Text Source: `title`
- Scene `yt_worship` with sources:
  - Media Source: `video`
  - Text Source: `title`

## Example: Creating yt_worship.py

```python
# Simply copy ytfast.py to yt_worship.py
# The script will automatically adapt based on its filename
```

No code changes needed! The script uses its own filename to determine:
- Which scene to control
- Where to store modules
- Default cache location

## Directory Structure with Multiple Scripts

```
obs-yt-player/
├── ytfast.py                    # Fast music player
├── ytfast_modules/              # Modules for ytfast
│   ├── config.py
│   ├── logger.py
│   └── ...
├── ytfast-cache/                # Videos for ytfast
│   └── videos/
├── yt_worship.py                # Worship music player
├── yt_worship_modules/          # Modules for yt_worship
│   ├── config.py
│   ├── logger.py
│   └── ...
└── yt_worship-cache/            # Videos for yt_worship
    └── videos/
```

## Configuration Tips

### Different Settings Per Script
Each script can have different:
- **Playlist URLs**: Different YouTube playlists
- **Cache Directories**: Custom paths if needed
- **Playback Modes**: Continuous, Single, or Loop
- **Audio-Only Mode**: Enable for one, disable for another
- **Gemini API**: Same key can be used across scripts

### Custom Cache Locations
While each script defaults to `<scriptname>-cache/`, you can customize:
- **ytfast**: `D:/StreamingAssets/FastMusic/`
- **yt_worship**: `D:/StreamingAssets/WorshipMusic/`

### Scene Organization
You can organize your scenes:
```
Main Broadcast Scene
├── Camera Source
├── ytfast (nested scene - plays background music)
└── Overlay Graphics

Worship Scene
├── Camera Source
├── yt_worship (nested scene - plays worship videos)
└── Lyrics Overlay
```

## Monitoring Multiple Scripts

### Log Identification
Background thread logs show which script they belong to:
```
[Unknown Script] [2024-01-13 10:00:00] [ytfast] Starting playlist sync...
[Unknown Script] [2024-01-13 10:00:01] [yt_worship] Starting playlist sync...
```

### Version Tracking
Each script maintains its own version:
```
[ytfast.py] [2024-01-13 10:00:00] Script version 3.3.0 loaded
[yt_worship.py] [2024-01-13 10:00:00] Script version 3.3.0 loaded
```

## Best Practices

1. **Unique Playlists**: Use different playlists for each script to avoid cache conflicts
2. **Descriptive Names**: Choose script names that reflect their purpose
3. **Separate Caches**: Keep default cache directories to maintain isolation
4. **Test Independently**: Verify each script works before running multiple
5. **Monitor Resources**: Multiple scripts mean multiple download/processing threads

## Troubleshooting

### Scripts Interfering with Each Other
- Check that scene names match script names (without .py extension)
- Verify each script has its own cache directory
- Ensure Media/Text source names are consistent (`video` and `title`)

### Performance Issues
- Reduce concurrent downloads if bandwidth is limited
- Consider enabling audio-only mode for background music scripts
- Stagger initial syncs to avoid overload

### Module Conflicts
- Each script's modules are isolated in `<scriptname>_modules/`
- No shared state between scripts
- Updates to one script don't affect others

## Advanced: Shared Modules
If you want to share code between scripts:
1. Create a `shared_modules/` directory
2. Add to Python path in each script
3. Import shared utilities

However, the default isolated approach is recommended for stability.