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
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            startupinfo=startupinfo,
            timeout=30
        )
        
        if result.returncode != 0:
            log(f"fpcalc failed: {result.stderr}", "DEBUG")
            return None, None
            
        # Parse fingerprint data
        data = json.loads(result.stdout)
        fingerprint = data['fingerprint']
        duration = data['duration']
        
        # Query AcoustID API
        return query_acoustid(fingerprint, duration)
        
    except subprocess.TimeoutExpired:
        log("fpcalc timeout after 30 seconds", "DEBUG")
        return None, None
    except Exception as e:
        log(f"AcoustID fingerprinting error: {e}", "DEBUG")
        return None, None
```

### 2. AcoustID API Query (using urllib)
```python
def query_acoustid(fingerprint, duration):
    """Query AcoustID API for metadata using urllib."""
    import urllib.parse
    import urllib.request
    import urllib.error
    
    url = 'https://api.acoustid.org/v2/lookup'
    params = {
        'client': ACOUSTID_API_KEY,
        'fingerprint': fingerprint,
        'duration': int(duration),
        'meta': 'recordings'
    }
    
    try:
        # Build URL with parameters
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # Make request
        with urllib.request.urlopen(full_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Extract best match
        if data.get('results'):
            for result in data['results']:
                if result.get('recordings'):
                    # Get first recording with good confidence
                    confidence = result.get('score', 0)
                    if confidence < 0.4:  # Skip low confidence matches
                        continue
                        
                    for recording in result['recordings']:
                        artists = recording.get('artists', [])
                        if artists and recording.get('title'):
                            artist = artists[0]['name']
                            title = recording['title']
                            log(f"AcoustID match (confidence: {confidence:.2f})", "DEBUG")
                            return title, artist
                
    except urllib.error.HTTPError as e:
        log(f"AcoustID API HTTP error: {e.code} {e.reason}", "DEBUG")
    except urllib.error.URLError as e:
        log(f"AcoustID API connection error: {e}", "DEBUG")
    except Exception as e:
        log(f"AcoustID API error: {e}", "DEBUG")
    
    return None, None
```

### 3. YouTube Title Parser
```python
def parse_youtube_title(title):
    """Parse YouTube title to extract artist and song."""
    # First, clean the title
    cleaned_title = title
    
    # Remove common suffixes in parentheses or brackets
    cleaned_title = re.sub(r'\s*\([^)]*\)\s*$', '', cleaned_title)  # Remove (Official Video) etc
    cleaned_title = re.sub(r'\s*\[[^\]]*\]\s*$', '', cleaned_title)  # Remove [HD] etc
    
    # Common patterns in YouTube titles
    patterns = [
        # Artist - Song (including various dash types)
        (r'^(.*?)\s*[-–—]\s*(.*)$', 'hyphen'),
        # Artist | Song
        (r'^(.*?)\s*\|\s*(.*)$', 'pipe'),
        # Artist : Song
        (r'^(.*?)\s*:\s*(.*)$', 'colon'),
        # "Song" by Artist
        (r'^"(.+?)"\s+by\s+(.+)$', 'by_format', True),  # True = swap order
    ]
    
    for pattern_info in patterns:
        pattern = pattern_info[0]
        name = pattern_info[1]
        swap = pattern_info[2] if len(pattern_info) > 2 else False
        
        match = re.match(pattern, cleaned_title, re.IGNORECASE)
        if match:
            if swap:
                song = match.group(1).strip()
                artist = match.group(2).strip()
            else:
                artist = match.group(1).strip()
                song = match.group(2).strip()
            
            # Additional cleanup
            song = song.strip('"\'')  # Remove quotes
            artist = artist.strip('"\'')
            
            # Remove "Official Audio/Video" from song if still present
            song = re.sub(r'\s*(Official\s*(Audio|Video|Music\s*Video))?\s*$', '', song, flags=re.IGNORECASE)
            
            log(f"Parsed using {name} pattern", "DEBUG")
            return song, artist
    
    # If no pattern matches, use cleaned title as song name
    return cleaned_title, "Unknown Artist"
```

### 4. Metadata Selection
```python
def get_metadata(filepath, yt_title, video_id):
    """Get song and artist metadata using AcoustID or YouTube title."""
    # Try AcoustID first
    song, artist = get_acoustid_metadata(filepath)
    if song and artist and song != "Unknown Title":
        log(f"Metadata via AcoustID: '{yt_title}' → Song: '{song}', Artist: '{artist}'", "NORMAL")
        return song, artist
    
    # Fallback to parsing YouTube title
    song, artist = parse_youtube_title(yt_title)
    log(f"Metadata via title parser: '{yt_title}' → Song: '{song}', Artist: '{artist}'", "NORMAL")
    return song, artist
```

### 5. Integration with Process Worker
Update process_videos_worker to call metadata extraction after download:
```python
# In process_videos_worker, after download:
# Download video
temp_path = download_video(video_id, title)
if not temp_path:
    log(f"Failed to download: {title}", "NORMAL")
    continue

# Extract metadata
song, artist = get_metadata(temp_path, title, video_id)

# TODO: Continue to normalization (Phase 6)
# Pass song, artist, and temp_path to normalization phase
```

## Key Considerations
- fpcalc must be available (installed in Phase 2)
- Use urllib (standard library) NOT requests
- API rate limit: 3 requests/second (free tier)
- Some videos won't have AcoustID matches
- Log clearly shows which method provided metadata
- Hide console windows on Windows
- Handle various dash types (-, –, —) in titles
- Skip low confidence AcoustID matches (<0.4)

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement get_acoustid_metadata function
- [ ] Implement query_acoustid with urllib (NOT requests)
- [ ] Implement parse_youtube_title function
- [ ] Implement get_metadata wrapper
- [ ] Update process_videos_worker to use metadata
- [ ] Add Windows console hiding for subprocess
- [ ] Handle all error cases gracefully
- [ ] Add confidence threshold for AcoustID
- [ ] Test with various video types

## Testing Before Commit
1. Process popular song - verify AcoustID match
2. Process obscure song - verify YouTube fallback
3. Process non-music video - verify graceful handling
4. Test with no network - verify error handling
5. Process classical music - verify multi-artist handling
6. Test API rate limiting with rapid requests
7. Verify metadata extraction works correctly
8. Check logs clearly show metadata source (AcoustID vs parser)
9. Test YouTube title parser with various formats:
   - "Artist - Song"
   - "Artist | Song"
   - "Song by Artist"
   - Titles with (Official Video), [HD], etc.
10. Test various dash types (hyphen, en-dash, em-dash)
11. **Verify version was incremented**
12. **Verify no console windows appear on Windows**

## Commit
After successful testing, commit with message:  
> *"Add AcoustID metadata extraction with YouTube fallback"*

*After verification, proceed to Phase 06.*