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
    is_video_being_processed, get_cached_video_info,
    get_current_playback_video_id
)
from utils import validate_youtube_id

def validate_video_file(file_path):
    """Check if video file is valid and playable."""
    try:
        if not os.path.exists(file_path):
            return False
        
        # Check minimum file size (1MB)
        file_size = os.path.getsize(file_path)
        if file_size < 1024 * 1024:
            return False
            
        # Check if it's a valid video file by extension
        valid_extensions = ['.mp4', '.webm', '.mkv']
        if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
            return False
            
        return True
    except Exception:
        return False

def scan_existing_cache():
    """Scan cache directory for existing normalized videos."""
    cache_path = Path(get_cache_dir())
    if not cache_path.exists():
        return
    
    log("Scanning cache for existing videos...")
    found_count = 0
    debug_count = 0
    skipped_count = 0
    
    # Look for normalized videos
    for file_path in cache_path.glob("*_normalized.mp4"):
        debug_count += 1
        
        # Validate the video file
        if not validate_video_file(str(file_path)):
            log(f"Skipping invalid video file: {file_path.name}")
            skipped_count += 1
            continue
            
        try:
            # Extract video ID from filename
            # Format: song_artist_videoId_normalized.mp4
            # Video IDs can contain underscores, so we need careful parsing
            filename = file_path.stem  # Remove .mp4
            
            # Must end with _normalized
            if not filename.endswith('_normalized'):
                continue
                
            # Remove _normalized suffix
            without_suffix = filename[:-11]  # len('_normalized') = 11
            
            # Find video ID by searching from the end
            # YouTube IDs are 11 characters and can contain letters, numbers, - and _
            parts = without_suffix.split('_')
            
            # Try to find a valid YouTube ID from the end
            video_id = None
            for i in range(len(parts) - 1, -1, -1):
                # Try combining parts to form an 11-character ID
                for j in range(i, len(parts)):
                    potential_id = '_'.join(parts[i:j+1])
                    if validate_youtube_id(potential_id):
                        video_id = potential_id
                        # Everything before this is song_artist
                        remaining = '_'.join(parts[:i])
                        break
                if video_id:
                    break
            
            if not video_id:
                log(f"Could not extract video ID from: {filename}")
                continue
            
            # Try to extract metadata from remaining part
            # The remaining part is song_artist
            if remaining:
                # Try to split into song and artist
                # The last part before video ID should be artist
                remaining_parts = remaining.rsplit('_', 1)
                if len(remaining_parts) == 2:
                    song, artist = remaining_parts
                else:
                    song = remaining
                    artist = "Unknown Artist"
            else:
                song = "Unknown Song"
                artist = "Unknown Artist"
            
            # Add to cached videos
            add_cached_video(video_id, {
                'path': str(file_path),
                'song': song.replace('_', ' '),
                'artist': artist.replace('_', ' '),
                'normalized': True,
                'gemini_failed': False  # Default for existing cache
            })
            found_count += 1
            
            # Debug log for first few files
            if debug_count <= 3:
                log(f"Scanned: {filename} -> ID: {video_id}, Song: {song}, Artist: {artist}")
                        
        except Exception as e:
            log(f"Error scanning file {file_path}: {e}")
    
    if found_count > 0:
        log(f"Found {found_count} existing videos in cache")
    if skipped_count > 0:
        log(f"Skipped {skipped_count} invalid video files")

def cleanup_removed_videos():
    """Remove videos that are no longer in playlist."""
    playlist_ids = get_playlist_video_ids()
    cached_videos = get_cached_videos()
    
    # Find videos to remove
    videos_to_remove = []
    current_playing_id = get_current_playback_video_id()
    
    for video_id in cached_videos:
        if video_id not in playlist_ids:
            # Check if it's currently playing
            if video_id == current_playing_id:
                log(f"Skipping removal of currently playing video: {video_id}")
            else:
                videos_to_remove.append(video_id)
    
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