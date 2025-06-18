"""
Cache management for OBS YouTube Player.
Handles existing cache scanning and cleanup.
"""

import os
from pathlib import Path

from logger import log
from state import (
    get_cache_dir, get_cached_videos, add_cached_video, 
    remove_cached_video, get_playlist_video_ids,
    is_video_being_processed, get_cached_video_info
)
from utils import validate_youtube_id

def scan_existing_cache():
    """Scan cache directory for existing normalized videos."""
    cache_path = Path(get_cache_dir())
    if not cache_path.exists():
        return
    
    log("Scanning cache for existing videos...")
    found_count = 0
    
    # Look for normalized videos
    for file_path in cache_path.glob("*_normalized.mp4"):
        try:
            # Extract video ID from filename
            # Format: song_artist_videoId_normalized.mp4
            filename = file_path.stem  # Remove .mp4
            parts = filename.rsplit('_', 2)  # Split from right
            
            if len(parts) >= 3 and parts[2] == 'normalized':
                video_id = parts[1]
                
                # Validate YouTube ID format
                if not validate_youtube_id(video_id):
                    continue
                
                # Try to extract metadata from filename
                metadata_parts = parts[0].split('_', 1)
                if len(metadata_parts) == 2:
                    song, artist = metadata_parts
                else:
                    song = parts[0]
                    artist = "Unknown Artist"
                
                # Add to cached videos
                add_cached_video(video_id, {
                    'path': str(file_path),
                    'song': song.replace('_', ' '),
                    'artist': artist.replace('_', ' '),
                    'normalized': True
                })
                found_count += 1
                        
        except Exception as e:
            log(f"Error scanning file {file_path}: {e}")
    
    if found_count > 0:
        log(f"Found {found_count} existing videos in cache")

def cleanup_removed_videos():
    """Remove videos that are no longer in playlist."""
    playlist_ids = get_playlist_video_ids()
    cached_videos = get_cached_videos()
    
    # Find videos to remove
    videos_to_remove = []
    for video_id in cached_videos:
        if video_id not in playlist_ids:
            # Check if it's currently playing
            if not is_video_being_processed(video_id):
                videos_to_remove.append(video_id)
            else:
                log(f"Skipping removal of currently playing video: {video_id}")
    
    # Remove videos
    for video_id in videos_to_remove:
        video_info = get_cached_video_info(video_id)
        if video_info:
            try:
                if os.path.exists(video_info['path']):
                    os.remove(video_info['path'])
                remove_cached_video(video_id)
                log(f"Removed: {video_info['artist']} - {video_info['song']}")
            except Exception as e:
                log(f"Error removing video {video_id}: {e}")
    
    if videos_to_remove:
        log(f"Cleaned up {len(videos_to_remove)} removed videos")

def cleanup_temp_files():
    """Clean up any temporary files."""
    try:
        cache_path = Path(get_cache_dir())
        if cache_path.exists():
            # Clean up .part files
            for part_file in cache_path.glob("*.part"):
                try:
                    os.remove(part_file)
                    log(f"Removed temp file: {part_file.name}")
                except Exception as e:
                    log(f"Error removing {part_file}: {e}")
            
            # Clean up _temp.mp4 files
            for temp_file in cache_path.glob("*_temp.mp4"):
                try:
                    os.remove(temp_file)
                    log(f"Removed temp file: {temp_file.name}")
                except Exception as e:
                    log(f"Error removing {temp_file}: {e}")
                    
    except Exception as e:
        log(f"Error during temp file cleanup: {e}")
