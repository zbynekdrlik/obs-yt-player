# Phase 13: Google Gemini AI Metadata Integration

## Overview
This phase adds Google Gemini AI as the primary metadata extraction method, providing intelligent parsing of YouTube video titles to accurately extract artist and song information.

## Objectives
- Integrate Google Gemini AI API for metadata extraction
- Make Gemini the primary metadata source when configured
- Maintain fallback to existing methods (AcoustID, iTunes, parsing)
- Add UI for API key configuration

## Implementation Details

### 1. New Module: `gemini_metadata.py`
```python
"""
Google Gemini API metadata extraction for YouTube videos.
Uses Gemini to intelligently parse artist and song from video context.
"""
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Tuple

import state
from logger import log
from config import SCRIPT_NAME

# Gemini API configuration
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_TIMEOUT = 10  # seconds
MAX_RETRIES = 2

def extract_metadata_with_gemini(video_id: str, video_title: str, api_key: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract artist and song metadata using Google Gemini API.
    
    Args:
        video_id: YouTube video ID
        video_title: Original video title
        api_key: Gemini API key (from OBS script properties)
        
    Returns:
        Tuple of (artist, song) or (None, None) if extraction fails
    """
    if not api_key:
        return None, None
        
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    prompt = f"""Analyze this YouTube music video and extract the artist name and song title.

Video URL: {video_url}
Video Title: {video_title}

Please respond with ONLY a JSON object in this exact format:
{{"artist": "Artist Name", "song": "Song Title"}}

Guidelines:
- If featuring multiple artists, list the primary artist
- Remove any extra information like (Official Video), [Live], (feat.), etc from the song title
- If you cannot determine either field, use null
- Base your response on the video title and any context available"""

    request_body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for consistent results
            "maxOutputTokens": 100
        }
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            request = urllib.request.Request(
                f"{GEMINI_API_ENDPOINT}?key={api_key}",
                data=json.dumps(request_body).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(request, timeout=GEMINI_TIMEOUT) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract the generated text
                if 'candidates' in result and result['candidates']:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    log(f"Gemini response for '{video_title}': {text}")
                    
                    try:
                        # Parse the JSON response
                        metadata = json.loads(text.strip())
                        artist = metadata.get('artist')
                        song = metadata.get('song')
                        
                        if artist and song:
                            log(f"Gemini extracted: {artist} - {song}")
                            return artist, song
                    except json.JSONDecodeError:
                        log(f"Failed to parse Gemini JSON response: {text}")
                        
        except urllib.error.HTTPError as e:
            log(f"Gemini API HTTP error (attempt {attempt + 1}): {e.code} - {e.reason}")
            if e.code == 429:  # Rate limit
                time.sleep(2 ** attempt)  # Exponential backoff
        except urllib.error.URLError as e:
            log(f"Gemini API URL error (attempt {attempt + 1}): {str(e)}")
        except Exception as e:
            log(f"Gemini API error (attempt {attempt + 1}): {str(e)}")
            
        if attempt < MAX_RETRIES - 1:
            time.sleep(1)  # Brief pause between retries
            
    log(f"Gemini metadata extraction failed for '{video_title}'")
    return None, None
```

### 2. State Management Updates
Added to `state.py`:
```python
# Configuration state
_gemini_api_key = None  # Add Gemini API key state

def get_gemini_api_key():
    """Get the Gemini API key."""
    with _state_lock:
        return _gemini_api_key

def set_gemini_api_key(key):
    """Set the Gemini API key."""
    global _gemini_api_key
    with _state_lock:
        _gemini_api_key = key
```

### 3. Metadata Module Updates
Modified `metadata.py` to use Gemini as primary source:
```python
def get_video_metadata(filepath, title, video_id=None):
    """
    Main metadata extraction function.
    Tries Gemini first (if configured), then AcoustID, iTunes, and title parsing.
    Always returns (song, artist, source) - never None.
    """
    # NEW: Try Gemini FIRST if API key is configured
    gemini_api_key = state.get_gemini_api_key()
    if gemini_api_key and video_id:
        log(f"Attempting Gemini metadata extraction for '{title}'")
        gemini_artist, gemini_song = gemini_metadata.extract_metadata_with_gemini(
            video_id, title, gemini_api_key
        )
        if gemini_artist and gemini_song:
            # Apply universal cleaning to Gemini results
            song = clean_featuring_from_song(gemini_song)
            artist = gemini_artist
            log(f"Metadata from Gemini: {artist} - {song}")
            return song, artist, 'Gemini'
    
    # If Gemini fails or not configured, try AcoustID
    # ... rest of existing fallback chain ...
```

### 4. UI Integration
Added to `script_properties()` in `ytfast.py`:
```python
# Add separator for optional features
obs.obs_properties_add_text(
    props,
    "separator1",
    "───── Optional Features ─────",
    obs.OBS_TEXT_INFO
)

# Gemini API key field (password type for security)
obs.obs_properties_add_text(
    props, 
    "gemini_api_key", 
    "Google Gemini API Key", 
    obs.OBS_TEXT_PASSWORD
)

# Help text for Gemini
obs.obs_properties_add_text(
    props,
    "gemini_help",
    "For better metadata extraction. Get your free API key at:\nhttps://makersuite.google.com/app/apikey",
    obs.OBS_TEXT_INFO
)
```

### 5. Download Module Updates
Pass video_id to metadata extraction:
```python
# Get metadata (from metadata module) - UPDATED to pass video_id
song, artist, metadata_source = get_video_metadata(temp_path, title, video_id)
```

## Benefits

1. **Intelligent Extraction**: Uses AI to understand complex video titles
2. **High Accuracy**: Particularly effective for worship/church music and international content
3. **Handles Edge Cases**: Works with titles that have featuring artists, remixes, live versions
4. **Optional Enhancement**: Doesn't break existing functionality when not configured
5. **Clean Integration**: Fits seamlessly into existing metadata pipeline

## Testing Results

Successfully tested with various video titles:
- ✅ "Joy Of The Lord | Planetshakers Official Music Video"
- ✅ "HOLYGHOST | Sons Of Sunday"  
- ✅ "Let The Church Sing | Tauren Wells | Worship Together Session"
- ✅ "Ask Me Why // Michael Bethany Ft. Dwan Hill + The Choir Room // Worship Together Session"
- ✅ "No One & You Really Are (feat. Chandler Moore & Tiffany Hudson) | Elevation Worship"
- ✅ "Marco Barrientos - Yo Sé (Video Oficial)"
- ✅ "En este lugar | Lakewood Music con @AlexanderPappas"
- ✅ "Fidelidad | Lakewood Music Español (con @IngridRosarioLive )"

All extractions were accurate, with proper artist/song separation and removal of extra annotations.

## Version History

- v2.5.0 - Initial Gemini integration
- v2.5.1 - Updated to make Gemini primary source (not fallback)
- v2.5.2-v2.5.4 - Fixed import errors
- v2.5.5 - Updated API endpoint to `gemini-2.0-flash`
- v2.5.6 - Final testing and validation

## Future Enhancements

1. **Batch Processing**: Could batch multiple titles in one API call
2. **Caching**: Cache Gemini results to avoid repeated API calls
3. **Context Enhancement**: Could provide genre hints or playlist context
4. **Error Reporting**: More detailed error messages for troubleshooting

## Conclusion

The Google Gemini AI integration significantly improves metadata extraction accuracy, especially for complex YouTube titles. It provides a superior user experience while maintaining backward compatibility with existing metadata sources.
