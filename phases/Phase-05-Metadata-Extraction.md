# Phase 05 – Metadata Extraction

## Goal
Implement metadata extraction using AcoustID audio fingerprinting as the primary method, with YouTube title parsing as a fallback. This provides accurate song and artist information for file naming and display.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.2.0` → `1.3.0`)

## Requirements Reference
This phase implements metadata retrieval from `02-requirements.md`:
- Primary: **AcoustID** (`M6o6ia3dKu`)
- Fallback: parse YouTube title; log transformation

## Implementation Details

### 1. Tool Management Updates
Add fpcalc (Chromaprint) to the tool download system:
- Windows: `https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-windows-x86_64.zip`
- macOS: `https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-macos-x86_64.tar.gz`
- Linux: `https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-linux-x86_64.tar.gz`

### 2. Audio Fingerprinting (`get_acoustid_metadata`)
```python
def get_acoustid_metadata(filepath):
    # 1. Run fpcalc to generate fingerprint
    # 2. Parse duration and fingerprint from output
    # 3. Query AcoustID API
    # 4. Parse best match from results
    # 5. Return (song, artist) or (None, None)
```

### 3. AcoustID API Request
- URL: `https://api.acoustid.org/v2/lookup`
- Parameters:
  - `client`: API key (`M6o6ia3dKu`)
  - `fingerprint`: From fpcalc
  - `duration`: Audio duration
  - `meta`: "recordings"
- Parse JSON response for best match

### 4. YouTube Title Parser (existing)
Improve pattern matching:
- Detect "Artist - Song" vs "Song | Artist" patterns
- Handle "feat.", "ft.", "&" in artist names
- Remove suffixes like "(Official Video)", "[HD]", etc.

### 5. Metadata Selection Logic
```python
def get_metadata(filepath, yt_title):
    # Try AcoustID first
    song, artist = get_acoustid_metadata(filepath)
    if song and artist:
        log(f"AcoustID: '{artist}' - '{song}'")
        return song, artist
    
    # Fallback to YouTube title
    song, artist = parse_youtube_title(yt_title)
    log(f"YouTube title: '{artist}' - '{song}'")
    return song, artist
```

## Key Considerations
- fpcalc requires audio file, not video URL
- API rate limit: 3 requests/second (free tier)
- Network timeout handling (5 seconds)
- Some videos won't have AcoustID matches
- Log which method provided metadata

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Add fpcalc URLs and download logic
- [ ] Implement fpcalc execution and parsing
- [ ] Implement AcoustID API call
- [ ] Parse API response for best match
- [ ] Improve YouTube title parser
- [ ] Update get_metadata logic
- [ ] Add appropriate logging
- [ ] Handle all error cases

## Testing Before Commit
1. Process popular song - verify AcoustID match
2. Process obscure song - verify YouTube fallback
3. Process non-music video - verify graceful handling
4. Test with no network - verify error handling
5. Process classical music - verify multi-artist handling
6. Test API rate limiting with rapid requests
7. Verify fpcalc works on all platforms
8. Check logs clearly show metadata source
9. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add AcoustID metadata extraction with YouTube fallback"*

*After verification, proceed to Phase 06.*