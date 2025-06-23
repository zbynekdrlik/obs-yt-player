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
Uses Gemini 2.5 Flash with Google Search grounding to intelligently extract artist and song information.
"""
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import re
from typing import Optional, Tuple

import state
from logger import log
from config import SCRIPT_NAME

# Gemini API configuration
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_TIMEOUT = 30  # Increased timeout for Google Search grounding
MAX_RETRIES = 2

def extract_metadata_with_gemini(video_id: str, video_title: str, api_key: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract artist and song metadata using Google Gemini API with Google Search grounding.
    
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
    
    # Enhanced prompt with STRICT JSON requirements
    prompt = f"""Look up information about this YouTube video and extract the artist and song title:
URL: {video_url}
Title: "{video_title}"

Use Google Search to find information about this specific YouTube video URL.

CRITICAL: Respond with ONLY a valid JSON object. No explanatory text allowed.

Return EXACTLY this format:
{{"artist": "Primary Artist Name", "song": "Song Title"}}

RULES:
1. Search for the YouTube URL to find the actual artist
2. For worship/church music, identify the performing artist/band
3. Remove feat./ft./featuring from artist name
4. Remove (Official Video), (Live), etc from song titles
5. Keep "/" in multi-part titles like "Faithful Then / Faithful Now"
6. If no artist found, return empty string for artist

Examples:
- "HOLYGHOST | Sons Of Sunday" → {{"artist": "Sons Of Sunday", "song": "HOLYGHOST"}}
- "'COME RIGHT NOW' | Official Video" → {{"artist": "Planetshakers", "song": "COME RIGHT NOW"}}

REMEMBER: Return ONLY valid JSON, nothing else."""

    # Add system instruction to enforce JSON-only responses
    request_body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "tools": [{
            "google_search": {}
        }],
        "systemInstruction": {
            "parts": [{
                "text": "You are a JSON API that returns only valid JSON objects. Never include explanatory text, reasoning, or any content outside the JSON structure."
            }]
        },
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for consistent results
            "candidateCount": 1
            # Removed responseMimeType as it's not supported with tool use
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
                    candidate = result['candidates'][0]
                    
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if parts and 'text' in parts[0]:
                            text = parts[0]['text']
                            log(f"Gemini response for '{video_title}': {text}")
                        else:
                            log(f"Unexpected Gemini response structure: {json.dumps(result, indent=2)[:500]}")
                            continue
                    else:
                        log(f"No content in candidate: {json.dumps(candidate, indent=2)[:500]}")
                        continue
                    
                    try:
                        # Clean up the response - remove markdown code blocks if present
                        cleaned_text = text.strip()
                        
                        # Remove markdown code block markers
                        if cleaned_text.startswith('```json'):
                            cleaned_text = cleaned_text[7:]  # Remove ```json
                        elif cleaned_text.startswith('```'):
                            cleaned_text = cleaned_text[3:]  # Remove ```
                        
                        if cleaned_text.endswith('```'):
                            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
                        
                        cleaned_text = cleaned_text.strip()
                        
                        # Try to extract JSON even if there's extra text (fallback)
                        # Look for JSON object pattern
                        json_match = re.search(r'\{[^{}]*"artist"[^{}]*"song"[^{}]*\}', cleaned_text)
                        if json_match and not cleaned_text.startswith('{'):
                            log(f"Extracting JSON from mixed response")
                            cleaned_text = json_match.group(0)
                        
                        # Parse the JSON response
                        metadata = json.loads(cleaned_text)
                        artist = metadata.get('artist', '').strip()
                        song = metadata.get('song', '').strip()
                        
                        # Accept response if we have at least a song title
                        if song:
                            if artist:
                                log(f"Gemini extracted: {artist} - {song}")
                            else:
                                log(f"Gemini extracted song only: {song} (no artist found)")
                            return artist if artist else None, song
                        else:
                            log(f"Gemini response missing song title: {metadata}")
                    except json.JSONDecodeError as e:
                        log(f"Failed to parse Gemini JSON response: {text} (Error: {e})")
                else:
                    log(f"No candidates in Gemini response: {json.dumps(result, indent=2)[:500]}")
                        
        except urllib.error.HTTPError as e:
            error_body = None
            try:
                error_body = e.read().decode('utf-8')
                error_json = json.loads(error_body)
                log(f"Gemini API HTTP error (attempt {attempt + 1}): {e.code} - {e.reason}")
                log(f"Error details: {json.dumps(error_json, indent=2)[:500]}")
            except:
                log(f"Gemini API HTTP error (attempt {attempt + 1}): {e.code} - {e.reason}")
                if error_body:
                    log(f"Error response: {error_body[:500]}")
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

### 6. Enhanced Filename Sanitization (utils.py)
```python
def sanitize_filename(text):
    """Sanitize text for use in filename."""
    # First, replace forward slashes with hyphens to avoid space issues
    text = text.replace('/', '-')
    
    # Remove/replace other invalid filename characters
    invalid_chars = '<>:"|?*\\'  # Note: forward slash already handled
    for char in invalid_chars:
        text = text.replace(char, '_')
    
    # Clean up multiple spaces or dashes
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'-+', '-', text)   # Replace multiple dashes with single dash
    text = re.sub(r'_+', '_', text)   # Replace multiple underscores with single underscore
    
    # Remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remove any leading/trailing spaces, dashes, or underscores
    text = text.strip(' -_')
    
    # Limit length and clean up
    text = text[:50].strip().rstrip('.')
    
    return text
```

## Benefits

1. **Intelligent Extraction**: Uses AI to understand complex video titles
2. **High Accuracy**: Particularly effective for worship/church music and international content
3. **Handles Edge Cases**: Works with titles that have featuring artists, remixes, live versions
4. **Optional Enhancement**: Doesn't break existing functionality when not configured
5. **Clean Integration**: Fits seamlessly into existing metadata pipeline
6. **Enhanced Title Pattern Handling**: Properly excludes album names and part numbers
7. **Google Search Grounding**: Can find artist information even when not in title

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
- ✅ "So Good | Glory Pt. 2 | Planetshakers Official Music Video" → Correctly excludes "Glory Pt. 2"
- ✅ "Living In Me | Show Me Your Glory - Live At Chapel" → Only takes "Living In Me"
- ✅ "Faithful Then / Faithful Now (Extended Version) | Elevation Worship" → Preserves forward slash
- ✅ "Donde Vaya (En Vivo) - Official Music Video" → Finds artist via Google Search
- ✅ "Presence | NEW LEVEL (worship cover)" → Correct artist/song separation
- ✅ "'COME RIGHT NOW' | Official Planetshakers Music Video" → Handles quotes properly

All extractions were accurate, with proper artist/song separation and removal of extra annotations.

## Version History

- v2.5.0 - Initial Gemini integration
- v2.5.1 - Updated to make Gemini primary source (not fallback)
- v2.5.2-v2.5.4 - Fixed import errors
- v2.5.5 - Updated API endpoint to `gemini-2.0-flash`
- v2.5.6 - Final testing and validation
- v3.0.1-v3.0.6 - Enhanced prompt for album name exclusion and title pattern handling
- v3.0.7 - Improved handling of "Song | Artist" patterns
- v3.0.8 - Upgraded to Gemini 2.5 Flash with Google Search grounding
- v3.0.9 - Enhanced prompt to enforce JSON-only responses
- v3.0.10 - Fixed API compatibility by removing `responseMimeType` parameter
- v3.0.11 - Cleaned up configuration to match main branch structure

## Future Enhancements

1. **Batch Processing**: Could batch multiple titles in one API call
2. **Caching**: Cache Gemini results to avoid repeated API calls
3. **Context Enhancement**: Could provide genre hints or playlist context
4. **Error Reporting**: More detailed error messages for troubleshooting
5. **Artist Verification**: Use additional sources to verify artist information

## Conclusion

The Google Gemini AI integration significantly improves metadata extraction accuracy, especially for complex YouTube titles. The recent enhancements (v3.0+) further improve handling of album names, complex title patterns, and artist detection through Google Search grounding. It provides a superior user experience while maintaining backward compatibility with existing metadata sources.