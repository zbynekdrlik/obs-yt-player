# Migration Notes for v3.5.x

## Known Issues

### Multiple Script Instances (v3.5.9)
**Issue**: Running multiple script instances simultaneously (e.g., ytplay.py and ytfast.py) can cause configuration warnings and logging issues due to shared state.

**Symptoms**:
- Wrong script names in logs
- Configuration warnings showing incorrect values
- Scripts showing each other's state

**Workaround**: 
- Use only one script instance at a time
- Or restart OBS when switching between scripts

**Fix planned for v3.6.0**: Refactor state module to support true multi-instance isolation.

## Migration from v3.4.x

The common modules architecture in v3.5.x brings changes:

1. **Script Name**: Default script is now `ytplay.py` (was `ytfast.py`)
2. **Modules Location**: All scripts share `ytplay_modules/` directory
3. **No Default Playlist**: You must configure your playlist URL

### Option 1: Keep using ytfast
- Copy `ytplay.py` to `ytfast.py`
- Your existing setup continues working

### Option 2: Switch to ytplay
- Rename your OBS scene from `ytfast` to `ytplay`
- Update any scene references
- Configure your playlist URL
