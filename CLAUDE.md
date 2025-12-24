# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OBS YouTube Player is a **Windows-only OBS Studio Python script** that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them via OBS Media Source. Optional Google Gemini AI provides intelligent metadata extraction.

## Development Commands

This is an OBS Python script, not a standalone application. There is no build system, test framework, or linting configured.

**Manual testing workflow:**
1. Load `yt-player-main/ytplay.py` in OBS Studio (Tools → Scripts)
2. Create scene named `ytplay` with sources `ytplay_video` (Media Source) and `ytplay_title` (Text Source)
3. Configure playlist URL in script properties
4. View logs in OBS Script Log window or `cache/logs/` directory

**Creating new instances:**
```cmd
create_new_ytplayer.bat <instance_name>
```

**Updating all instances from template:**
```cmd
update_all_instances.bat
```

## Architecture

### Entry Point and OBS Interface

`ytplay.py` is the main script loaded by OBS. It implements OBS callbacks (`script_load`, `script_unload`, `script_update`, `script_properties`) and orchestrates 5 background worker threads.

### Module Loading System

The script uses dynamic imports for multi-instance support:
- Script name determines module directory: `worship.py` → `worship_modules/`
- All modules use relative imports (`from .module import ...`)
- `config.py` auto-detects script name and derives scene/source names

### Threading Model

```
Main Thread (OBS)
├── playback_controller timer (1s interval) - manages playback state machine
│
Background Threads (daemon):
├── tools_setup_worker     - downloads yt-dlp + FFmpeg on first run
├── playlist_sync_worker   - fetches playlist via yt-dlp (on-demand, not periodic)
├── process_videos_worker  - downloads videos, extracts metadata, normalizes audio
└── reprocess_worker       - retries Gemini extraction for _gf marked files
```

### State Management

`state.py` provides thread-safe global state with a single lock (`_state_lock`). All state access goes through accessor functions. Key state categories:
- Configuration (playlist URL, cache dir, playback mode)
- System flags (tools_ready, scene_active, is_playing)
- Data structures (cached_videos dict, played_videos list, video_queue)

### Playback State Machine

`playback_controller.py` runs a 1-second timer that:
1. Checks shutdown/source availability
2. Verifies scene is active (including nested scenes)
3. Monitors media state via `obs_source_media_get_state()`
4. Delegates to `state_handlers.py` for state-specific logic

Media states handled: `PLAYING`, `ENDED`, `STOPPED`, `NONE`

### Video Processing Pipeline

```
playlist.py (fetch IDs) → video_queue → download.py (yt-dlp)
    → metadata.py (Gemini or title parsing) → normalize.py (FFmpeg loudnorm)
    → cache.py (add to cached_videos)
```

### Metadata Extraction

Two-tier system in `metadata.py`:
1. **Gemini AI** (`gemini_metadata.py`): Uses Gemini 2.5 Flash with Google Search grounding. Failed extractions marked with `_gf` suffix for retry.
2. **Title parsing** (fallback): Regex patterns for "Artist - Song" and "Song | Artist" formats.

### OBS Source Control

- `media_control.py`: Updates Media Source path, gets playback state/time/duration
- `opacity_control.py`: Manages fade effects via color_filter on Text Source
- `title_manager.py`: Schedules title show (1.5s after start) and hide (3.5s before end)
- `scene.py`: Detects active scene including nested scene sources, handles transitions

### File Naming Convention

```
{song}_{artist}_{videoId}_normalized.mp4      # Successfully processed
{song}_{artist}_{videoId}_normalized_gf.mp4   # Gemini failed, will retry
{videoId}_temp.mp4                            # Temporary download
```

### Multi-Instance Architecture

Each instance is a complete folder copy with renamed script and modules:
- `yt-player-worship/worship.py` + `worship_modules/`
- Source names auto-prefixed: `worship_video`, `worship_title`
- Complete cache/state isolation between instances

## Key Constants (config.py)

| Constant | Value | Purpose |
|----------|-------|---------|
| `PLAYBACK_CHECK_INTERVAL` | 1000ms | Playback controller timer rate |
| `MAX_RESOLUTION` | 1440 | Maximum video height for downloads |
| `DOWNLOAD_TIMEOUT` | 600s | yt-dlp timeout |
| `NORMALIZE_TIMEOUT` | 300s | FFmpeg timeout |
| `TITLE_FADE_DURATION` | 1000ms | Opacity transition time |

## Module Responsibilities

| Module | Primary Responsibility |
|--------|----------------------|
| `playback_controller.py` | Main loop, video start/stop, source verification |
| `state_handlers.py` | Media state handling, loop restart scheduling |
| `scene.py` | Scene activation detection, nested scene support |
| `media_control.py` | OBS media/text source manipulation |
| `download.py` | yt-dlp video downloading with progress |
| `normalize.py` | FFmpeg 2-pass loudnorm processing |
| `gemini_metadata.py` | Google Gemini API calls with retry logic |
| `cache.py` | Cache scanning, cleanup of removed playlist items |
| `state.py` | Thread-safe state with accessor functions |

## Important Patterns

**Circular import avoidance**: Many modules import from each other. Use local imports inside functions when needed:
```python
def some_function():
    from .playback_controller import start_next_video
    start_next_video()
```

**OBS timer management**: Timers store callback references in module-level variables and must be explicitly removed:
```python
_my_timer = None
def my_callback():
    global _my_timer
    obs.timer_remove(_my_timer)
    _my_timer = None
    # do work
```

**Windows-specific subprocess**: All subprocess calls use hidden console windows:
```python
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE
```
