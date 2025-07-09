"""Gemini API integration for metadata extraction.
Provides AI-powered artist/song detection from video titles.
"""

import os
import re
import time
import google.generativeai as genai
from .logger import log
from .state import get_gemini_api_key

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Track failed attempts to avoid repeated failures
_gemini_failures = set()  # Set of video IDs that failed

def setup_gemini():
    """Set up Gemini API if key is available."""
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Use the most cost-effective model for simple text tasks
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        log(f"Failed to setup Gemini: {e}")
        return None

def extract_metadata_with_gemini(title, video_id=None):
    """Extract artist and song using Gemini AI."""
    # Check if we've already failed on this video
    if video_id and video_id in _gemini_failures:
        return None
    
    # Skip if no API key
    if not get_gemini_api_key():
        return None
    
    model = setup_gemini()
    if not model:
        return None
    
    # Create a focused prompt for music metadata extraction
    prompt = f"""Extract the artist name and song title from this YouTube video title. 
Respond ONLY with two lines in this exact format:
ARTIST: [artist name]
SONG: [song title]

If you can't determine either, use "Unknown Artist" or "Unknown Song".
Remove any extra information like "Official Video", "Lyric Video", year, etc.
For classical music, the composer is the artist.

Video title: {title}"""
    
    for attempt in range(MAX_RETRIES):
        try:
            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent output
                    max_output_tokens=100,  # We only need two short lines
                )
            )
            
            # Parse response
            text = response.text.strip()
            lines = text.split('\n')
            
            artist = None
            song = None
            
            for line in lines:
                if line.startswith('ARTIST:'):
                    artist = line.replace('ARTIST:', '').strip()
                elif line.startswith('SONG:'):
                    song = line.replace('SONG:', '').strip()
            
            if artist and song:
                # Clean up common additions
                song = re.sub(r'\s*\(Official.*?\)\s*', '', song)
                song = re.sub(r'\s*\[Official.*?\]\s*', '', song)
                song = re.sub(r'\s*\(Lyric.*?\)\s*', '', song)
                song = re.sub(r'\s*\[Lyric.*?\]\s*', '', song)
                song = re.sub(r'\s*\(Audio.*?\)\s*', '', song)
                song = re.sub(r'\s*\[Audio.*?\]\s*', '', song)
                song = re.sub(r'\s*\(\d{4}\)\s*', '', song)  # Remove years
                song = song.strip()
                
                log(f"Gemini extracted: {artist} - {song}")
                return {
                    'artist': artist,
                    'song': song,
                    'gemini_used': True
                }
            
        except Exception as e:
            log(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    # Mark this video as failed to avoid repeated attempts
    if video_id:
        _gemini_failures.add(video_id)
        log(f"Marked video {video_id} as Gemini failed")
    
    return None

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