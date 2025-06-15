# Phase 02 – Dependency Setup & Tool Management

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
- Log download progress at DEBUG level **at milestones only** (0%, 25%, 50%, 75%, 100%)
- Log successful verification at NORMAL level
- Log errors with retry information

### Download Progress Implementation
- Use a set to track logged percentages
- Log only at milestone percentages (0%, 25%, 50%, 75%, 100%)
- This prevents log spam while still providing progress feedback

## Integration Notes
- The `tools_thread` must start in `script_load()`
- All worker threads (sync, process, etc.) must check `tools_ready` before proceeding
- Use `CREATE_NO_WINDOW` flag on Windows for subprocess calls

## Testing Before Commit
1. Load the script in OBS
2. Verify tools download to `<cache_dir>/tools/`
3. Check that both yt-dlp and FFmpeg executables are present
4. Verify console shows appropriate log messages (5 progress entries max per download)
5. Test that tools work by running them manually from the tools directory
6. Ensure OBS remains responsive during download
7. Verify no log spam (should see only milestone percentages)

## Commit
After successful testing, commit with message:
> *"Add dependency management: auto-download yt-dlp and FFmpeg"*

*After verification, proceed to Phase 03.*
Remember to check **03-OBS_API.md** for threading constraints and **04-Guidelines.md** for style rules.