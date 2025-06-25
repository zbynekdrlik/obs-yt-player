# Migration Notes for v3.5.0 → v3.6.0

## v3.6.0 (True Multi-Instance Support)

### What's Fixed
- **Complete state isolation between script instances**
  - Each script now maintains its own isolated state using script path as unique identifier
  - No more wrong script names in logs
  - No more configuration warnings showing incorrect values
  - Scripts no longer access each other's playlist URLs or settings

### Technical Implementation
- State module refactored to use dictionary-based isolation
- Script path used as unique key for each instance
- Background threads properly inherit script context
- Thread-local storage ensures correct script context in all threads

### Breaking Changes
- None - existing scripts will continue to work as before
- All modules updated to use new state mechanism transparently

### For Developers
- Background threads must call `set_thread_script_context(script_path)` at start
- Use `get_current_script_path()` to retrieve current script context
- State cleanup happens automatically on script unload

## v3.5.0 → v3.5.9 (Common Modules Architecture)

### Major Changes
- **Script Rename**: Default script changed from `ytfast.py` to `ytplay.py`
- **Modules Directory**: Changed from `<scriptname>_modules/` to shared `ytplay_modules/`
- **Default Playlist**: Now empty (was a specific URL) - users must configure

### New Features
- Shared modules architecture - update once, all scripts benefit
- Configuration warnings at bottom of UI
- Improved UI layout with consistent dropdowns
- Multiple crash fixes (v3.5.7-v3.5.9)

### Multi-Instance Setup
1. Copy `ytplay.py` to new name (e.g., `yt_worship.py`)
2. Each script automatically:
   - Uses its filename as the scene name
   - Creates its own cache directory
   - Maintains separate configuration
   - Identifies itself in logs (v3.6.0: now works correctly)

### Known Issues (Fixed in v3.6.0)
- ~~Multiple scripts have state contamination when run simultaneously~~
- ~~Wrong script names appear in logs~~
- ~~Scripts show each other's configuration values~~
