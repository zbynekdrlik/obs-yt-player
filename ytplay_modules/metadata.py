"""
Metadata extraction module for OBS YouTube Player.
Handles Gemini AI extraction and fallback parsing.
"""

import re
import os

from logger import log
from state import get_gemini_failures, get_gemini_api_key

# Import Gemini integration
try:
    from gemini_metadata import extract_metadata_with_gemini
    _gemini_available = True
except ImportError:
    _gemini_available = False
    log("Gemini metadata module not available")

def clear_gemini_failures():
    """Clear the Gemini failures cache."""
    failures = get_gemini_failures()
    if failures:
        count = len(failures)
        failures.clear()
        log(f"Cleared {count} Gemini failure markers")

def clean_featuring_from_song(song):
    """Remove ALL bracket phrases from song title."""
    if not song:
        return song
    
    original_song = song
    log(f"Song title cleaning - Original: '{original_song}'")
    
    # Remove bracket content
    bracket_patterns = [
        r'\([^)]*\)',  # Parentheses
        r'\[[^\]]*\]', # Square brackets
        r'\{[^}]*\}',  # Curly brackets
    ]
    
    cleaned = song
    for pattern in bracket_patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Remove trailing annotations
    trailing_patterns = [
        r'\s+feat\.?\s+.*$',
        r'\s+ft\.?\s+.*$',
        r'\s+featuring\s+.*$',
        r'\s+official\s*(?:music\s*)?video\s*$',
        r'\s+official\s*audio\s*$',
        r'\s+music\s*video\s*$',
        r'\s+live\s*$',
        r'\s+acoustic\s*$',
        r'\s+hd\s*$',
        r'\s+4k\s*$',
    ]
    
    for pattern in trailing_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Final cleanup
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'[,\-\|\s]+$', '', cleaned).strip()
    
    if cleaned != original_song:
        log(f"Song title cleaned: '{original_song}' → '{cleaned}'")
    
    return cleaned or original_song

def parse_title_smart(title):
    """Smart title parser that handles various YouTube title formats."""
    if not title:
        return None, None
        
    log(f"Title parser - Original: '{title}'")
    
    # Clean the title
    cleaned = title.strip()
    
    # Try various patterns to extract artist and song
    patterns = [
        # Pattern: "Song | Artist"
        (r'^([^|]+)\s*\|\s*([^|]+?)(?:\s*(?:Official|Music|Video|Live|feat\.|ft\.)|$)', False),
        # Pattern: "Artist - Song"
        (r'^([^-]+?)\s*-\s*([^-]+?)(?:\s*\(|\s*\[|$)', True),
    ]
    
    for pattern, artist_first in patterns:
        match = re.match(pattern, cleaned, re.IGNORECASE)
        if match:
            part1 = match.group(1).strip()
            part2 = match.group(2).strip()
            
            if artist_first:
                artist, song = part1, part2
            else:
                song, artist = part1, part2
            
            # Clean up
            song = clean_featuring_from_song(song)
            
            if song and artist and len(artist) > 2:
                log(f"Title parser - Pattern match: Artist='{artist}', Song='{song}'")
                return song, artist
    
    # Unable to parse
    log(f"Title parser - Unable to parse title reliably")
    return None, None

def extract_metadata_gemini(video_title, video_id, api_key):
    """Extract metadata using Gemini AI."""
    if not _gemini_available or not api_key or not video_id:
        return None
    
    try:
        log(f"Attempting Gemini metadata extraction for '{video_title}'")
        artist, song = extract_metadata_with_gemini(video_id, video_title, api_key)
        
        if artist and song:
            # Apply universal cleaning to Gemini results
            song = clean_featuring_from_song(song)
            log(f"Metadata from Gemini: {artist} - {song}")
            return {
                'song': song,
                'artist': artist,
                'source': 'Gemini',
                'gemini_failed': False
            }
        else:
            log(f"Gemini failed for video {video_id}")
            return None
            
    except Exception as e:
        log(f"Gemini extraction error: {e}")
        return None

def parse_title_fallback(title):
    """Parse title using pattern matching as fallback."""
    song, artist = parse_title_smart(title)
    
    if song and artist:
        log(f"Using parsed metadata: {artist} - {song}")
        return {
            'song': song,
            'artist': artist,
            'source': 'title_parsing',
            'gemini_failed': False
        }
    
    # Conservative fallback
    log("No reliable artist/song could be parsed - using conservative fallback")
    return {
        'song': title,
        'artist': 'Unknown Artist',
        'source': 'title_parsing',
        'gemini_failed': False
    }

def extract_metadata(video_info, gemini_api_key=None):
    """Extract metadata from video using available methods."""
    video_id = video_info.get('id')
    title = video_info.get('title', '')
    
    gemini_failed = False
    
    # Try Gemini if API key available
    if gemini_api_key and video_id:
        result = extract_metadata_gemini(title, video_id, gemini_api_key)
        if result:
            return result
        else:
            # Gemini was attempted but failed
            gemini_failed = True
    
    # Fallback to title parsing
    result = parse_title_fallback(title)
    
    # Mark if Gemini failed so file can be marked with _gf
    if gemini_failed:
        result['gemini_failed'] = True
        # Add to failures set for tracking
        failures = get_gemini_failures()
        failures.add(video_id)
    
    return result

def get_current_video_from_media_source():
    """Get current video ID from media source filename."""
    # This needs OBS integration
    import obspython as obs
    from config import MEDIA_SOURCE_NAME
    
    try:
        # Get media source
        source = obs.obs_get_source_by_name(MEDIA_SOURCE_NAME)
        if not source:
            return None
        
        # Get source settings
        settings = obs.obs_source_get_settings(source)
        local_file = obs.obs_data_get_string(settings, "local_file")
        
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        
        if not local_file:
            return None
        
        # Extract video ID from filename
        # Format: song_artist_videoId_normalized.mp4 or song_artist_videoId_normalized_gf.mp4
        filename = os.path.basename(local_file)
        
        # Remove .mp4
        if filename.endswith('.mp4'):
            filename = filename[:-4]
        
        # Remove _gf if present
        if filename.endswith('_gf'):
            filename = filename[:-3]
        
        # Remove _normalized
        if filename.endswith('_normalized'):
            filename = filename[:-11]
        
        # Video ID is the last 11 characters
        if len(filename) >= 11:
            potential_id = filename[-11:]
            # Validate it looks like a YouTube ID
            if re.match(r'^[a-zA-Z0-9_-]{11}$', potential_id):
                return potential_id
        
        return None
        
    except Exception as e:
        log(f"Error getting current video from media source: {e}")
        return None
