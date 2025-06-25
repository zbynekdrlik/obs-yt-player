# 02‑Requirements (Functional Spec)

This file lists **all features** the final script must implement.  
It is authoritative; later Phase prompts reference this spec.

## Dependencies
- Auto‑download & update **yt‑dlp** and **FFmpeg** into `<cache_dir>/tools` (background thread).  
- Retry on failure; set `tools_ready` flag when verified.

## Playlist Synchronisation
1. Trigger **only** at startup and via *Sync Playlist Now* button.  
2. **NO PERIODIC SYNC** - Script runs on slow LTE internet, sync only on demand.
3. Process videos **one‑by‑one**: download → metadata → normalise → rename.  
4. Remove local files whose IDs left the playlist (skip currently playing).

## Caching & File Management
- Store videos in user‑configurable cache dir (editable text field).  
- **Default cache location**: `<script_directory>/<scriptname>-cache/`
  - Example: `ytfast.py` → `./ytfast-cache/`
  - Allows multiple script instances with separate caches
  - Users can easily modify path in text field
- Sanitise filenames: `<song>_<artist>_<id>_normalized.mp4`.  
- Add `_gf` suffix for videos where Gemini extraction failed.
- Retain only newest duplicate; clean temp `.part` files.

## Metadata Retrieval
- Primary: **Google Gemini API** (required, must be configured with API key).
  - Uses AI with Google Search grounding to extract artist/song
  - Most accurate for complex titles
  - Failed extractions marked with `_gf` for automatic retry
- Fallback: Smart title parser when Gemini unavailable or fails
  - Handles "Artist - Song" and "Song | Artist" patterns
  - Conservative fallback ensures videos always play
- Apply universal song title cleaning to ALL results
- Remove annotations like (Live), [Official], (feat. Artist)
- Log all cleaning transformations for debugging

## Automatic Retry System
- Videos with `_gf` marker are automatically retried on startup
- If Gemini succeeds on retry, file is renamed without marker
- Metadata is updated in cache registry
- Ensures maximum accuracy over time without manual intervention

## Playback Logic
- Scene name == script filename without extension (e.g. `ytfast.py` → scene `ytfast`).  
- Media Source `video`, Text Source `title`.  
- Random no‑repeat playback; handle scene transitions.
- **Transition handling**: Start playback immediately when transitioning TO scene, continue playing until transition completes when leaving scene.
- Support both regular mode and Studio Mode (preview/program).
- **Nested Scene Support** (v3.3.0+): Videos play when scene is included as a source within another scene
  - Recursive detection of scene visibility
  - Respects source visibility settings
  - Supports multiple nesting levels
- **Title display timing**:
  - Clear title 3.5 seconds before song ends (prevents text on black screen during fade)
  - Show title 1.5 seconds after song starts (allows video to establish before text appears)
  - Use OBS timers for precise timing control
  - Smooth opacity transitions (1 second fade duration) using OBS color correction filter

## Audio-Only Mode
- **Optional feature**: Checkbox in script properties to enable/disable
- When enabled, downloads videos with minimal video quality (144p) while preserving best audio quality
- Significantly reduces bandwidth usage and file sizes (80-90% smaller)
- Maintains full audio quality and normalization
- Perfect for audio-only streaming scenarios (radio streams, etc.)
- Logs clearly indicate when audio-only mode is active

## Threading
- All OBS API calls **must** run on main thread (`obs.timer_add`).  
- Separate worker threads/queues for download, normalisation, metadata.
- Gemini reprocess thread runs on startup to retry failed extractions.

## Logging
- Thread-aware logging system with timestamp and script identification.
- Format depends on thread context:
  - Main thread: `[timestamp] message` (OBS prepends script name)
  - Background threads: `[timestamp] [script_name] message` (to identify source)
- OBS output format:
  - Main thread: `[script.py] [timestamp] message`
  - Background threads: `[Unknown Script] [timestamp] [script_name] message`
- This allows distinguishing between multiple script instances in background threads.
- No debug levels or toggles - all messages are logged equally.
- Log script version on startup.
- File-based logging to `{cache_dir}/logs/` with session management.

## Versioning
- Maintain version constant in script (`SCRIPT_VERSION = "X.Y.Z"`)
- Increment version with each development iteration:
  - **MAJOR**: New phases, significant feature additions
  - **MINOR**: Enhancements within existing phases
  - **PATCH**: Bug fixes, minor changes
- Each phase implementation increments MAJOR version
- Log version on script startup

## Default Configuration
- **Default Playlist URL**: `https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U`
- Users can change this in OBS script properties to any valid YouTube playlist

Refer back here from every Phase prompt to ensure no requirement is missed.  
See **03‑OBS_API.md** for environment constraints and **04‑Guidelines.md** for coding style.

*Prev → 01‑Overview.md | Next → 03‑OBS_API.md*