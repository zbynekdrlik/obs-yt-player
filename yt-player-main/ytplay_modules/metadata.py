"""
Metadata extraction for OBS YouTube Player (Windows-only).
Handles Gemini AI and title parsing only.
"""

import os
import re
import json
from pathlib import Path

from config import SCRIPT_VERSION
from logger import log
from utils import format_duration, validate_youtube_id
import gemini_metadata
import state

def get_video_metadata(filepath, title, video_id=None):
    """
    Main metadata extraction function.
    Tries Gemini first (if configured), then falls back to title parsing.
    Always returns (song, artist, source, gemini_failed) - never None.
    The gemini_failed flag indicates if Gemini was attempted but failed.
    """
    gemini_failed = False
    
    # Always try Gemini if API key is configured
    # We want to retry on every restart
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
            return song, artist, 'Gemini', False
        else:
            # Gemini failed
            gemini_failed = True
            log(f"Gemini failed for video {video_id}, falling back to title parsing")
    
    # Fall back to title parsing
    song, artist, metadata_source = extract_metadata_from_title(title)
    
    return song, artist, metadata_source, gemini_failed

def extract_metadata_from_title(title):
    """
    Title parser that always returns metadata - never None. This is the final fallback step.
    Returns (song, artist, source)
    """
    # Try smart title parsing
    song_parsed, artist_parsed = parse_title_smart(title)
    
    if song_parsed and artist_parsed:
        log(f"Using parsed metadata: {artist_parsed} - {song_parsed}")
        # Apply universal cleaning to parsed results
        song_parsed, artist_parsed = apply_universal_song_cleaning(song_parsed, artist_parsed, "title_parsing")
        return song_parsed, artist_parsed, "title_parsing"
    
    # Conservative fallback
    log("No reliable artist/song could be parsed - using conservative fallback")
    return title, "Unknown Artist", "title_parsing"

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

def apply_universal_song_cleaning(song, artist, source):
    """Apply universal song title cleaning to metadata from ANY source."""
    if not song:
        return song, artist
    
    original_song = song
    
    # Apply the comprehensive cleaning function
    cleaned_song = clean_featuring_from_song(song)
    
    # Log the cleaning if it changed anything
    if cleaned_song != original_song:
        log(f"Universal cleaning applied to {source} result: '{original_song}' → '{cleaned_song}'")
    
    return cleaned_song, artist

def clear_gemini_failures():
    """Legacy function kept for compatibility."""
    log("Gemini failures are tracked via filename markers (_gf) and retried on restart")
    # This function is now a no-op since we always retry on restart
