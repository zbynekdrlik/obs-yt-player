# Phase 07 – Metadata Retrieval

## Goal
Add metadata functions using:

1. **Primary**: AcoustID fingerprinting (API key: `M6o6ia3dKu`).
2. **Fallback**: Parse YouTube title.

## Requirements Reference
This phase implements the "Metadata Retrieval" section from `02-requirements.md`.

## Implementation
- `get_metadata(filepath, yt_title)` → returns `(song, artist)`.
- Run in separate thread/queue to avoid blocking.
- Log transformations: *"YT: 'Original Title' → Song: 'Song Name', Artist: 'Artist Name'"*.

## Testing Before Commit
1. Test AcoustID API with sample audio files
2. Verify fallback to YouTube title parsing
3. Test various title formats (artist - song, song by artist, etc.)
4. Check metadata queue processing
5. Verify transformation logging
6. Test API error handling

## Commit
After successful testing, commit with message:  
> *"Add AcoustID metadata retrieval with YouTube fallback."*

*After verification, proceed to Phase 08.*