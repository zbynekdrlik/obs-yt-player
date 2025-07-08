# Folder-Based Multi-Instance Setup

## Overview

This document describes the **folder-based approach** for running multiple YouTube player instances in OBS Studio. Instead of complex state isolation within shared modules, each player instance lives in its own completely separate folder.

## Why This Approach?

### Problems with State Isolation
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

## Directory Structure

```
obs-scripts/
├── yt-player-main/              # Main player instance
│   ├── ytfast.py                # Main script
│   ├── ytfast_modules/          # Module directory
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration with SCENE_NAME
│   │   ├── downloader.py
│   │   ├── metadata.py
│   │   ├── player.py
│   │   └── ...
│   └── cache/                   # Cache directory
│
├── yt-player-worship/           # Worship player instance
│   ├── ytworship.py             # Renamed main script
│   ├── ytworship_modules/       # Renamed module directory
│   │   └── ...                  # All modules with updated imports
│   └── cache/
│
├── yt-player-kids/              # Kids player instance
│   ├── ytkids.py
│   ├── ytkids_modules/
│   │   └── ...
│   └── cache/
│
└── setup_new_instance.py        # Helper script for creating instances
```

## Creating a New Instance

### Method 1: Using the Helper Script (Recommended)

```bash
python setup_new_instance.py main worship
```

This will:
1. Copy `yt-player-main/` to `yt-player-worship/`
2. Rename `ytfast.py` to `ytworship.py`
3. Rename `ytfast_modules/` to `ytworship_modules/`
4. Update all imports from `ytfast_modules` to `ytworship_modules`
5. Update `SCENE_NAME` from "ytfast" to "ytworship"
6. Clean the cache directory

### Method 2: Manual Setup

1. **Copy the entire folder**
   ```bash
   cp -r yt-player-main/ yt-player-worship/
   ```

2. **Rename the main script**
   ```bash
   cd yt-player-worship
   mv ytfast.py ytworship.py
   ```

3. **Rename the modules folder**
   ```bash
   mv ytfast_modules/ ytworship_modules/
   ```

4. **Update imports in main script**
   - Open `ytworship.py`
   - Replace all `from ytfast_modules` with `from ytworship_modules`

5. **Update SCENE_NAME in config.py**
   - Open `ytworship_modules/config.py`
   - Change `SCENE_NAME = "ytfast"` to `SCENE_NAME = "ytworship"`

6. **Clean cache directory**
   ```bash
   rm -rf cache/*
   ```

## OBS Setup

For each player instance:

1. **Add the script to OBS**
   - Scripts → + → Add `yt-player-worship/ytworship.py`

2. **Create the scene**
   - Create a new scene named exactly as configured (e.g., "ytworship")

3. **Configure the script**
   - Set the YouTube playlist URL
   - Configure other settings as needed

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Folder | `yt-player-{name}/` | `yt-player-worship/` |
| Main Script | `yt{name}.py` | `ytworship.py` |
| Modules Folder | `yt{name}_modules/` | `ytworship_modules/` |
| Scene Name | `yt{name}` | `ytworship` |

## Best Practices

1. **Keep a template instance**
   - Maintain `yt-player-main/` as your template
   - Update and test changes there first
   - Copy to other instances after testing

2. **Version control**
   - Consider adding specific player folders to `.gitignore`
   - Or commit them if you want version control for all instances

3. **Backup before updates**
   - When updating an instance, backup the folder first
   - Easy rollback if something breaks

4. **Consistent naming**
   - Use clear, descriptive names for instances
   - Avoid special characters or spaces

## Migration from Single-Script Setup

If you're currently using the old single-script approach:

1. Create `yt-player-main/` directory
2. Move `ytfast.py` into it
3. Move `ytfast_modules/` into it
4. Update OBS to load script from new location
5. Test that everything works
6. Create additional instances as needed

## Troubleshooting

### Script not loading in OBS
- Check that all file paths are correct
- Ensure imports match the folder names
- Verify SCENE_NAME matches OBS scene

### Import errors
- Module folder name must match imports
- Check for typos in import statements
- Ensure `__init__.py` exists in modules folder

### Wrong scene detected
- Check `SCENE_NAME` in `config.py`
- Scene name in OBS must match exactly

### Cache issues
- Each instance has its own cache folder
- Clear cache when copying instances
- Check folder permissions

## Advantages Over State Isolation

1. **No threading context issues**
   - Each instance runs in complete isolation
   - No need for complex context management

2. **Simple import paths**
   - Each instance has its own modules
   - No path conflicts possible

3. **Easy updates**
   - Update one instance without affecting others
   - Test changes safely

4. **Clear file organization**
   - Know exactly which files belong to which player
   - Easy to backup or remove instances

## Example Use Cases

### Multiple Playlist Types
```
yt-player-main/       → General music playlist
yt-player-worship/    → Worship music playlist  
yt-player-kids/       → Kids content playlist
yt-player-ambient/    → Background/ambient playlist
```

### Different Configurations
```
yt-player-1080p/      → High quality downloads
yt-player-720p/       → Medium quality downloads
yt-player-audio/      → Audio-only mode
```

### Testing vs Production
```
yt-player-prod/       → Production instance
yt-player-test/       → Testing new features
yt-player-dev/        → Development instance
```

## Summary

The folder-based approach trades a small amount of disk space (duplicated module files) for massive gains in simplicity, reliability, and maintainability. Each player instance is completely self-contained, making it impossible to have state conflicts or import issues between instances.

This is the recommended approach for running multiple YouTube players in OBS Studio.