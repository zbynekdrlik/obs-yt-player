# Migration Notes for v3.5.0

## Files to be removed after migration:
- ytfast.py (already removed)
- ytfast_modules/ (entire directory)

## Migration Steps:
1. All modules from ytfast_modules/ have been copied to ytplay_modules/
2. Updated modules (config.py, logger.py, scene.py, state.py) use new architecture
3. Other modules remain unchanged but now live in shared directory

## Breaking Changes:
- Default script is now ytplay.py
- Modules directory is now ytplay_modules/
- Empty default playlist URL

## For existing users:
- Option 1: Keep ytfast.py name, just rename modules folder
- Option 2: Rename to ytplay.py and update scene name