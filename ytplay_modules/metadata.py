"""Metadata extraction for OBS YouTube Player."""

from logger import log

def clear_gemini_failures():
    """Clear Gemini failure cache."""
    log("Clearing Gemini failure cache")

def extract_metadata(video_id, title):
    """Extract metadata from video title."""
    # Placeholder implementation
    return {
        'song': 'Unknown Song',
        'artist': 'Unknown Artist',
        'gemini_failed': False
    }