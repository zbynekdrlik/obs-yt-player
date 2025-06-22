"""
Google Gemini API metadata extraction for YouTube videos.
Uses Gemini to intelligently parse artist and song from video context.
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
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/models/gemini-2.5-flash:generateContent"
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
    
    prompt = f"""Extract artist and song from this YouTube music video:
URL: {video_url}
Title: "{video_title}"

Return ONLY JSON: {{"artist": "Artist Name", "song": "Song Title"}}

Rules:
- Song = ONLY the first part before any "|" separator
- Exclude album names, "Pt. 2", etc from song
- Remove (Official Video), [Live], etc from song
- Keep "/" in multi-song titles

Example: "So Good | Glory Pt. 2 | Planetshakers" → {{"artist": "Planetshakers", "song": "So Good"}}"""

    request_body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for consistent results
            "candidateCount": 1,
            "maxOutputTokens": 256  # Increased from 100
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
                    if 'content' in candidate:
                        content = candidate['content']
                        if 'parts' in content and content['parts']:
                            text = content['parts'][0]['text']
                            log(f"Gemini response for '{video_title}': {text}")
                        elif 'text' in content:
                            # Sometimes the text might be directly in content
                            text = content['text']
                            log(f"Gemini response for '{video_title}': {text}")
                        else:
                            log(f"Unexpected Gemini response structure: {json.dumps(result, indent=2)[:500]}")
                            if 'finishReason' in candidate and candidate['finishReason'] == 'MAX_TOKENS':
                                log("Response hit MAX_TOKENS limit - prompt may be too long")
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
                        
                        # Parse the JSON response
                        metadata = json.loads(cleaned_text)
                        artist = metadata.get('artist')
                        song = metadata.get('song')
                        
                        if artist and song:
                            log(f"Gemini extracted: {artist} - {song}")
                            return artist, song
                        else:
                            log(f"Gemini response missing artist or song: {metadata}")
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
