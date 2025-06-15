# 06-Phase 02 – Dependency Setup & Tool Management

## Goal
Implement the dependency management system that downloads and maintains yt-dlp and FFmpeg. This phase ensures all required tools are available before any media processing begins.

### Implementation Requirements
- Create a dedicated `tools_thread` that starts at script load
- Download/update **yt-dlp** and **FFmpeg** into `<cache_dir>/tools/`
- Set `tools_ready` flag only after both tools are verified working
- Implement retry mechanism (every 60 seconds on failure)
- **Non-blocking**: OBS must remain responsive during downloads
- Worker threads must check `tools_ready` and re-queue tasks if tools aren't ready

### Key Components to Add:
1. Tool download functions for yt-dlp and FFmpeg
2. Platform-specific FFmpeg binary selection (Windows/Mac/Linux)
3. Tool verification (check if executables work)
4. Thread-safe `tools_ready` flag with proper locking
5. Retry logic with exponential backoff
6. Progress logging without spam

### Logging Requirements
- Log once when starting tool setup:
  > "Waiting for tools to be ready. Please be patient, downloading FFmpeg may take several minutes."
- Log download progress at DEBUG level
- Log successful verification at NORMAL level
- Log errors with retry information

## Integration Notes
- The `tools_thread` must start in `script_load()`
- All worker threads (sync, normalize, etc.) must check `tools_ready` before proceeding
- Use `CREATE_NO_WINDOW` flag on Windows for subprocess calls

## Commit
Suggested commit message:
> *"Add dependency management: auto-download yt-dlp and FFmpeg"*

*After verification, proceed to Phase 03 (previously Phase 02).*
Remember to check **03-OBS_API.md** for threading constraints and **04-Guidelines.md** for style rules.