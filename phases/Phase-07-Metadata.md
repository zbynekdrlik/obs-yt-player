# Phase 07 – Metadata Retrieval

## Goal
Add metadata functions using:

1. **Primary**: AcoustID fingerprinting (API key: `M6o6ia3dKu`).
2. **Fallback**: Parse YouTube title.

## Implementation
- `get_metadata(filepath, yt_title)` → returns `(song, artist)`.
- Run in separate thread/queue to avoid blocking.
- Log transformations: *"YT: 'Original Title' → Song: 'Song Name', Artist: 'Artist Name'"*.

## Commit
Suggested commit message:  
> *"Add AcoustID metadata retrieval with YouTube fallback."*

*After verification, proceed to Phase 08.*