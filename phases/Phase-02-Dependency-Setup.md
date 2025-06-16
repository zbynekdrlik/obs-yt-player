# Phase 02 – Dependency Setup & Tool Management

## Goal
Implement the dependency management system that downloads and maintains yt-dlp, FFmpeg, and fpcalc (for AcoustID). This phase ensures all required tools are available before any media processing begins.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version (e.g., if current is `1.0.x`, increment to `1.1.0`)
**Remember**: Increment version with EVERY code change during development, not just once per phase.

## Requirements Reference
This phase implements the dependency setup from `02-requirements.md`:
- Auto-download & update tools into `<cache_dir>/tools`
- Retry on failure; set `tools_ready` flag when verified

### Implementation Requirements
- Create a dedicated `tools_thread` that starts at script load
- Download/update **yt-dlp**, **FFmpeg**, and **fpcalc** into `<cache_dir>/tools/`
- Set `tools_ready` flag only after all tools are verified working
- Implement retry mechanism (every 60 seconds on failure)
- **Non-blocking**: OBS must remain responsive during downloads
- Worker threads must check `tools_ready` and re-queue tasks if tools aren't ready

### Key Components to Add:

#### 1. Tool URLs
```python
# yt-dlp
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_WIN = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# FFmpeg
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

# fpcalc (Chromaprint)
FPCALC_URLS = {
    "win32": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-windows-x86_64.zip",
    "darwin": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-macos-x86_64.tar.gz",
    "linux": "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-linux-x86_64.tar.gz"
}
```

#### 2. Tool Download Functions
- `download_ytdlp()` - Simple executable download
- `download_ffmpeg()` - Extract from archive
- `download_fpcalc()` - Extract fpcalc from archive

#### 3. Tool Verification
```python
def verify_tool(tool_path, test_args):
    # Run tool with test arguments
    # Return True if successful
```

Test arguments:
- yt-dlp: `["--version"]`
- FFmpeg: `["-version"]`
- fpcalc: `["-version"]`

#### 4. Thread-Safe State
- Use `state_lock` for `tools_ready` flag
- Check all three tools before setting flag

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

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant (increment MINOR version)
- [ ] Add fpcalc URLs and constants
- [ ] Implement download_fpcalc function
- [ ] Update setup_tools to include fpcalc
- [ ] Add fpcalc to tool verification
- [ ] Test all three tools download correctly
- [ ] Verify extraction works on all platforms
- [ ] Ensure thread safety

## Testing Before Commit
1. Load the script in OBS
2. **Verify correct version appears in logs** (should show incremented version)
3. Verify tools download to `<cache_dir>/tools/`
4. Check that yt-dlp, FFmpeg, and fpcalc executables are present
5. Verify console shows appropriate log messages (5 progress entries max per download)
6. Test that all tools work by running them manually:
   - `yt-dlp --version`
   - `ffmpeg -version`
   - `fpcalc -version`
7. Ensure OBS remains responsive during download
8. Verify no log spam (should see only milestone percentages)
9. Test on fresh system with no existing tools
10. If bugs found, increment version again (PATCH) and retest

## Commit
After successful testing, commit with message:
> *"Add dependency management for yt-dlp, FFmpeg, and fpcalc"*

*After verification, proceed to Phase 03.*