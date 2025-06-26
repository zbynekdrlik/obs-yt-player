"""
Utility functions for OBS YouTube Player.
"""

import os
import re
import unicodedata

def sanitize_filename(filename):
    """Sanitize filename for filesystem compatibility."""
    # Replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure it's not empty
    if not filename:
        filename = 'unknown'
    
    return filename

def validate_youtube_id(video_id):
    """Validate YouTube video ID format."""
    if not video_id or len(video_id) != 11:
        return False
    # YouTube IDs contain letters, numbers, hyphens and underscores
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

def format_time(seconds):
    """Format seconds into MM:SS or HH:MM:SS format."""
    if seconds < 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
