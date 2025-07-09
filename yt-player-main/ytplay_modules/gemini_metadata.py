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

from . import state
from .logger import log
from .config import SCRIPT_NAME

# Gemini API configuration
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_TIMEOUT = 30  # Increased timeout for Google Search grounding
MAX_RETRIES = 2

# Version 3.3.3 - Improve prompt to handle medleys and album names correctly

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

IMPORTANT RULES:
1. Search for the YouTube URL to find the actual artist and song information
2. For worship/church music, identify the performing artist/band (not the church name)
3. Remove feat./ft./featuring from artist name
4. Remove (Official Video), (Live), etc from song titles
5. For single songs with "/" in their actual title (like "Faithful Then / Faithful Now"), keep the full title
6. NEVER include album names in the song title - return only the actual song name
7. If the video is a medley or contains multiple distinct songs, return ONLY the first song
8. If no artist found, return empty string for artist

Examples:
- "HOLYGHOST | Sons Of Sunday" → {{"artist": "Sons Of Sunday", "song": "HOLYGHOST"}}
- "'COME RIGHT NOW' | Official Video" → {{"artist": "Planetshakers", "song": "COME RIGHT NOW"}}
- "Supernatural Love | Show Me Your Glory - Live At Chapel | Planetshakers Official Music Video" → {{"artist": "Planetshakers", "song": "Supernatural Love"}}
- "Forever | Live At Chapel" → {{"artist": "Kari Jobe", "song": "Forever"}}
- "The Blessing (Live) | Elevation Worship" → {{"artist": "Elevation Worship", "song": "The Blessing"}}
- "Faithful Then / Faithful Now | Elevation Worship" → {{"artist": "Elevation Worship", "song": "Faithful Then / Faithful Now"}}
- "There Is A King/What Would You Do | Live | Elevation Worship" → {{"artist": "Elevation Worship", "song": "There Is A King"}}

REMEMBER: Return ONLY valid JSON, nothing else. The song field should contain ONLY the song title, never album names or other metadata."""

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

# Track failed attempts to avoid repeated failures (compatibility)
_gemini_failures = set()  # Set of video IDs that failed

def clear_gemini_failures():
    """Clear the set of failed video IDs (called on script restart)."""
    global _gemini_failures
    _gemini_failures.clear()
    log("Cleared Gemini failure cache")

def remove_gemini_failure(video_id):
    """Remove a video ID from the failure set (for retry)."""
    if video_id in _gemini_failures:
        _gemini_failures.remove(video_id)
        log(f"Removed {video_id} from Gemini failure cache")

def is_gemini_failed(video_id):
    """Check if a video ID has failed Gemini extraction."""
    return video_id in _gemini_failures
