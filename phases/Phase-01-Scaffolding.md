# Phase 01 – Scaffolding & Project Skeleton

## Goal
Create the initial `ytfast.py` OBS script skeleton **only**. This establishes the foundation with proper structure, constants, and OBS integration.

## Version Increment
**This is the initial version** → Start at `1.0.0`
**Remember**: After this initial version, increment version with EVERY code change, not just once per phase.

## Requirements Reference
This phase sets up the foundation for all requirements in `02-requirements.md`.

## Components to Implement

### 1. Module-Level Constants
```python
SCRIPT_VERSION = "1.0.0"  # Initial version
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=..."
SCENE_NAME = os.path.splitext(os.path.basename(__file__))[0]
DEFAULT_CACHE_DIR = os.path.join(script_dir, f"{SCENE_NAME}-cache")
# Other constants as per requirements
```

### 2. Global Variables
- Threading infrastructure (locks, queues, events)
- State flags (tools_ready, scene_active, etc.)
- Data structures (cached_videos, playlist_ids)
- Script properties variables

### 3. OBS Script Properties
- Playlist URL text field (editable)
- Cache Directory text field (editable)
- Sync Now button

### 4. Core Functions
- `script_description()` - Return docstring ≤400 chars
- `script_properties()` - Define UI properties
- `script_defaults()` - Set default values
- `script_update()` - Handle property changes
- `script_load()` - Initialize script
- `script_unload()` - Cleanup
- `log()` - Logging helper with timestamps (single level)

### 5. Placeholder Workers
- Empty thread starter functions
- Comments indicating future implementation

## Key Implementation Points
- Follow output rules from `04-guidelines.md`
- Respect OBS constraints from `03-obs_api.md`
- **Dynamic naming**: Scene/cache based on script filename
- **Editable cache path**: Text field for easy customization
- Thread-safe design from the start
- **Simple logging**: No debug levels, just timestamped messages

## Implementation Checklist
- [ ] Set SCRIPT_VERSION to "1.0.0"
- [ ] Add all required constants
- [ ] Define global variables
- [ ] Implement OBS callback functions
- [ ] Add property definitions (no debug checkbox)
- [ ] Create simple logging helper
- [ ] Add thread starter placeholders
- [ ] Include proper docstring
- [ ] Test all functionality

## Testing Before Commit
1. Load script in OBS Scripts menu
2. **Verify version shows as 1.0.0 in logs**
3. Verify all properties appear correctly
4. Check cache directory field is editable
5. Verify script loads without errors
6. Ensure default values are set
7. Check default cache: `<location>/<n>-cache`
8. Test property persistence after restart
9. Verify scene name matches script name
10. Check log output format: `[script_name] [timestamp] message`
11. If any issues found during testing, increment version (e.g., to 1.0.1) and retest

## Commit
After successful testing, commit with message:  
> *"Initial scaffolding: OBS properties & basic structure"*

*After verification, proceed to Phase 02.*