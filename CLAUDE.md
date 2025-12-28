# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OBS YouTube Player is a **Windows-only OBS Studio Python script** that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them via OBS Media Source. Optional Google Gemini AI provides intelligent metadata extraction.

## Development Commands

**Install dependencies:**
```bash
uv sync --dev
```

**Run tests:**
```bash
uv run pytest tests/ -v
```

**Run linting:**
```bash
uv run ruff check .
uv run ruff format --check .
```

**Run type checking:**
```bash
uv run mypy yt-player-main/ytplay_modules
```

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

## Branch Strategy

**Single development branch**: Always use `dev` as the only feature/fix branch.

- Work on `dev` branch for all changes
- Create PR from `dev` to `main` when ready
- Delete `dev` after merge, recreate for next task
- Never create multiple feature branches (no `fix/xxx`, `feature/xxx`)

**CRITICAL - Claude restrictions:**
- **NEVER commit or push directly to `main`** - main branch is protected
- **NEVER merge PRs** - only the user can merge PRs, Claude must wait for user approval
- Always work on `dev` branch and create PRs for user review

**Before creating PR to main:**
- `install.ps1` line 22: `$RepoBranch = "main"` (not "dev")
- `yt-player-main/VERSION`: Must NOT contain "-dev" suffix (e.g., use "4.3.3" not "4.3.3-dev.1")
- CI will reject PRs that violate these rules

This project has one developer using Claude as a tool - not a multi-developer workflow.

## CI Verification Requirements

**CRITICAL: Always verify CI passes before delivering code to the user.**

After pushing changes:
1. Run `gh run list --limit 3` to check CI status
2. Wait for all jobs to complete (use `gh run view <id> --json status,conclusion`)
3. If any job fails, fix immediately before asking user to test

**Quality thresholds - always be stricter, never lighter:**
- Never relax test coverage thresholds
- Never skip or disable failing tests
- Never ignore linting/type errors
- Add new CI checks when gaps are discovered (e.g., PowerShell syntax checking was added after a syntax error reached the user)

**CI includes:**
- Python linting (Ruff)
- Type checking (Mypy)
- PowerShell syntax validation
- Security scanning (Bandit)
- Tests across Python 3.9-3.13 on Ubuntu and Windows

Delivering broken code wastes user time and erodes trust. When in doubt, add more validation, not less.

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
| `playback_controller.py` | Main 1s timer loop, video start/stop, source verification |
| `state_handlers.py` | Media state handling (PLAYING/ENDED/STOPPED), loop restart |
| `state.py` | Thread-safe global state with `_state_lock` and accessors |
| `scene.py` | Scene activation detection, nested scene support |
| `media_control.py` | OBS media/text source manipulation |
| `download.py` | yt-dlp video downloading with progress tracking |
| `normalize.py` | FFmpeg 2-pass loudnorm processing (-14 LUFS) |
| `gemini_metadata.py` | Google Gemini API calls with retry logic |
| `metadata.py` | Two-tier metadata extraction (Gemini + regex fallback) |
| `cache.py` | Cache scanning, cleanup of removed playlist items |
| `playlist.py` | Playlist sync worker, yt-dlp flat-playlist fetching |
| `video_selector.py` | Random selection with no-repeat logic |
| `play_history.py` | Persistent play tracking across restarts (JSON) |
| `reprocess.py` | Automatic Gemini retry for `_gf` marked files |
| `opacity_control.py` | Title fade effects via OBS color filter |
| `title_manager.py` | Title show/hide timing (1.5s after start, 3.5s before end) |
| `tools.py` | yt-dlp + FFmpeg auto-download and verification |
| `utils.py` | YouTube ID validation, filename sanitization |
| `logger.py` | Dual logging (OBS console + file-based) |
| `config.py` | Dynamic configuration, scene/source name derivation |
| `playback.py` | Video processing worker thread |

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

## Thread Safety

All shared state in `state.py` is protected by `_state_lock`:

```python
# Reading state (returns copy to prevent external modification)
def get_cached_videos():
    with _state_lock:
        return _cached_videos.copy()

# Writing state (modify inside lock)
def add_cached_video(video_id, info):
    with _state_lock:
        _cached_videos[video_id] = info
```

**Key rules:**
- Never hold the lock while doing I/O (file reads, API calls)
- Use accessor functions, never access `_variables` directly from other modules
- Copy data before returning from accessors to prevent race conditions
- The `play_history.py` persistence happens outside the lock to avoid deadlock

## Remote Testing via SSH

See `docs/WINDOWS_TESTING.md` for comprehensive testing guide. Key patterns below.

### SSH Connection
```bash
# Use sshpass for non-interactive SSH (credentials in TARGETS.md)
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no USER@IP "command"

# Copy files
sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no file USER@IP:"c:/path/dest"
```

### Complex PowerShell Commands
**Escaping is problematic over SSH.** For complex scripts, write to file and execute:
```bash
# Write script locally, copy to Windows, execute
cat > /tmp/script.ps1 << 'EOF'
# PowerShell code here
EOF
sshpass -p 'PASSWORD' scp /tmp/script.ps1 USER@IP:"c:/Users/USER/script.ps1"
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -ExecutionPolicy Bypass -File c:\Users\USER\script.ps1'
```

### Starting GUI Apps (OBS) via SSH
GUI apps started via SSH run in session 0 (invisible). Use PowerShell Task Scheduler:
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "
$action = New-ScheduledTaskAction -Execute \"c:\\path\\to\\obs.exe\" -Argument \"-p\"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(5)
$principal = New-ScheduledTaskPrincipal -UserId \"USERNAME\" -LogonType Interactive
Register-ScheduledTask -TaskName \"StartOBS\" -Action $action -Trigger $trigger -Principal $principal -Force
Start-ScheduledTask -TaskName \"StartOBS\"
"'
```

**CRITICAL for portable OBS:** Always use `-p` flag: `obs64.exe -p`

### Portable OBS Paths
| Component | Path |
|-----------|------|
| Executable | `{OBS_PATH}\bin\64bit\obs64.exe` |
| Config | `{OBS_PATH}\config\obs-studio\` |
| Logs | `{OBS_PATH}\config\obs-studio\logs\` |
| WebSocket config | `{OBS_PATH}\config\obs-studio\plugin_config\obs-websocket\config.json` |

### Renamed OBS Executables
When OBS is renamed (e.g., `obs64.exe` → `cg.exe`) for task manager clarity, updates break it because OBS downloads a new `obs64.exe` but the renamed exe stays outdated.

**Solution:** The installer automatically creates a launcher batch file (e.g., `cg.bat`) that:
1. Checks if `obs64.exe` exists (OBS auto-updated)
2. Replaces the renamed exe with the updated `obs64.exe`
3. Starts the renamed OBS in portable mode

**Manual setup** (if installer didn't run or for existing installations):
```batch
REM Create {name}.bat in OBS root folder with this content:
@echo off
setlocal
set "CUSTOM_EXE=%~n0"
cd /d "%~dp0bin\64bit"
if exist "obs64.exe" (
    if exist "%CUSTOM_EXE%.exe" del /f "%CUSTOM_EXE%.exe"
    move "obs64.exe" "%CUSTOM_EXE%.exe"
)
start "" "%CUSTOM_EXE%.exe" -p
```
The batch filename determines the exe name: `cg.bat` → runs `cg.exe`

See `scripts/obs_launcher_template.bat` for documented template.

### Non-Interactive Installer Testing
Set environment variables before running installer:
```powershell
[Environment]::SetEnvironmentVariable("YTPLAY_AUTO_CONFIRM", "1", "Process")
[Environment]::SetEnvironmentVariable("YTPLAY_OBS_PATH", "c:\path\to\obs", "Process")
[Environment]::SetEnvironmentVariable("YTPLAY_PLAYLIST_URL", "1", "Process")
$env:YTPLAY_AUTO_CONFIRM = "1"
$env:YTPLAY_OBS_PATH = "c:\path\to\obs"
& c:\path\to\install.ps1
```

### WebSocket Testing
Use `scripts/test_websocket.ps1` or quick check:
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Test-NetConnection localhost -Port 4459 | Select TcpTestSucceeded"'
```

### Common Operations
```bash
# Check if OBS running (may be renamed, e.g., cg.exe)
sshpass -p 'P' ssh U@IP 'powershell -Command "Get-Process obs64,cg -EA SilentlyContinue"'

# Kill OBS
sshpass -p 'P' ssh U@IP 'powershell -Command "Stop-Process -Name obs64,cg -Force -EA SilentlyContinue"'

# Read OBS logs (portable)
sshpass -p 'P' ssh U@IP "powershell -Command \"Get-ChildItem 'c:\\path\\logs' | Sort LastWriteTime -Desc | Select -First 1 | % { Get-Content \$_.FullName -Tail 50 }\""
```
