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

## Directory Structure

```
obs-scripts/
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
│   ├── ytworship.py             # Instance script
│   ├── ytworship_modules/       # Instance modules
│   │   └── ...                  # All modules with updated imports
│   └── cache/
│
├── yt-player-kids/              # Kids player instance
│   ├── ytkids.py
│   ├── ytkids_modules/
│   └── cache/
│
└── create_new_ytplayer.bat      # Windows batch file for instances
```

## Creating a New Instance

### Using the Windows Batch File

```cmd
create_new_ytplayer.bat worship
```

This will:
1. Copy `yt-player-main/` to `yt-player-worship/`
2. Rename `ytplay.py` to `ytworship.py`
3. Rename `ytplay_modules/` to `ytworship_modules/`
4. Update all imports automatically
5. Clean the cache directory
6. Display setup instructions

### Manual Setup (Advanced Users)

1. **Copy the entire folder**
   ```bash
   cp -r yt-player-main/ yt-player-worship/
   ```

2. **Rename the main script**
   ```bash
   cd yt-player-worship
   mv ytplay.py ytworship.py
   ```

3. **Rename the modules folder**
   ```bash
   mv ytplay_modules/ ytworship_modules/
   ```

4. **Update imports using PowerShell**
   ```powershell
   # Update main script
   (Get-Content ytworship.py) -replace 'from ytplay_modules', 'from ytworship_modules' | Set-Content ytworship.py
   
   # Update all module files
   Get-ChildItem -Path ytworship_modules -Filter *.py -Recurse | ForEach-Object {
       (Get-Content $_.FullName) -replace 'from ytplay_modules', 'from ytworship_modules' | Set-Content $_.FullName
   }
   ```

5. **Clean cache directory**
   ```bash
   rm -rf cache/*
   ```

## OBS Setup

For each player instance:

1. **Add the script to OBS**
   - Scripts → + → Add `yt-player-worship/ytworship.py`

2. **Create the scene**
   - Scene name = script name (without .py)
   - Example: `ytworship.py` → Scene: `ytworship`

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
| `ytworship.py` | `ytworship` | Worship music |
| `ytkids.py` | `ytkids` | Kids content |
| `ytambient.py` | `ytambient` | Background music |
| `remixes.py` | `remixes` | Remix playlist |

## How It Works

1. **Dynamic Configuration**
   - `config.py` automatically detects the script name
   - Scene name is derived from script filename
   - No hardcoded paths or names

2. **Module Isolation**
   - Each instance has its own modules folder
   - Import statements reference instance-specific modules
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
- Verify no syntax errors in imports

### Import errors
```
ModuleNotFoundError: No module named 'ytworship_modules'
```
- Module folder name must match imports exactly
- Check for typos in import statements
- Ensure `__init__.py` exists in modules folder

### Wrong scene detected
- Scene name comes from script filename
- `ytworship.py` → Scene must be named `ytworship`
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

2. **Manual migration steps**
   - Create `yt-player-main/` directory
   - Move `ytfast.py` to `yt-player-main/ytplay.py`
   - Move `ytfast_modules/` to `yt-player-main/ytplay_modules/`
   - Move cache directory to `yt-player-main/cache/`
   - Update imports in all Python files
   - Update OBS to load from new location

3. **Update OBS script paths**
   - Remove old script references
   - Add new scripts from folders

4. **Verify functionality**
   - Test each instance
   - Check logs for errors

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

## Summary

The folder-based architecture provides true isolation between instances while maintaining flexibility and ease of use. Each instance is self-contained, making it impossible to have conflicts between different players.

Key advantages:
- **Zero shared state** between instances
- **Simple setup** with batch file
- **Clear organization** of files
- **Independent updates** and testing
- **Flexible naming** for any use case

This is the recommended approach for running multiple YouTube players in OBS Studio.
