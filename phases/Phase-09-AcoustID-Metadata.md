# Phase 09 – AcoustID Metadata Implementation

## Goal
Implement proper AcoustID audio fingerprinting to accurately identify song and artist metadata, replacing the current YouTube title parsing fallback with a more reliable primary method.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., `1.1.0` → `1.2.0`)

## Requirements Reference
This phase implements the metadata retrieval requirement from `02-requirements.md`:
- Primary: **AcoustID** (`M6o6ia3dKu`)
- Fallback: parse YouTube title (already implemented)

## Implementation Details

### 1. Download fpcalc Tool
- Add fpcalc to the tools download system
- Platform-specific URLs:
  - Windows: Extract from Chromaprint releases
  - macOS/Linux: Download appropriate binary
- Verify tool works with test fingerprint

### 2. Audio Fingerprinting Process
- Extract audio fingerprint using fpcalc
- Pass the video file path to fpcalc
- Capture duration and fingerprint from output
- Handle errors gracefully (corrupted audio, etc.)

### 3. AcoustID API Integration
- Use the provided API key: `M6o6ia3dKu`
- Make HTTP request to AcoustID web service
- Include fingerprint and duration in request
- Parse JSON response for recordings

### 4. Metadata Extraction
- Extract best match from AcoustID results
- Prioritize results with higher scores
- Get artist name(s) and track title
- Handle multiple artists appropriately
- Return None, None if no good match found

### 5. Integration with Existing Pipeline
- Update `get_acoustid_metadata()` function
- Maintain existing fallback to YouTube title parsing
- Log when AcoustID succeeds vs falls back
- Cache fingerprints to avoid re-processing (optional)

## Key Considerations
- fpcalc must be in tools directory
- API rate limits (3 requests per second for free tier)
- Network timeouts and error handling
- Some videos may not have AcoustID matches
- Log the metadata source (AcoustID vs YouTube title)

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Add fpcalc download URLs
- [ ] Implement fpcalc download function
- [ ] Add fpcalc to tool verification
- [ ] Implement fingerprint generation
- [ ] Implement AcoustID API call
- [ ] Parse API response properly
- [ ] Update get_acoustid_metadata function
- [ ] Test with various music videos
- [ ] Handle edge cases gracefully

## Testing Before Commit
1. Process a popular song - verify AcoustID finds correct metadata
2. Process an obscure song - verify fallback to YouTube title works
3. Test with non-music video - should fallback gracefully
4. Verify fpcalc tool downloads on fresh install
5. Test API error handling (disconnect network briefly)
6. Check logs show "AcoustID: Artist - Song" vs "YouTube title: Artist - Song"
7. Verify no impact on processing speed
8. Test with various audio formats
9. **Verify version was incremented in script**

## API Response Example
```json
{
  "status": "ok",
  "results": [{
    "score": 0.95,
    "recordings": [{
      "artists": [{"name": "Artist Name"}],
      "title": "Song Title"
    }]
  }]
}
```

## Commit
After successful testing, commit with message:  
> *"Add AcoustID audio fingerprinting for accurate metadata"*

*After verification, proceed to next phase.*