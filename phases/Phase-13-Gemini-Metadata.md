# Phase-13‑Gemini‑Metadata

## Overview
This phase adds Google Gemini API as the PRIMARY metadata source when configured. The Gemini LLM provides the most accurate metadata extraction by intelligently analyzing YouTube video URLs and titles.

## Requirements from 02‑Requirements.md
- Makes Gemini the primary metadata source:
  1. **NEW** Primary: Gemini API (when configured with API key)
  2. Secondary: AcoustID
  3. Tertiary: iTunes
  4. Quaternary: Title parsing
- Maintain all existing universal song title cleaning
- Log all Gemini API interactions

## Technical Implementation

### Module: `ytfast_modules/gemini_metadata.py`

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

from . import state
from .logger import log
from .config import SCRIPT_NAME

# Gemini API configuration
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
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

def clean_gemini_song_title(song: str) -> str:
    """
    Apply same cleaning rules as other metadata sources.
    """
    # This will be handled by the universal cleaner
    return song
```

### Integration Updates

#### Update `ytfast_modules/metadata.py`:

Gemini is now the FIRST metadata source checked:

```python
# At the top, import the new module
from . import gemini_metadata

# In get_video_metadata function:

def get_video_metadata(filepath, title, video_id=None):
    """
    Main metadata extraction function.
    Tries Gemini first (if configured), then AcoustID, iTunes, and title parsing.
    Always returns (song, artist, source) - never None.
    """
    # NEW: Try Gemini FIRST if API key is configured
    gemini_api_key = state.get_state('gemini_api_key')
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
    
    # If Gemini fails or not configured, continue with existing cascade...
```

#### Update `ytfast_modules/config.py`:

```python
# Add to version (increment PATCH for iteration)
SCRIPT_VERSION = "2.5.1"

# Add Gemini configuration
GEMINI_ENABLED_DEFAULT = False  # User must opt-in with API key
```

#### Update main script `ytfast.py`:

Add Gemini API key to script properties:

```python
def script_properties():
    props = obs.obs_properties_create()
    
    # Existing properties...
    
    # Add Gemini API section
    obs.obs_properties_add_text(
        props, "gemini_api_key", 
        "Gemini API Key (optional - for better metadata)", 
        obs.OBS_TEXT_PASSWORD
    )
    
    obs.obs_properties_add_text(
        props, "gemini_help",
        "Get your API key from: https://makersuite.google.com/app/apikey",
        obs.OBS_TEXT_INFO
    )
    
    return props

def script_update(settings):
    # Existing code...
    
    # Store Gemini API key
    gemini_key = obs.obs_data_get_string(settings, "gemini_api_key")
    if gemini_key:
        state.set_state('gemini_api_key', gemini_key)
        log("Gemini API key configured")
```

## Testing Requirements

Before merging:
1. **Without API Key**: Verify script falls back to AcoustID → iTunes → parsing
2. **With Invalid Key**: Ensure graceful failure and fallback
3. **With Valid Key**: Test that Gemini runs FIRST for all videos
4. **Complex Titles**: Verify improved accuracy on Planetshakers videos
5. **Performance**: Ensure quick responses (10s timeout)

### Expected Log Output:
```
[ytfast.py] [timestamp] Script version 2.5.1 loaded
[ytfast.py] [timestamp] Gemini API key configured
[Unknown Script] [timestamp] [ytfast] Attempting Gemini metadata extraction for 'Praise On It | Winning Team | Planetshakers Official Music Video'
[Unknown Script] [timestamp] [ytfast] Gemini response: {"artist": "Planetshakers", "song": "Praise On It"}
[Unknown Script] [timestamp] [ytfast] Gemini extracted: Planetshakers - Praise On It
[Unknown Script] [timestamp] [ytfast] Metadata from Gemini: Planetshakers - Praise On It
```

## Benefits
- **Primary accuracy**: Most accurate metadata extraction method
- **Complex title handling**: Excels at parsing difficult titles
- **Intelligent parsing**: Uses LLM understanding of context
- **Fast results**: No need to fingerprint or search multiple APIs
- **Optional feature**: Falls back to existing methods if not configured

## Privacy & Security
- API key stored securely in OBS (password field)
- Only video title and ID sent to Gemini
- No video content downloaded by Gemini
- User must explicitly opt-in with their own API key

*Prev → Phase-12-Simple-Polish.md | Next → (Future phases)*