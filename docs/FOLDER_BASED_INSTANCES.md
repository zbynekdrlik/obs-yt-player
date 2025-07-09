# Folder-Based Multi-Instance Setup

## Overview

This document describes the **folder-based approach** for running multiple YouTube player instances in OBS Studio. Each player instance lives in its own completely separate folder with full isolation.

## Why This Approach?

### Problems with Shared Code
- Complex threading context management
- Import path conflicts between instances
- State cross-contamination issues
- Difficult to debug when problems occur
- Regressions when updating shared code

### Benefits of Folder Separation
- ✅ **Complete isolation** - Each instance is 100% independent
- ✅ **Simple to understand** - Just copy a folder
- ✅ **Easy debugging** - Problems stay contained
- ✅ **Version independence** - Update instances separately
- ✅ **No shared state** - Impossible to have conflicts
- ✅ **Clear organization** - One folder = one player
- ✅ **Flexible naming** - Any script name works
- ✅ **Automatic configuration** - No manual import updates needed

## Directory Structure

```
obs-yt-player/
├── yt-player-main/              # Template player instance
│   ├── ytplay.py                # Main script
│   ├── ytplay_modules/          # Module directory
│   │   ├── __init__.py
│   │   ├── config.py            # Auto-detects script name
│   │   ├── download.py
│   │   ├── metadata.py
│   │   └── ...
│   └── cache/                   # Cache directory
│
├── yt-player-worship/           # Worship player instance
│   ├── worship.py               # Instance script
│   ├── worship_modules/         # Instance modules (auto-configured)
│   │   └── ...                  # All modules work automatically
│   └── cache/
│
├── yt-player-kids/              # Kids player instance
│   ├── kids.py
│   ├── kids_modules/
│   └── cache/
│
└── create_new_ytplayer.bat      # Windows batch file for instances
```

## Creating a New Instance

### Using the Windows Batch File (Recommended)

```cmd
create_new_ytplayer.bat worship
```

This will:
1. Copy `yt-player-main/` to `yt-player-worship/`
2. Rename `ytplay.py` to `worship.py`
3. Rename `ytplay_modules/` to `worship_modules/`
4. Clean the cache directory
5. Display setup instructions

**Note:** The batch file no longer updates imports because the dynamic import system handles this automatically!

### Manual Setup (Advanced Users)

1. **Copy the entire folder**
   ```bash
   cp -r yt-player-main/ yt-player-worship/
   ```

2. **Rename the main script**
   ```bash
   cd yt-player-worship
   mv ytplay.py worship.py
   ```

3. **Rename the modules folder**
   ```bash
   mv ytplay_modules/ worship_modules/
   ```

4. **Clean cache directory**
   ```bash
   rm -rf cache/*
   ```

That's it! No import updates needed - the script automatically detects its module directory.

## How the Dynamic Import System Works

The multi-instance system uses intelligent module loading:

1. **Script Detection**
   ```python
   SCRIPT_NAME = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]
   MODULES_DIR_NAME = f"{SCRIPT_NAME}_modules"
   ```

2. **Dynamic Import**
   ```python
   modules = importlib.import_module(MODULES_DIR_NAME)
   ```

3. **Relative Imports**
   - All modules use relative imports: `from .logger import log`
   - These work regardless of the module directory name

This means each instance automatically finds its own modules without any manual configuration!

## OBS Setup

For each player instance:

1. **Add the script to OBS**
   - Scripts → + → Add `yt-player-worship/worship.py`

2. **Create the scene**
   - Scene name = script name (without .py)
   - Example: `worship.py` → Scene: `worship`

3. **Add required sources**
   - **Media Source** named `video`
     - Uncheck "Local File"
     - Leave other settings default
   - **Text Source** named `title` (optional)
     - For displaying song metadata

4. **Configure the script**
   - Set the YouTube playlist URL
   - Configure other settings as needed

## Naming Conventions

The script name (without .py) becomes the scene name:

| Script Name | Scene Name | Example Use |
|-------------|------------|-------------|
| `ytplay.py` | `ytplay` | General music |
| `worship.py` | `worship` | Worship music |
| `kids.py` | `kids` | Kids content |
| `ambient.py` | `ambient` | Background music |
| `remixes.py` | `remixes` | Remix playlist |

## Key Features

1. **Dynamic Configuration**
   - `config.py` automatically detects the script name
   - Scene name is derived from script filename
   - No hardcoded paths or names

2. **Module Isolation**
   - Each instance has its own modules folder
   - Modules are loaded dynamically at runtime
   - Complete separation of code execution

3. **Cache Separation**
   - Each instance has its own cache folder
   - No conflicts between different playlists
   - Independent download and processing

## Best Practices

1. **Keep a template instance**
   - Maintain `yt-player-main/` as your template
   - Update and test changes there first
   - Copy to other instances after testing

2. **Version control**
   - Track the template folder in git
   - Consider `.gitignore` for instance folders
   - Or commit them for full version control

3. **Consistent updates**
   - When updating shared functionality, update template first
   - Use batch file to recreate instances
   - Test each instance after updates

4. **Naming strategy**
   - Use descriptive names for instances
   - Keep names short but clear
   - Avoid special characters or spaces

## Advanced Usage

### Batch Operations

Create multiple instances quickly:

```batch
create_new_ytplayer.bat worship
create_new_ytplayer.bat kids
create_new_ytplayer.bat ambient
create_new_ytplayer.bat remixes
```

### Different Configurations

Use instances for different quality settings:

```
yt-player-hd/        → High quality downloads
yt-player-sd/        → Standard quality
yt-player-audio/     → Audio-only mode
```

## Troubleshooting

### Script not loading in OBS
- Check that Python file exists and is readable
- Ensure modules folder was renamed correctly
- Verify `__init__.py` exists in modules folder

### Import errors
```
ModuleNotFoundError: No module named 'worship_modules'
```
- Module folder name must match script name + "_modules"
- Example: `worship.py` needs `worship_modules/`
- Check for typos in folder names

### Wrong scene detected
- Scene name comes from script filename
- `worship.py` → Scene must be named `worship`
- Check OBS scene name matches exactly

### Videos not playing
- Media Source must be named `video`
- Scene must be active or nested
- Check cache folder permissions

## Migration from Old Setup

If upgrading from the single-file setup:

1. **Backup your current setup**
   ```bash
   cp -r obs-scripts obs-scripts-backup
   ```

2. **Download the new version**
   - Get the latest release with folder structure

3. **Move your cache** (optional)
   - Copy your existing cache to preserve downloads
   - Place in `yt-player-main/cache/`

4. **Update OBS script paths**
   - Remove old script references
   - Add new scripts from folders

5. **Verify functionality**
   - Test each instance
   - Check logs for errors

## Technical Details

### Module Loading Process

1. Main script determines its own name
2. Calculates module directory name
3. Uses `importlib` to dynamically load modules
4. All internal imports use relative paths

### Why This Works

- **No hardcoded module names** in the codebase
- **Relative imports** (`.module`) work in any directory
- **Dynamic detection** adapts to any script name
- **Package structure** (`__init__.py`) enables clean imports

## Example Use Cases

### Multiple Content Types
```
yt-player-music/      → General music playlist
yt-player-worship/    → Worship service playlist  
yt-player-kids/       → Children's content
yt-player-teaching/   → Educational videos
```

### Stream Scheduling
```
yt-player-morning/    → Morning show content
yt-player-afternoon/  → Afternoon playlist
yt-player-evening/    → Evening programming
```

### Language Variants
```
yt-player-english/    → English content
yt-player-spanish/    → Spanish content
yt-player-french/     → French content
```

### Quality Variants
```
yt-player-hd/         → 1080p downloads
yt-player-sd/         → 480p downloads
yt-player-audio/      → Audio-only mode enabled
```

## Summary

The folder-based architecture with dynamic imports provides true isolation between instances while maintaining flexibility and ease of use. Each instance is self-contained and self-configuring, making it impossible to have conflicts between different players.

Key advantages:
- **Zero shared state** between instances
- **Simple setup** with batch file
- **No manual configuration** needed
- **Clear organization** of files
- **Independent updates** and testing
- **Flexible naming** for any use case
- **Automatic module detection** at runtime

This is the recommended approach for running multiple YouTube players in OBS Studio, providing both simplicity and power for any streaming setup.
