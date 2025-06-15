# OBS YouTube Player

An OBS Studio Python script that syncs YouTube playlists, caches videos locally with loudness normalization (-14 LUFS), and plays them randomly via Media Source with metadata display. All processing runs in background threads to keep OBS responsive.

## Features

- **Automatic Playlist Sync**: Fetches and syncs YouTube playlists
- **Local Caching**: Downloads and stores videos locally for reliable playback
- **Audio Normalization**: Normalizes audio to -14 LUFS using FFmpeg
- **Random Playback**: Plays videos randomly without repeats
- **Metadata Display**: Shows song and artist information via Text Source
- **Background Processing**: All heavy tasks run in separate threads
- **OBS Integration**: Seamless integration with OBS Studio scenes and sources

## Requirements

- OBS Studio with Python scripting support
- Internet connection for initial video downloads
- Sufficient disk space for video cache

## Installation

1. Download `ytfast.py` from the releases
2. In OBS Studio, go to Tools → Scripts
3. Click the "+" button and select `ytfast.py`
4. Configure the script properties:
   - Set your YouTube playlist URL
   - Choose a cache directory
   - Enable debug logging if needed

## Usage

1. Create a scene named `ytfast` (or matching your script filename)
2. Add a Media Source named `video` to the scene
3. Add a Text Source named `title` for metadata display
4. Click "Sync Playlist Now" to start downloading videos
5. Switch to your scene to begin random playback

## Project Structure

This project follows a phased development approach. See the `docs/` directory for detailed implementation specifications and the `phases/` directory for step-by-step development guides.

## Development

The project is organized into implementation phases:

1. **Phase 01**: Scaffolding & Project Skeleton
2. **Phase 02**: Playlist Synchronisation
3. **Phase 03**: Video Download & Caching
4. **Phase 04**: Audio Normalisation
5. **Phase 05**: Playback Control & Scene Logic
6. **Phase 06**: Metadata Retrieval
7. **Phase 07**: Final Review & Polish

Each phase builds upon the previous one, ensuring a systematic and maintainable development process.

## License

MIT License - see LICENSE file for details.
