# Phase 06 – Title Parser Fallback

## Goal
Implement YouTube title parsing as a fallback metadata extraction method when AcoustID fails. This ensures all videos get reasonable metadata even when they're not in the AcoustID database.

## Version Increment
**This phase adds new features** → Increment MINOR version from current version

## Requirements Reference
This phase implements the fallback metadata method from `02-requirements.md`:
- Fallback: parse YouTube title
- Log transformation clearly
- Handle various title formats intelligently

## Implementation Details

### 1. YouTube Title Parser
```python
def parse_youtube_title(title):
    """Parse YouTube title to extract artist and song."""
    # First, clean the title
    cleaned_title = title
    
    # Remove common suffixes in parentheses or brackets
    paren_regex = r'\s*\([^)]*\)\s*$'
    bracket_regex = r'\s*\[[^\]]*\]\s*$'
    
    cleaned_title = re.sub(paren_regex, '', cleaned_title)
    cleaned_title = re.sub(bracket_regex, '', cleaned_title)
    
    # Known artist patterns - check if title contains known artists
    known_artists = {
        'planetshakers': 'Planetshakers',
        'sons of sunday': 'Sons Of Sunday',
        'hillsong': 'Hillsong',
        'bethel': 'Bethel',
        'elevation': 'Elevation Worship',
        'tauren wells': 'Tauren Wells',
        'michael bethany': 'Michael Bethany',
        'dwan hill': 'Dwan Hill'
    }
    
    # Check for known artists in the title
    lower_title = cleaned_title.lower()
    detected_artist = None
    for artist_key, artist_name in known_artists.items():
        if artist_key in lower_title:
            detected_artist = artist_name
            break
    
    # Special handling for multiple separators
    if cleaned_title.count('|') >= 2:
        parts = [p.strip() for p in cleaned_title.split('|')]
        # Usually format is "Song | Artist | Extra"
        if len(parts) >= 2:
            song = parts[0]
            artist = parts[1]
            # Clean up artist if it contains extra info
            artist = re.sub(r'\s*(ft\.|feat\.|featuring).*$', '', artist, flags=re.IGNORECASE)
            return song, artist
    
    # Common patterns in YouTube titles
    patterns = [
        # Artist - Song (including various dash types)
        (r'^(.*?)\s*[-–—]\s*(.*)$', 'hyphen'),
        # Artist | Song
        (r'^(.*?)\s*\|\s*(.*)$', 'pipe'),
        # Artist : Song
        (r'^(.*?)\s*:\s*(.*)$', 'colon'),
        # "Song" by Artist
        (r'^"(.+?)"\s+by\s+(.+)$', 'by_format', True),  # True = swap order
        # Song // Artist (common in worship music)
        (r'^(.*?)\s*//\s*(.*)$', 'double_slash'),
    ]
    
    for pattern_info in patterns:
        pattern = pattern_info[0]
        name = pattern_info[1]
        swap = pattern_info[2] if len(pattern_info) > 2 else False
        
        match = re.match(pattern, cleaned_title, re.IGNORECASE)
        if match:
            if swap:
                song = match.group(1).strip()
                artist = match.group(2).strip()
            else:
                part1 = match.group(1).strip()
                part2 = match.group(2).strip()
                
                # Smart detection logic
                # Apply intelligent parsing based on pattern and content
                song, artist = determine_artist_song(
                    part1, part2, detected_artist, name
                )
            
            # Additional cleanup
            song = clean_metadata(song)
            artist = clean_metadata(artist)
            
            log(f"Parsed using {name} pattern: Artist='{artist}', Song='{song}'", "DEBUG")
            return song, artist
    
    # If no pattern matches, use cleaned title as song name
    return cleaned_title, "Unknown Artist"
```

### 2. Smart Detection Logic
```python
def determine_artist_song(part1, part2, detected_artist, pattern_name):
    """Intelligently determine which part is artist and which is song."""
    # If we have a known artist, use that
    if detected_artist:
        if detected_artist.lower() in part1.lower():
            return part2, part1  # song, artist
        elif detected_artist.lower() in part2.lower():
            return part1, part2  # song, artist
    
    # Heuristic detection
    part1_lower = part1.lower()
    part2_lower = part2.lower()
    
    # Check for metadata keywords in part2
    if any(keyword in part2_lower for keyword in ['official', 'video', 'audio', 'lyrics', 'session', 'version']):
        # Part2 has metadata, so part1 is likely the song
        artist = re.sub(r'\s*(official|video|audio|lyrics|session|version).*$', '', part2, flags=re.IGNORECASE)
        return part1, artist
    
    # Check if part1 is ALL CAPS (common for song titles)
    if part1.isupper() and not part2.isupper():
        return part1, part2  # song, artist
    
    # Check for artist suffixes
    if any(part2_lower.endswith(suffix) for suffix in [' band', ' music', ' worship']):
        return part1, part2  # song, artist
    
    # Check for featuring info
    if 'ft.' in part2_lower or 'feat.' in part2_lower or 'featuring' in part2_lower:
        return part2, part1  # song, artist (main artist is part1)
    
    # Default based on pattern type
    if pattern_name in ['pipe', 'double_slash']:
        # These patterns often have Song | Artist or Song // Artist
        return part1, part2
    else:
        # Hyphen usually Artist - Song
        return part2, part1
```

### 3. Metadata Cleanup
```python
def clean_metadata(text):
    """Clean up metadata text."""
    # Remove quotes
    text = text.strip('"\'')
    
    # Remove Official Audio/Video/etc
    official_regex = r'\s*(Official\s*(Audio|Video|Music\s*Video|Lyric\s*Video))?\s*$'
    text = re.sub(official_regex, '', text, flags=re.IGNORECASE)
    
    # Remove session info
    text = re.sub(r'\s*\|\s*Worship Together Session\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Worship Together Session\s*$', '', text, flags=re.IGNORECASE)
    
    # Final cleanup
    text = re.sub(r'\s*Official\s*$', '', text, flags=re.IGNORECASE).strip()
    
    # Handle featuring info
    if 'ft.' in text.lower() or 'feat.' in text.lower():
        # Extract and format featuring info properly
        feat_match = re.search(r'\s*(ft\.|feat\.|featuring)\s*(.*)$', text, flags=re.IGNORECASE)
        if feat_match:
            main_part = re.sub(r'\s*(ft\.|feat\.|featuring).*$', '', text, flags=re.IGNORECASE)
            featuring = feat_match.group(2).strip()
            if featuring:
                text = f"{main_part} feat. {featuring}"
    
    return text.strip()
```

### 4. Updated Metadata Wrapper
```python
def get_metadata(filepath, yt_title, video_id):
    """Get song and artist metadata using AcoustID or YouTube title."""
    log(f"Getting metadata for: {yt_title}", "DEBUG")
    
    # Try AcoustID first (from Phase 5)
    song, artist = get_acoustid_metadata(filepath)
    if song and artist and song != "Unknown Title":
        log(f"Metadata via AcoustID: '{yt_title}' → Artist: '{artist}', Song: '{song}'", "NORMAL")
        return song, artist
    
    # Fallback to parsing YouTube title
    song, artist = parse_youtube_title(yt_title)
    log(f"Metadata via title parser: '{yt_title}' → Artist: '{artist}', Song: '{song}'", "NORMAL")
    return song, artist
```

### 5. Integration with Process Worker
Update process_videos_worker to use complete metadata extraction:
```python
# In process_videos_worker, after download:
# Extract metadata (AcoustID + fallback)
song, artist = get_metadata(temp_path, title, video_id)

# TODO: Continue to normalization (Phase 7)
# Pass song, artist, and temp_path to normalization phase
```

## Key Considerations
- Handle various separator patterns (-, |, :, //, "by")
- Multiple pipe separators need special handling
- Known artist list helps determine correct order
- ALL CAPS often indicates song title
- Clean metadata keywords (Official, Video, etc.)
- Handle featuring artists properly
- Different patterns have different default orders
- Log parsing pattern used for debugging

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` constant
- [ ] Implement parse_youtube_title function
- [ ] Implement determine_artist_song helper
- [ ] Implement clean_metadata helper
- [ ] Update get_metadata wrapper
- [ ] Update process_videos_worker integration
- [ ] Add known artist list (expandable)
- [ ] Handle various dash types (-, –, —)
- [ ] Handle double slash (//) pattern
- [ ] Clean up session info and metadata

## Testing Before Commit
1. Test pattern: "Joy Of The Lord | Planetshakers Official Music Video"
   - Expected: Artist="Planetshakers", Song="Joy Of The Lord"
2. Test pattern: "HOLYGHOST | Sons Of Sunday"
   - Expected: Artist="Sons Of Sunday", Song="HOLYGHOST"
3. Test pattern: "Let The Church Sing | Tauren Wells | Worship Together Session"
   - Expected: Artist="Tauren Wells", Song="Let The Church Sing"
4. Test pattern: "Ask Me Why // Michael Bethany Ft. Dwan Hill"
   - Expected: Artist="Michael Bethany Ft. Dwan Hill", Song="Ask Me Why"
5. Test pattern: "Artist - Song (Official Video)"
6. Test pattern: '"Song Name" by Artist Name'
7. Test ALL CAPS detection
8. Test featuring artist handling
9. Test with no recognizable pattern
10. Test with multiple separators
11. **Verify version was incremented**
12. **Verify logs show parsing pattern used**

## Commit
After successful testing, commit with message:  
> *"Add YouTube title parser fallback (Phase 6)"*

*After verification, proceed to Phase 07.*