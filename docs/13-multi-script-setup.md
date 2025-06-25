# Multi-Script Setup Guide

## Overview
The OBS YouTube Player architecture supports running multiple script instances simultaneously, each with its own playlist, cache, and configuration. All scripts share a common modules directory (`ytplay_modules`) for easier maintenance and updates.

## How Multi-Script Support Works

### 1. Common Modules Architecture
- **Shared Modules**: All scripts use `ytplay_modules/` directory
- **Script-Specific Elements**:
  - Scene name matches script name (e.g., `ytplay.py` → scene `ytplay`)
  - Cache directories are script-specific (e.g., `ytplay-cache/`, `yt_worship-cache/`)
  - Each script maintains its own state and configuration

### 2. Automatic Script Identification
Each script automatically determines its identity from its filename:
```python
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
```

## Setting Up Multiple Scripts

### Step 1: Initial Setup
1. Ensure `ytplay.py` and `ytplay_modules/` exist in your OBS scripts directory
2. Add `ytplay.py` to OBS and configure your first playlist

### Step 2: Create Additional Scripts
To create a worship music player:
```bash
# Simply copy the main script
cp ytplay.py yt_worship.py
```

That's it! No need to copy modules - all scripts share `ytplay_modules/`

### Step 3: Configure Each Script in OBS
1. Add both scripts to OBS:
   - Scripts → Add → `ytplay.py`
   - Scripts → Add → `yt_worship.py`

2. Configure each script:
   - **YouTube Playlist URL**: Set different playlists for each
   - **Cache Directory**: Automatically defaults to `<scriptname>-cache/`
   - **Other settings**: Configure independently per script

### Step 4: OBS Scene Setup
Each script automatically creates and manages its own scene:
- Scene `ytplay` with sources:
  - Media Source: `video`
  - Text Source: `title`
- Scene `yt_worship` with sources:
  - Media Source: `video`
  - Text Source: `title`

## Directory Structure

```
obs-yt-player/
├── ytplay.py                    # Default player
├── yt_worship.py                # Worship music player
├── ytplay_modules/              # SHARED modules directory
│   ├── config.py               # Configuration constants
│   ├── logger.py               # Logging system
│   ├── state.py                # State management
│   └── ...                     # Other modules
├── ytplay-cache/                # Cache for ytplay
│   └── videos/
└── yt_worship-cache/            # Cache for yt_worship
    └── videos/
```

## Configuration

### Default Settings
- **Playlist URL**: Empty by default (must be set by user)
- **Cache Directory**: `<script-directory>/<scriptname>-cache/`
- **Playback Mode**: Continuous
- **Audio Only Mode**: Disabled
- **Gemini API Key**: Optional (empty by default)

### Per-Script Configuration
Each script maintains independent settings:
- Different YouTube playlists
- Custom cache directories (if needed)
- Individual playback modes
- Separate audio-only settings
- Same Gemini API key can be used across all scripts

### Example Configurations

**ytplay.py** - General music:
- Playlist: Your favorite music playlist
- Cache: `./ytplay-cache/` (default)
- Mode: Continuous
- Audio Only: Disabled

**yt_worship.py** - Worship music:
- Playlist: Worship songs playlist
- Cache: `D:/Worship/cache/` (custom)
- Mode: Continuous
- Audio Only: Enabled (save bandwidth)

**yt_ambient.py** - Background ambience:
- Playlist: Ambient/chill playlist
- Cache: `./yt_ambient-cache/` (default)
- Mode: Loop (repeat favorites)
- Audio Only: Enabled

## Monitoring Multiple Scripts

### Log Identification
Logs clearly show which script they belong to:
```
# Main thread logs
[ytplay.py] [2024-01-13 10:00:00] Script version 3.5.0 loaded
[yt_worship.py] [2024-01-13 10:00:00] Script version 3.5.0 loaded

# Background thread logs
[Unknown Script] [2024-01-13 10:00:01] [ytplay] Starting playlist sync...
[Unknown Script] [2024-01-13 10:00:02] [yt_worship] Starting playlist sync...
```

### Benefits of Shared Modules
1. **Single Update Point**: Update modules once, all scripts benefit
2. **Consistent Behavior**: All scripts use the same core logic
3. **Easier Maintenance**: One set of modules to maintain
4. **Reduced Disk Usage**: No duplicate module files
5. **Simplified Setup**: Just copy the main script file

## Best Practices

1. **Unique Playlists**: Use different playlists to avoid cache conflicts
2. **Descriptive Names**: Choose script names that reflect their purpose
3. **Resource Management**: Consider bandwidth when running multiple scripts
4. **Stagger Syncs**: Don't sync all playlists simultaneously on slow connections
5. **Monitor Performance**: Multiple scripts mean multiple processing threads

## Troubleshooting

### Script Not Working After Copy
- Ensure `ytplay_modules/` directory exists
- Check that scene name matches script name (without .py)
- Verify playlist URL is set (no default URL)

### Scripts Interfering
- Confirm each uses different playlist URLs
- Check cache directories are separate
- Ensure Media/Text source names are `video` and `title`

### Module Updates
- Changes to modules affect ALL scripts
- Test updates with one script before adding more
- Keep backups before major module changes

## Advanced Usage

### Custom Module Paths
If needed, you can modify the modules path in a script:
```python
# Use a different modules directory
MODULES_DIR = os.path.join(SCRIPT_DIR, "custom_modules")
```

### Creating Specialized Scripts
Examples of specialized scripts you might create:
- `yt_livestream.py` - For live streaming background music
- `yt_podcast.py` - For podcast content
- `yt_kids.py` - For children's content
- `yt_workout.py` - For exercise videos

Each maintains its own:
- Scene in OBS
- Cache directory
- Playlist configuration
- Playback settings

While sharing the same reliable core modules!