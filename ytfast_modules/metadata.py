"""
Metadata extraction for OBS YouTube Player (Windows-only).
Handles Gemini AI, AcoustID fingerprinting, iTunes search, and title parsing.
"""

import os
import re
import json
import subprocess
import urllib.request
import urllib.parse

from config import ACOUSTID_API_KEY, ACOUSTID_ENABLED, SCRIPT_VERSION
from logger import log
from utils import get_fpcalc_path, format_duration
import gemini_metadata
import state

def get_video_metadata(filepath, title, video_id=None):
    """
    Main metadata extraction function.
    Tries Gemini first (if configured), then AcoustID, iTunes, and title parsing.
    Always returns (song, artist, source) - never None.
    """
    # NEW: Try Gemini FIRST if API key is configured
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
            return song, artist, 'Gemini'
    
    # If Gemini fails or not configured, try AcoustID
    song, artist = get_acoustid_metadata(filepath)
    metadata_source = "AcoustID" if (song and artist) else None
    
    # Apply universal cleaning to AcoustID results if found
    if song and artist:
        song, artist = apply_universal_song_cleaning(song, artist, "AcoustID")
        return song, artist, metadata_source
    
    # If AcoustID fails, try title-based extraction (iTunes + parsing)
    song, artist, metadata_source = extract_metadata_from_title(title)
    
    return song, artist, metadata_source

def get_acoustid_metadata(filepath):
    """Query AcoustID for metadata using audio fingerprint."""
    if not ACOUSTID_ENABLED:
        log("AcoustID disabled, skipping fingerprinting")
        return None, None
        
    try:
        # Run fpcalc to generate fingerprint
        cmd = [
            get_fpcalc_path(),
            '-json',
            '-length', '120',  # Analyze first 2 minutes
            filepath
        ]
        
        # Hide console window on Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            startupinfo=startupinfo,
            timeout=30
        )
        
        if result.returncode != 0:
            log(f"fpcalc failed: {result.stderr}")
            return None, None
            
        # Parse fingerprint data
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"Failed to parse fpcalc JSON output: {e}")
            log(f"fpcalc output: {result.stdout[:200]}...")
            return None, None
            
        fingerprint = data.get('fingerprint')
        duration = data.get('duration')
        
        if not fingerprint or not duration:
            log(f"Missing fingerprint or duration in fpcalc output")
            return None, None
            
        # Format duration for logging
        duration_formatted = format_duration(duration)
        log(f"Generated fingerprint, duration: {duration_formatted}")
        
        # Query AcoustID API
        return query_acoustid(fingerprint, duration)
        
    except subprocess.TimeoutExpired:
        log("fpcalc timeout after 30 seconds")
        return None, None
    except Exception as e:
        log(f"AcoustID fingerprinting error: {e}")
        return None, None

def query_acoustid(fingerprint, duration):
    """Query AcoustID API for metadata using urllib."""
    url = 'https://api.acoustid.org/v2/lookup'
    params = {
        'client': ACOUSTID_API_KEY,
        'fingerprint': fingerprint,
        'duration': int(duration),
        'meta': 'recordings'
    }
    
    try:
        # Build URL with parameters
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # Log the request details for debugging (but not the full fingerprint)
        duration_formatted = format_duration(duration)
        log(f"AcoustID request - duration: {duration_formatted}, fingerprint length: {len(fingerprint)}")
        
        # Make request with User-Agent
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
        
        # Log API response status
        status = data.get('status', 'unknown')
        if status != 'ok':
            log(f"AcoustID API status: {status}")
            if 'error' in data:
                log(f"AcoustID error: {data['error']}")
            return None, None
        
        # Extract best match
        results = data.get('results', [])
        log(f"AcoustID returned {len(results)} results")
        
        for result in results:
            if result.get('recordings'):
                # Get first recording with good confidence
                confidence = result.get('score', 0)
                if confidence < 0.4:  # Skip low confidence matches
                    log(f"Skipping low confidence match: {confidence:.2f}")
                    continue
                    
                for recording in result['recordings']:
                    artists = recording.get('artists', [])
                    if artists and recording.get('title'):
                        artist = artists[0]['name']
                        title = recording['title']
                        log(f"AcoustID match (confidence: {confidence:.2f}): {artist} - {title}")
                        return title, artist
        
        log("No suitable AcoustID matches found")
        return None, None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No response body'
        log(f"AcoustID API HTTP error: {e.code} {e.reason}")
        log(f"Error response: {error_body[:200]}")
    except urllib.error.URLError as e:
        log(f"AcoustID API connection error: {e}")
    except Exception as e:
        log(f"AcoustID API error: {e}")
    
    return None, None

def extract_metadata_from_title(title):
    """
    Enhanced title parser that tries iTunes then falls back to parsing.
    Always returns metadata - never None. This is the final fallback step.
    Returns (song, artist, source)
    """
    # First, try smart title parsing to extract expected artist
    song_parsed, artist_parsed = parse_title_smart(title)
    
    # Try iTunes search
    song_itunes, artist_itunes = search_itunes_metadata(title, expected_artist=artist_parsed)
    if song_itunes and artist_itunes:
        # Apply universal cleaning to iTunes results
        song_itunes, artist_itunes = apply_universal_song_cleaning(song_itunes, artist_itunes, "iTunes")
        return song_itunes, artist_itunes, "iTunes"
    
    # If iTunes fails but we have good parsed results, use them
    if song_parsed and artist_parsed:
        log(f"Using parsed metadata: {artist_parsed} - {song_parsed}")
        # Apply universal cleaning to parsed results
        song_parsed, artist_parsed = apply_universal_song_cleaning(song_parsed, artist_parsed, "title_parsing")
        return song_parsed, artist_parsed, "title_parsing"
    
    # Conservative fallback
    log("No reliable artist/song could be parsed - using conservative fallback")
    return title, "Unknown Artist", "title_parsing"

def search_itunes_metadata(search_query, expected_artist=None):
    """Search iTunes API for song metadata."""
    try:
        original_query = search_query
        
        # Clean up search query
        search_query = search_query.lower()
        
        # Remove common video suffixes
        for suffix in ['official music video', 'official video', 'lyrics', 'live', 
                       'worship together session', 'official', 'music video', 'hd', '4k',
                       '+ the choir room', 'the choir room', 'video oficial', '(video oficial)',
                       '[official]', '(official)', 'en vivo', '(en vivo)', 'worship cover',
                       'songs for church', 'live at chapel', 'revival', 'feat.', 'ft.']:
            search_query = search_query.replace(suffix, '').strip()
        
        # Replace multiple separators with spaces
        search_query = search_query.replace('//', ' ')
        search_query = search_query.replace('|', ' ')
        search_query = search_query.replace(' - ', ' ')
        
        # Remove extra whitespace
        search_query = ' '.join(search_query.split())
        
        log(f"iTunes search - Query: '{search_query}', Expected artist: '{expected_artist}'")
        
        # URL encode the search query
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&limit=25"
        
        # Make request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get('resultCount', 0) == 0:
            log("No iTunes results found")
            return None, None
        
        # Try to find best match
        best_match = find_best_itunes_match(data['results'], search_query, expected_artist, original_query)
        if best_match:
            song, artist = best_match
            log(f"iTunes match: {artist} - {song}")
            return song, artist
        
        log("No suitable iTunes matches found")
        return None, None
        
    except Exception as e:
        log(f"iTunes search error: {e}")
        return None, None

def find_best_itunes_match(results, search_query, expected_artist=None, original_query=""):
    """Find best iTunes match with genre validation."""
    search_words = set(w for w in search_query.split() if len(w) > 2)
    
    if len(search_words) < 2:
        return None
    
    best_match = None
    best_score = 0
    
    for result in results:
        artist = result.get('artistName', '')
        song = result.get('trackName', '')
        
        if not artist or not song:
            continue
        
        # Check for genre mismatch
        if is_genre_mismatch(search_query, artist.lower(), song.lower(), original_query):
            log(f"Rejected iTunes match for genre mismatch: {artist} - {song}")
            continue
        
        # Score based on word matching
        song_lower = song.lower()
        artist_lower = artist.lower()
        
        # Count matches in song title (weighted more)
        song_matches = sum(2 for word in search_words if word in song_lower)
        
        # Count matches in artist name
        artist_matches = sum(1 for word in search_words if word in artist_lower)
        
        # Bonus for artist consistency if we have expected artist
        artist_bonus = 0
        if expected_artist:
            expected_lower = expected_artist.lower()
            expected_words = set(w for w in expected_lower.split() if len(w) > 2)
            result_words = set(w for w in artist_lower.split() if len(w) > 2)
            if expected_words.intersection(result_words):
                artist_bonus = 3
        
        total_score = song_matches + artist_matches + artist_bonus
        
        # Stricter validation
        min_required = max(4, len(search_words) // 2)
        
        # Require meaningful song title overlap
        if song_matches == 0 and artist_bonus == 0:
            continue
        
        if total_score >= min_required and total_score > best_score:
            best_match = (song, artist)
            best_score = total_score
    
    return best_match

def is_genre_mismatch(search_query, artist_lower, song_lower, original_query=""):
    """Enhanced genre mismatch detection."""
    search_lower = search_query.lower()
    original_lower = original_query.lower()
    
    # Worship/Christian music indicators
    worship_indicators = [
        'worship', 'church', 'praise', 'glory', 'lord', 'god', 'jesus', 'christ', 'holy', 
        'prayer', 'faith', 'blessed', 'heaven', 'salvation', 'hallelujah', 'amen',
        'planetshakers', 'elevation', 'hillsong', 'bethel', 'gateway', 'lakewood',
        'revival', 'presence', 'sanctuary', 'almighty', 'sovereign', 'redeemer',
        'savior', 'emmanuel', 'hosanna', 'christian', 'gospel'
    ]
    
    # Check if search suggests worship context
    has_worship_context = any(indicator in search_lower for indicator in worship_indicators)
    has_worship_context = has_worship_context or any(indicator in original_lower for indicator in worship_indicators)
    
    # Known problematic artist patterns
    problematic_artists = [
        'level 42', 'physical presence', 'worship songs on the piano',
        'piano tribute', 'instrumental'
    ]
    
    # Check result text for problematic patterns
    result_text = f"{artist_lower} {song_lower}".lower()
    
    # Check for known problematic artists
    if any(problematic in result_text for problematic in problematic_artists):
        if has_worship_context:
            return True
    
    # Check for instrumental/cover mismatches
    original_words = original_lower.split()
    if any(artist in original_words for artist in ['planetshakers', 'elevation', 'hillsong', 'bethel']):
        if 'instrumental' in result_text or 'karaoke' in result_text:
            return True
    
    return False

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
