"""Gemini AI metadata extraction for OBS YouTube Player.
Uses Google's Gemini AI to extract artist and song information from video titles.
"""

import requests
import json
import time
import tempfile
import os

# Use absolute imports to fix module loading issue
from ytplay_modules.logger import log

# Gemini API configuration
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

def extract_metadata_with_gemini(video_id, video_title, api_key):
    """Extract artist and song metadata using Gemini AI."""
    if not api_key:
        return None, None
    
    try:
        # Prepare the prompt
        prompt = f"""Extract the artist name and song title from this YouTube video title. 

Video title: "{video_title}"

Rules:
1. Identify the ARTIST NAME (performer/band/singer)
2. Identify the SONG TITLE (name of the song)
3. Remove any featuring artists from the song title - they should NOT be included
4. Remove any additional information like "Official Video", "Lyric Video", "Live", etc.
5. If you cannot reliably identify both artist and song, return null for both

Respond ONLY with a JSON object in this exact format:
{{
  "artist": "Artist Name",
  "song": "Song Title"
}}

Do not include any other text or explanation."""
        
        # Prepare request
        url = f"{GEMINI_API_BASE}?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 100
            }
        }
        
        # Make request
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code != 200:
            log(f"Gemini API error: {response.status_code} - {response.text}")
            return None, None
        
        # Parse response
        result = response.json()
        
        # Extract the generated text
        try:
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean the response - sometimes Gemini adds markdown formatting
            generated_text = generated_text.strip()
            if generated_text.startswith('```json'):
                generated_text = generated_text[7:]
            if generated_text.startswith('```'):
                generated_text = generated_text[3:]
            if generated_text.endswith('```'):
                generated_text = generated_text[:-3]
            generated_text = generated_text.strip()
            
            # Parse JSON response
            metadata = json.loads(generated_text)
            
            artist = metadata.get('artist')
            song = metadata.get('song')
            
            # Validate response
            if artist and song and artist != "null" and song != "null":
                # Additional validation - ensure we got meaningful results
                if len(artist) > 1 and len(song) > 1:
                    log(f"Gemini extracted: Artist='{artist}', Song='{song}'")
                    return artist, song
                else:
                    log("Gemini returned invalid/too short results")
                    return None, None
            else:
                log("Gemini could not extract metadata")
                return None, None
                
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            log(f"Error parsing Gemini response: {e}")
            log(f"Raw response: {result}")
            return None, None
            
    except requests.exceptions.Timeout:
        log("Gemini request timeout")
        return None, None
    except Exception as e:
        log(f"Gemini extraction error: {e}")
        return None, None

def test_gemini_connection(api_key):
    """Test if Gemini API key is valid."""
    if not api_key:
        return False
        
    try:
        # Simple test prompt
        url = f"{GEMINI_API_BASE}?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": "Say 'OK' if you can read this."
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 10
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=5)
        
        if response.status_code == 200:
            log("Gemini API key validated successfully")
            return True
        else:
            log(f"Gemini API key validation failed: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"Gemini connection test failed: {e}")
        return False

def save_api_key_to_file(api_key, script_name):
    """Save API key to a file for persistence."""
    try:
        # Get temp directory
        temp_dir = tempfile.gettempdir()
        key_file = os.path.join(temp_dir, f"obs_ytplay_{script_name}_gemini.key")
        
        with open(key_file, 'w') as f:
            f.write(api_key)
        
        log(f"Gemini API key saved to: {key_file}")
        return True
    except Exception as e:
        log(f"Failed to save API key: {e}")
        return False

def load_api_key_from_file(script_name):
    """Load API key from file if it exists."""
    try:
        temp_dir = tempfile.gettempdir()
        key_file = os.path.join(temp_dir, f"obs_ytplay_{script_name}_gemini.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                api_key = f.read().strip()
            
            if api_key:
                log("Loaded Gemini API key from file")
                return api_key
    except Exception as e:
        log(f"Failed to load API key: {e}")
    
    return None