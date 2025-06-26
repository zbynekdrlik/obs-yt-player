"""
Metadata extraction module for OBS YouTube Player.
Handles Gemini AI extraction and fallback parsing.
"""

from logger import log
from state import get_gemini_failures

def clear_gemini_failures():
    """Clear the Gemini failures cache."""
    failures = get_gemini_failures()
    if failures:
        count = len(failures)
        failures.clear()
        log(f"Cleared {count} Gemini failure markers")

def extract_metadata_gemini(video_title, video_id, api_key):
    """Extract metadata using Gemini AI."""
    # TODO: Implement Gemini API integration
    return None

def parse_title_fallback(title):
    """Parse title using pattern matching as fallback."""
    # TODO: Implement title parsing logic
    # For now, return basic metadata
    return {
        'song': title,
        'artist': 'Unknown Artist'
    }

def clean_metadata(metadata):
    """Clean and standardize metadata."""
    # TODO: Implement metadata cleaning
    return metadata

def extract_metadata(video_info, gemini_api_key=None):
    """Extract metadata from video using available methods."""
    video_id = video_info.get('id')
    title = video_info.get('title', '')
    
    # Try Gemini if API key available
    if gemini_api_key:
        metadata = extract_metadata_gemini(title, video_id, gemini_api_key)
        if metadata:
            return clean_metadata(metadata)
    
    # Fallback to title parsing
    metadata = parse_title_fallback(title)
    return clean_metadata(metadata)

def get_current_video_from_media_source():
    """Get current video ID from media source filename."""
    # TODO: Implement getting current video from OBS media source
    return None
