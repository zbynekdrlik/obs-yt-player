# Phase 5: Google Gemini AI Metadata (Primary Source)

## Overview
Implement Google Gemini AI as the primary metadata extraction source, with enhanced Google Search grounding for accurate artist/song identification. Includes automatic retry system for failed extractions.

## Requirements from 02-requirements.md
- **Metadata Retrieval**: Primary source is Google Gemini API (required)
- Uses AI with Google Search grounding to extract artist/song
- Most accurate for complex titles
- Failed extractions marked with `_gf` for automatic retry
- Apply universal song title cleaning to results

## Key Changes in This Phase
1. **Gemini as Primary Source**: When API key is configured, Gemini is the only metadata method
2. **Google Search Grounding**: Enhanced prompts use web search for accuracy
3. **Automatic Retry System**: Failed extractions marked with `_gf` for retry
4. **Fallback to Title Parser**: When Gemini unavailable or fails
5. **No Other Metadata Sources**: Removed AcoustID and iTunes for simplicity

## Implementation

### 1. Create gemini_metadata.py module

```python
"""
Google Gemini API metadata extraction for YouTube videos.
Uses Gemini 2.5 Flash with Google Search grounding to intelligently extract artist and song information.
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
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_TIMEOUT = 30  # Increased timeout for Google Search grounding
MAX_RETRIES = 2

def extract_metadata_with_gemini(video_id: str, video_title: str, api_key: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract artist and song metadata using Google Gemini API with Google Search grounding.
    
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
    
    # Enhanced prompt with STRICT JSON requirements
    prompt = f"""Look up information about this YouTube video and extract the artist and song title:
URL: {video_url}
Title: "{video_title}"

Use Google Search to find information about this specific YouTube video URL.

CRITICAL: Respond with ONLY a valid JSON object. No explanatory text allowed.

Return EXACTLY this format:
{{"artist": "Primary Artist Name", "song": "Song Title"}}

RULES:
1. Search for the YouTube URL to find the actual artist
2. For worship/church music, identify the performing artist/band
3. Remove feat./ft./featuring from artist name
4. Remove (Official Video), (Live), etc from song titles
5. Keep "/" in multi-part titles like "Faithful Then / Faithful Now"
6. If no artist found, return empty string for artist

Examples:
- "HOLYGHOST | Sons Of Sunday" → {{"artist": "Sons Of Sunday", "song": "HOLYGHOST"}}
- "'COME RIGHT NOW' | Official Video" → {{"artist": "Planetshakers", "song": "COME RIGHT NOW"}}

REMEMBER: Return ONLY valid JSON, nothing else."""

    # Add system instruction to enforce JSON-only responses
    request_body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "tools": [{
            "google_search": {}
        }],
        "systemInstruction": {
            "parts": [{
                "text": "You are a JSON API that returns only valid JSON objects. Never include explanatory text, reasoning, or any content outside the JSON structure."
            }]
        },
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for consistent results
            "candidateCount": 1
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
                    
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if parts and 'text' in parts[0]:
                            text = parts[0]['text']
                            log(f"Gemini response for '{video_title}': {text}")
                        else:
                            log(f"Unexpected Gemini response structure: {json.dumps(result, indent=2)[:500]}")
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
                        
                        # Try to extract JSON even if there's extra text (fallback)
                        # Look for JSON object pattern
                        json_match = re.search(r'\{[^{}]*"artist"[^{}]*"song"[^{}]*\}', cleaned_text)
                        if json_match and not cleaned_text.startswith('{'):
                            log(f"Extracting JSON from mixed response")
                            cleaned_text = json_match.group(0)
                        
                        # Parse the JSON response
                        metadata = json.loads(cleaned_text)
                        artist = metadata.get('artist', '').strip()
                        song = metadata.get('song', '').strip()
                        
                        # Accept response if we have at least a song title
                        if song:
                            if artist:
                                log(f"Gemini extracted: {artist} - {song}")
                            else:
                                log(f"Gemini extracted song only: {song} (no artist found)")
                            return artist if artist else None, song
                        else:
                            log(f"Gemini response missing song title: {metadata}")
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
```

### 2. Update metadata.py
Replace the entire metadata extraction logic to use Gemini as primary:

```python
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

# ... rest of title parsing and cleaning functions remain the same
```

### 3. Create reprocess.py module

```python
"""
Reprocess videos that failed Gemini extraction on previous runs.
This module handles renaming files when Gemini succeeds on retry.
"""

import os
import threading
import time
from pathlib import Path

from logger import log
from state import (
    get_cache_dir, get_cached_videos, get_cached_video_info,
    should_stop_threads, is_tools_ready,
    add_cached_video, get_gemini_api_key, get_playlist_url
)
from metadata import get_video_metadata
from utils import sanitize_filename
import subprocess
import json

_reprocess_thread = None

def get_video_title_from_youtube(video_id):
    """Fetch video title from YouTube for a specific video ID."""
    try:
        from utils import get_ytdlp_path
        
        ytdlp_path = get_ytdlp_path()
        
        # Prepare command to get video info
        cmd = [
            ytdlp_path,
            '--get-title',
            '--no-warnings',
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        
        # Run command with hidden window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            log(f"Failed to get title for video {video_id}")
            return None
            
    except Exception as e:
        log(f"Error fetching video title: {e}")
        return None

def find_videos_to_reprocess():
    """Find all videos with _gf marker that need Gemini retry."""
    videos_to_reprocess = []
    cached_videos = get_cached_videos()
    
    for video_id, video_info in cached_videos.items():
        if video_info.get('gemini_failed', False):
            # We need to get the title - either from cache or fetch it
            title = None
            
            # First try to use the song title we have (it might be from title parsing)
            if video_info.get('song') and video_info.get('song') != 'Unknown Song':
                # Reconstruct a reasonable title from what we have
                title = f"{video_info['song']} - {video_info['artist']}"
            else:
                # Fetch the actual title from YouTube
                title = get_video_title_from_youtube(video_id)
            
            if title:
                videos_to_reprocess.append({
                    'id': video_id,
                    'title': title,
                    'current_path': video_info['path'],
                    'song': video_info['song'],
                    'artist': video_info['artist']
                })
    
    return videos_to_reprocess

def reprocess_video(video_info):
    """Attempt to reprocess a single video with Gemini."""
    video_id = video_info['id']
    title = video_info['title']
    current_path = video_info['current_path']
    
    log(f"Retrying Gemini extraction for: {title}")
    
    # Try to get metadata again (will use Gemini if API key is available)
    song, artist, metadata_source, gemini_failed = get_video_metadata(
        current_path, title, video_id
    )
    
    if not gemini_failed and metadata_source == 'Gemini':
        # Gemini succeeded! Need to rename the file
        log(f"Gemini extraction succeeded on retry: {artist} - {song}")
        
        # Generate new filename without _gf marker
        cache_dir = get_cache_dir()
        safe_song = sanitize_filename(song)
        safe_artist = sanitize_filename(artist)
        new_filename = f"{safe_song}_{safe_artist}_{video_id}_normalized.mp4"
        new_path = os.path.join(cache_dir, new_filename)
        
        # Rename the file if paths are different
        if current_path != new_path and os.path.exists(current_path):
            try:
                # Remove new path if it exists (shouldn't happen)
                if os.path.exists(new_path):
                    os.remove(new_path)
                
                # Rename the file
                os.rename(current_path, new_path)
                log(f"Renamed file: {os.path.basename(current_path)} -> {os.path.basename(new_path)}")
                
                # Update cached video info
                add_cached_video(video_id, {
                    'path': new_path,
                    'song': song,
                    'artist': artist,
                    'normalized': True,
                    'gemini_failed': False
                })
                
                return True
            except Exception as e:
                log(f"Error renaming file: {e}")
                return False
    else:
        # Gemini still failed or no API key
        if not get_gemini_api_key():
            log(f"Skipping reprocess - no Gemini API key configured")
        else:
            log(f"Gemini extraction failed again for: {title}")
        return False

def reprocess_worker():
    """Background worker to reprocess videos with failed Gemini extraction."""
    # Wait for tools to be ready
    while not is_tools_ready() and not should_stop_threads():
        time.sleep(1)
    
    if should_stop_threads():
        return
    
    # Wait a bit to ensure cache scan is complete
    time.sleep(5)
    
    # Check if Gemini API key is configured
    if not get_gemini_api_key():
        log("No Gemini API key configured - skipping reprocess of failed videos")
        return
    
    # Find videos to reprocess
    videos_to_reprocess = find_videos_to_reprocess()
    
    if not videos_to_reprocess:
        log("No videos found that need Gemini reprocessing")
        return
    
    log(f"Found {len(videos_to_reprocess)} videos to retry Gemini extraction")
    
    # Process each video
    success_count = 0
    for video_info in videos_to_reprocess:
        if should_stop_threads():
            break
        
        if reprocess_video(video_info):
            success_count += 1
        
        # Small delay between attempts
        time.sleep(0.5)
    
    if success_count > 0:
        log(f"Successfully reprocessed {success_count} videos with Gemini")
    
    log("Gemini reprocessing complete")

def start_reprocess_thread():
    """Start the reprocess thread if needed."""
    global _reprocess_thread
    
    # Only start if not already running
    if _reprocess_thread is None or not _reprocess_thread.is_alive():
        _reprocess_thread = threading.Thread(target=reprocess_worker, daemon=True)
        _reprocess_thread.start()
        log("Started Gemini reprocess thread")
```

### 4. Update download.py, normalize.py, cache.py, and state.py

See the full implementation details in the original Phase 13 document above. The key changes:
- download.py: Pass gemini_failed flag through the pipeline
- normalize.py: Add `_gf` suffix to filenames when Gemini fails
- cache.py: Recognize `_gf` marker when scanning cache
- state.py: Add Gemini API key storage functions

### 5. Update main script properties

Add Gemini API key field to ytfast.py:

```python
def script_properties():
    """Define script properties for OBS."""
    props = obs.obs_properties_create()
    
    # Playlist URL
    obs.obs_properties_add_text(props, "playlist_url", "YouTube Playlist URL", obs.OBS_TEXT_DEFAULT)
    
    # Cache directory
    obs.obs_properties_add_path(props, "cache_dir", "Cache Directory", obs.OBS_PATH_DIRECTORY, None, state.get_cache_dir())
    
    # Gemini API Key (REQUIRED)
    obs.obs_properties_add_text(props, "gemini_api_key", "Google Gemini API Key (Required)", obs.OBS_TEXT_PASSWORD)
    
    # Sync button
    obs.obs_properties_add_button(props, "sync_now", "Sync Playlist Now", sync_playlist_manual)
    
    return props
```

## Testing Steps

1. **Test with Gemini API Key**:
   - Add valid Gemini API key in script properties
   - Add new videos to playlist
   - Verify Gemini extracts metadata correctly
   - Check logs show "Metadata from Gemini"

2. **Test Gemini Failure**:
   - Temporarily use invalid API key or disconnect network
   - Process new video
   - Verify file gets `_gf` marker
   - Check logs show fallback to title parsing

3. **Test Automatic Retry**:
   - Fix API key/network
   - Restart OBS
   - Verify reprocess thread finds failed videos
   - Check file is renamed without `_gf`
   - Verify metadata is updated

4. **Test Without API Key**:
   - Remove API key
   - Process videos
   - Verify title parser is used
   - No `_gf` markers should be added

## Success Criteria

- ✅ Gemini is primary metadata source when configured
- ✅ Failed extractions marked with `_gf` in filename
- ✅ Automatic retry on startup for failed videos
- ✅ Successful retry results in file rename
- ✅ Title parser provides reliable fallback
- ✅ All sources apply universal cleaning
- ✅ System works without API key (using title parser)

## Notes

- Gemini 2.5 Flash with Google Search grounding provides excellent accuracy
- Free tier includes generous limits for personal use
- The `_gf` marker system ensures no metadata is permanently lost
- Reprocessing happens automatically without user intervention
- This is now the ONLY metadata extraction method (no AcoustID or iTunes)