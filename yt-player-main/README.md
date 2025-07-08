# YouTube Player - Main Instance

This is the main YouTube player instance for OBS Studio.

## Quick Start

1. In OBS, add this script: `yt-player-main/ytfast.py`
2. Create a scene named `ytfast`
3. Configure your playlist URL in script settings

## Creating Additional Instances

Use the helper script in the parent directory:

```bash
cd ..
python setup_new_instance.py main worship
```

This will create a new `yt-player-worship/` instance.

## Configuration

- Scene name: `ytfast`
- Cache location: `yt-player-main/cache/`
- Modules: `yt-player-main/ytfast_modules/`

See `docs/FOLDER_BASED_INSTANCES.md` for more information.
