# OBS YouTube Player

A Windows OBS Studio script that plays YouTube playlists with loudness normalization (-14 LUFS) and optional AI metadata extraction.

## Quick Install

Run in **PowerShell**:

```powershell
irm https://raw.githubusercontent.com/zbynekdrlik/obs-yt-player/main/install.ps1 | iex
```

The installer auto-detects OBS, creates the scene/sources, and configures everything.

**Tip:** Close OBS before updating existing installations.

## Features

- **Playback Modes**: Continuous (shuffle), Single (one video), Loop (repeat)
- **Audio Normalization**: All videos normalized to -14 LUFS
- **Audio-Only Mode**: Minimal bandwidth with 144p video + high-quality audio
- **Scene-Aware**: Only plays when the scene is active
- **Gemini AI** (optional): Better artist/song detection from titles

## Configuration

After installation, configure in OBS (Tools → Scripts → ytplay.py):

| Setting | Description |
|---------|-------------|
| Playlist URL | YouTube playlist (public or unlisted) |
| Playback Mode | Continuous, Single, or Loop |
| Audio Only | Enable for minimal video quality |
| Gemini API Key | Optional, for better metadata |

## Scene Setup

If you didn't use the auto-setup, create manually:

1. **Scene** named `ytplay`
2. **Media Source** named `ytplay_video` (uncheck "Local File")
3. **Text Source** named `ytplay_title` (optional, shows current song)

## Multi-Instance

Run the installer again with a different name to create additional instances:
- `worship` → scene `worship`, sources `worship_video`, `worship_title`
- `ambient` → scene `ambient`, sources `ambient_video`, `ambient_title`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Videos not playing | Check scene is active, sources named correctly |
| High CPU | Normal during download/processing |
| Metadata wrong | Add Gemini API key for better detection |
| Update failed | Close OBS first, then run installer |

## Getting Gemini API Key (Optional)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a free API key
3. Paste in script settings

The script works without Gemini - it just provides better metadata parsing.

## License

MIT License
