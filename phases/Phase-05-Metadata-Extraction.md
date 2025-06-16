# Phase 05 – Metadata Extraction

## Goal
Implement metadata extraction using AcoustID audio fingerprinting as the primary method, with YouTube title parsing as a fallback. This provides accurate song and artist information for file naming and display.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements metadata retrieval from `02-requirements.md`:
- Primary: **AcoustID** (`M6o6ia3dKu`)
- Fallback: parse YouTube title; log transformation

## Implementation Details

### 1. Audio Fingerprinting
```python
def get_acoustid_metadata(filepath):
    """Query AcoustID for metadata using audio fingerprint."""
    try:
        # Run fpcalc to generate fingerprint
        cmd = [
            get_fpcalc_path(),
            '-json',
            '-length', '120',  # Analyze first 2 minutes
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None, None
            
        # Parse fingerprint data
        data = json.loads(result.stdout)
        fingerprint = data['fingerprint']
        duration = data['duration']
        
        # Query AcoustID API
        return query_acoustid(fingerprint, duration)
        
    except Exception as e:
        log(f"AcoustID error: {e}", "DEBUG")
        return None, None
```

### 2. AcoustID API Query
```python
def query_acoustid(fingerprint, duration):
    """Query AcoustID API for metadata."""
    url = 'https://api.acoustid.org/v2/lookup'
    params = {
        'client': ACOUSTID_API_KEY,
        'fingerprint': fingerprint,
        'duration': int(duration),
        'meta': 'recordings'
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        # Extract best match
        if data.get('results'):
            result = data['results'][0]
            if result.get('recordings'):
                recording = result['recordings'][0]
                artists = recording.get('artists', [])
                artist = artists[0]['name'] if artists else 'Unknown Artist'
                title = recording.get('title', 'Unknown Title')
                return title, artist
                
    except Exception as e:
        log(f"AcoustID API error: {e}", "DEBUG")
    
    return None, None
```

### 3. YouTube Title Parser
```python
def parse_youtube_title(title):
    """Parse YouTube title to extract artist and song."""
    # Common patterns in YouTube titles
    patterns = [
        (r'^(.*?)\s*-\s*(.*)$', 'hyphen'),  # Artist - Song
        (r'^(.*?)\s*\|\s*(.*)$', 'pipe'),   # Artist | Song
        (r'^(.*?)\s*:\s*(.*)$', 'colon'),   # Artist : Song
    ]
    
    for pattern, name in patterns:
        match = re.match(pattern, title)
        if match:
            artist = match.group(1).strip()
            song = match.group(2).strip()
            
            # Clean up common suffixes
            song = re.sub(r'\s*\([^)]*\)$', '', song)  # Remove (Official Video) etc
            song = re.sub(r'\s*\[[^\]]*\]$', '', song)  # Remove [HD] etc
            
            return song, artist
    
    # If no pattern matches, use title as song name
    return title, "Unknown Artist"
```

### 4. Metadata Selection
```python
def get_metadata(filepath, yt_title):
    """Get song and artist metadata using AcoustID or YouTube title."""
    # Try AcoustID first
    song, artist = get_acoustid_metadata(filepath)
    if song and artist:
        log(f"YT: '{yt_title}' → Song: '{song}', Artist: '{artist}'")
        return song, artist
    
    # Fallback to parsing YouTube title
    song, artist = parse_youtube_title(yt_title)
    log(f"YT: '{yt_title}' → Song: '{song}', Artist: '{artist}'")
    return song, artist
```

### 5. Integration with Process Worker
Update process_videos_worker to call metadata extraction after download:
```python
# In process_videos_worker, after download:
song, artist = get_metadata(temp_path, title)
# Pass metadata to normalization phase
```

## Key Considerations
- fpcalc must be available (installed in Phase 2)
- Use urllib instead of requests (standard library)
- API rate limit: 3 requests/second (free tier)
- Some videos won't have AcoustID matches
- Log which method provided metadata

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement get_acoustid_metadata function
- [ ] Implement query_acoustid with urllib
- [ ] Implement parse_youtube_title function
- [ ] Implement get_metadata wrapper
- [ ] Update process_videos_worker to use metadata
- [ ] Handle all error cases gracefully
- [ ] Test with various video types

## Testing Before Commit
1. Process popular song - verify AcoustID match
2. Process obscure song - verify YouTube fallback
3. Process non-music video - verify graceful handling
4. Test with no network - verify error handling
5. Process classical music - verify multi-artist handling
6. Test API rate limiting with rapid requests
7. Verify metadata extraction works correctly
8. Check logs clearly show metadata source
9. Test YouTube title parser with various formats
10. **Verify version was incremented**

## Commit
After successful testing, commit with message:  
> *"Add AcoustID metadata extraction with YouTube fallback"*

*After verification, proceed to Phase 06.*