# Phase 05 – AcoustID Metadata Extraction

## Goal
Implement metadata extraction using AcoustID audio fingerprinting. This provides accurate song and artist information from an extensive music database when matches are found.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.3.6 to 1.4.0)

## Requirements Reference
This phase implements the primary metadata retrieval method from `02-requirements.md`:
- **AcoustID** fingerprinting with API key
- Use valid public API key: `M6o6ia3dKu` (as specified in requirements)
- Skip low confidence matches (<0.4)

## Implementation Details

### 1. Audio Fingerprinting
```python
def get_acoustid_metadata(filepath):
    """Query AcoustID for metadata using audio fingerprint."""
    if not ACOUSTID_ENABLED:
        log("AcoustID disabled, skipping fingerprinting")
        return None, None
        
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
            log(f"fpcalc failed: {result.stderr}")
            return None, None
            
        # Parse fingerprint data
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"Failed to parse fpcalc JSON output: {e}")
            log(f"fpcalc output: {result.stdout[:200]}...")
            return None, None
            
        fingerprint = data.get('fingerprint')
        duration = data.get('duration')
        
        if not fingerprint or not duration:
            log(f"Missing fingerprint or duration in fpcalc output")
            return None, None
            
        log(f"Generated fingerprint, duration: {duration}s")
        
        # Query AcoustID API
        return query_acoustid(fingerprint, duration)
        
    except subprocess.TimeoutExpired:
        log("fpcalc timeout after 30 seconds")
        return None, None
    except Exception as e:
        log(f"AcoustID fingerprinting error: {e}")
        return None, None
```

### 2. AcoustID API Query (using urllib)
```python
def query_acoustid(fingerprint, duration):
    """Query AcoustID API for metadata using urllib."""
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
        
        # Log the request details for debugging (but not the full fingerprint)
        log(f"AcoustID request - duration: {duration}s, fingerprint length: {len(fingerprint)}")
        
        # Make request with User-Agent
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
        
        # Log API response status
        status = data.get('status', 'unknown')
        if status != 'ok':
            log(f"AcoustID API status: {status}")
            if 'error' in data:
                log(f"AcoustID error: {data['error']}")
            return None, None
        
        # Extract best match
        results = data.get('results', [])
        log(f"AcoustID returned {len(results)} results")
        
        for result in results:
            if result.get('recordings'):
                # Get first recording with good confidence
                confidence = result.get('score', 0)
                if confidence < 0.4:  # Skip low confidence matches
                    log(f"Skipping low confidence match: {confidence:.2f}")
                    continue
                    
                for recording in result['recordings']:
                    artists = recording.get('artists', [])
                    if artists and recording.get('title'):
                        artist = artists[0]['name']
                        title = recording['title']
                        log(f"AcoustID match (confidence: {confidence:.2f}): {artist} - {title}")
                        return title, artist
        
        log("No suitable AcoustID matches found")
        return None, None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No response body'
        log(f"AcoustID API HTTP error: {e.code} {e.reason}")
        log(f"Error response: {error_body[:200]}")
    except urllib.error.URLError as e:
        log(f"AcoustID API connection error: {e}")
    except Exception as e:
        log(f"AcoustID API error: {e}")
    
    return None, None
```

### 3. Constants and Configuration
Add to module-level constants:
```python
# AcoustID API configuration
ACOUSTID_ENABLED = True  # Toggle to enable/disable AcoustID lookups
```
Note: ACOUSTID_API_KEY is already defined in the constants section

### 4. Integration with Process Worker
Update process_videos_worker to call AcoustID extraction after download:
```python
# In process_videos_worker, after download:
# Download video
temp_path = download_video(video_id, title)
if not temp_path:
    log(f"Failed to download: {title}")
    continue

# Try AcoustID metadata extraction
song, artist = get_acoustid_metadata(temp_path)

# Store metadata for next phase
metadata = {
    'song': song,
    'artist': artist,
    'yt_title': title
}

# TODO: Continue to Phase 6 (iTunes metadata)
# If AcoustID fails, will try iTunes in next phase
```

## Key Considerations
- fpcalc must be available (installed in Phase 2)
- Use urllib (standard library) NOT requests
- Valid API key required (use `M6o6ia3dKu` from requirements)
- API rate limit: 3 requests/second (free tier)
- Parse JSON output carefully with error handling
- Log detailed error messages for debugging
- Hide console windows on Windows
- Skip low confidence matches (<0.4)
- Add User-Agent header with script version
- Use simplified logging (no debug levels)

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` (increment MINOR version)
- [ ] Add ACOUSTID_ENABLED constant
- [ ] Implement get_acoustid_metadata function
- [ ] Implement query_acoustid with urllib (NOT requests)
- [ ] Add proper error handling for JSON parsing
- [ ] Add Windows console hiding for subprocess
- [ ] Handle all error cases gracefully
- [ ] Add confidence threshold for AcoustID
- [ ] Use simplified logging format
- [ ] Use script version in User-Agent header

## Testing Before Commit
1. Process popular song - verify AcoustID match
2. Process song with low confidence - verify it's skipped
3. Test with invalid API key - verify error handling
4. Test with no network - verify graceful failure
5. Process classical music - verify artist extraction
6. Test API rate limiting with rapid requests
7. Verify fingerprint generation works
8. Check logs show confidence scores
9. Test with very short audio files
10. Test with corrupted audio files
11. **Verify version was incremented**
12. **Verify no console windows appear on Windows**

## Commit
After successful testing, commit with message:  
> *"Add AcoustID metadata extraction (Phase 5)"*

*After verification, proceed to Phase 06.*
