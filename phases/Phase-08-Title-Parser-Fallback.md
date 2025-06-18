# Phase 08 – Title Parser Fallback

## Goal
Implement smart title parsing as a fallback when online metadata sources (AcoustID, iTunes) fail. This ensures every video gets reasonable metadata even without online matches.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.7.0 to 1.8.0)

## Requirements Reference
This phase implements the fallback metadata extraction from `02-requirements.md`:
- Parse YouTube titles when online sources fail
- Log the transformation for debugging
- Handle various title formats intelligently

## Implementation Details

### 1. Title Parsing Function
```python
def parse_title_smart(title):
    """
    Smart title parser that handles various YouTube title formats.
    Returns (song, artist) or (None, None)
    """
    if not title:
        return None, None
        
    # Log original title
    log(f"Title parser - Original: '{title}'")
    
    # Clean the title
    cleaned = title.strip()
    
    # First check for special patterns that indicate artist
    # Pattern 1: "Song | Artist" or "Song | Artist feat. X"
    pipe_match = re.match(r'^([^|]+)\s*\|\s*([^|]+?)(?:\s*(?:Official|Music|Video|Live|feat\.|ft\.)|$)', cleaned, re.IGNORECASE)
    if pipe_match:
        song = pipe_match.group(1).strip()
        artist = pipe_match.group(2).strip()
        # Clean up artist name
        for suffix in ['Official Music Video', 'Official Video', 'Music Video', 'Official', 'Video', 'Live']:
            artist = re.sub(f'\\s*{suffix}.*', '', artist, flags=re.IGNORECASE)
        if song and artist and len(artist) > 2:
            song = clean_featuring_from_song(song)
            log(f"Title parser - Pipe pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Pattern 2: "Artist - Song" (most common)
    dash_match = re.match(r'^([^-]+?)\s*-\s*([^-]+?)(?:\s*\(|\s*\[|$)', cleaned)
    if dash_match:
        part1 = dash_match.group(1).strip()
        part2 = dash_match.group(2).strip()
        
        # Check if this looks like "Artist - Song" pattern
        # Usually artist names are shorter and don't contain certain keywords
        song_keywords = ['official', 'video', 'lyrics', 'live', 'feat', 'ft.', 'audio']
        if any(keyword in part2.lower() for keyword in song_keywords):
            # Part2 likely contains song + extra info
            artist = part1
            song = part2
        else:
            # Standard "Artist - Song"
            artist = part1
            song = part2
        
        # Clean up
        song = clean_featuring_from_song(song)
        # Remove video suffixes from song
        for suffix in ['Official Music Video', 'Official Video', 'Music Video', 'Official', 'Video', 'Live', 'Audio']:
            song = re.sub(f'\\s*[\\(\\[]?{suffix}[\\)\\]]?', '', song, flags=re.IGNORECASE).strip()
        
        if song and artist and len(artist) > 2:
            log(f"Title parser - Dash pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Pattern 3: Check for worship/church patterns
    worship_match = re.match(r'^(.+?)\s*\|\s*([\w\s]+?)(?:\s*\(worship.*?\))?', cleaned, re.IGNORECASE)
    if worship_match and 'worship' in cleaned.lower():
        song = worship_match.group(1).strip()
        artist = worship_match.group(2).strip()
        # Remove common suffixes
        artist = re.sub(r'\s*\(.*?\)\s*', '', artist, flags=re.IGNORECASE)
        if song and artist and len(artist) > 2:
            log(f"Title parser - Worship pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Remove common video suffixes before further parsing
    suffixes_to_remove = [
        'official music video', 'official video', 'official audio',
        'music video', 'lyrics video', 'lyric video', 'lyrics',
        'hd', '4k', 'live', 'acoustic', 'cover', 'remix',
        'feat.', 'ft.', 'featuring', '(audio)', '[audio]',
        'worship together session', 'official', 'video',
        'video oficial', '(video oficial)', 'en vivo', '(en vivo)',
        'songs for church', 'live at chapel'
    ]
    
    # Make lowercase for suffix matching
    cleaned_lower = cleaned.lower()
    for suffix in suffixes_to_remove:
        # Remove suffix with various bracket types
        for bracket in ['()', '[]', '{}']:
            pattern = f"{bracket[0]}{suffix}{bracket[1]}"
            cleaned_lower = cleaned_lower.replace(pattern, '')
        # Remove suffix at end of string
        if cleaned_lower.endswith(suffix):
            cleaned_lower = cleaned_lower[:-len(suffix)].strip()
    
    # Apply case changes back
    if len(cleaned_lower) < len(cleaned):
        cleaned = cleaned[:len(cleaned_lower)]
    
    log(f"Title parser - After cleaning: '{cleaned}'")
    
    # Try other separator patterns
    separators = [
        ' – ',     # Em dash variant
        ' — ',     # En dash variant  
        ' // ',    # Double slash
        ': ',      # Colon separator
        ' by ',    # "Song by Artist"
    ]
    
    # Check each separator
    for sep in separators:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)  # Split only on first occurrence
            if len(parts) == 2:
                part1, part2 = parts[0].strip(), parts[1].strip()
                
                if sep == ' by ':
                    # "Song by Artist" pattern
                    song, artist = part1, part2
                else:
                    # Default assumption: Artist - Song
                    artist, song = part1, part2
                
                # Clean up featuring artists from song title
                song = clean_featuring_from_song(song)
                
                if song and artist and len(artist) > 2:
                    log(f"Title parser - Found separator '{sep}': Artist='{artist}', Song='{song}'")
                    return song, artist
    
    # Pattern: Quoted song title
    quote_match = re.search(r'[""''](.*?)["'']', cleaned)
    if quote_match:
        song = quote_match.group(1)
        # Remove the quoted part to find artist
        artist = cleaned.replace(quote_match.group(0), '').strip()
        if artist and song and len(artist) > 2:
            log(f"Title parser - Quote pattern: Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Unable to parse - return None to avoid bad metadata
    log(f"Title parser - Unable to parse title reliably")
    return None, None
```

### 2. Update Metadata Extraction Wrapper
```python
def extract_metadata_from_title(title):
    """
    Enhanced title parser that tries iTunes then falls back to parsing.
    Always returns metadata - never None. This is the final fallback step.
    Returns (song, artist, source)
    """
    # First, try smart title parsing to extract expected artist
    song_parsed, artist_parsed = parse_title_smart(title)
    
    # Try iTunes search with multiple strategies:
    # 1. If we have parsed artist, try strict matching
    # 2. Always try relaxed matching regardless of parsing success
    song_itunes, artist_itunes = search_itunes_metadata(title, expected_artist=artist_parsed)
    if song_itunes and artist_itunes:
        # Apply universal cleaning to iTunes results (from Phase 7)
        song_itunes, artist_itunes = apply_universal_song_cleaning(song_itunes, artist_itunes, "iTunes")
        return song_itunes, artist_itunes, "iTunes"
    
    # If iTunes fails but we have good parsed results, use them
    if song_parsed and artist_parsed:
        log(f"Using parsed metadata: {artist_parsed} - {song_parsed}")
        # Apply universal cleaning to parsed results (from Phase 7)
        song_parsed, artist_parsed = apply_universal_song_cleaning(song_parsed, artist_parsed, "title_parsing")
        return song_parsed, artist_parsed, "title_parsing"
    
    # Conservative fallback - still counts as title parsing attempt
    log("No reliable artist/song could be parsed - using conservative fallback")
    return title, "Unknown Artist", "title_parsing"
```

### 3. Integration with Process Worker
Update process_videos_worker:
```python
# In process_videos_worker, after download:
# Try AcoustID metadata extraction
song, artist = get_acoustid_metadata(temp_path)
metadata_source = "AcoustID" if (song and artist) else None

# Apply universal cleaning to AcoustID results if found (Phase 7)
if song and artist:
    song, artist = apply_universal_song_cleaning(song, artist, "AcoustID")

# If AcoustID fails, try title-based extraction (iTunes + parsing)
# This function always returns metadata - never None
if not song or not artist:
    song, artist, metadata_source = extract_metadata_from_title(title)

# Log metadata source with detailed results
log(f"Metadata from {metadata_source}: {artist} - {song}")

# Store metadata for next phase
metadata = {
    'song': song,
    'artist': artist,
    'yt_title': title
}

# Log final metadata result with clear formatting
log(f"=== METADATA RESULT for '{title}' ===")
log(f"    Artist: {artist}")
log(f"    Song: {song}")
log(f"    Source: {metadata_source}")
log(f"=====================================")

# TODO: Continue to Phase 9 (Audio Normalization)
```

## Metadata Result Logging
Each processed video shows a clear, formatted metadata result:
```
=== METADATA RESULT for 'Video Title' ===
    Artist: Artist Name
    Song: Song Title
    Source: AcoustID/iTunes/title_parsing
=====================================
```

This provides:
- Clear visual separation of results
- Easy-to-read indented format
- Source tracking for debugging
- Consistent output for all videos

## Title Format Examples

### Common Formats Handled:
1. **Artist - Song**: "Elevation Worship - Praise"
2. **Song by Artist**: "Praise by Elevation Worship" 
3. **Artist | Song**: "Elevation Worship | Praise"
4. **Artist: Song**: "Elevation Worship: Praise"
5. **Song // Artist**: "Praise // Elevation Worship"
6. **Quoted Titles**: "Elevation Worship "Praise" (Official Video)"
7. **With Features**: "Song - Artist ft. Guest (Official Video)"
8. **Complex**: "SONG NAME | Artist Name | Worship Together Session"

### Note on Suffix Removal:
Basic suffix removal is done in the parser, but comprehensive cleaning is handled by the universal metadata cleaning function from Phase 7.

## Key Considerations
- Always returns some metadata (never None, None, None)
- Logs parsing attempts for debugging
- Handles multiple separator types
- Basic suffix removal (comprehensive cleaning in Phase 7)
- Handles featuring artists detection
- Case-insensitive pattern matching
- Preserves original case in results
- Falls back to "Unknown Artist" if needed
- Provides clear metadata result logging

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` (increment MINOR version)
- [x] Implement parse_title_smart function
- [x] Update extract_metadata_from_title
- [x] Add pattern matching for various formats
- [x] Add quote detection pattern
- [x] Ensure fallback always returns something
- [x] Add detailed logging of parsing attempts
- [x] Update process_videos_worker integration
- [x] Implement metadata result logging
- [x] Integrate with Phase 7 universal cleaning

## Testing Before Commit
1. Test basic format: "Artist - Song"
2. Test reverse format: "Song by Artist"
3. Test pipe separator: "Artist | Song | Extra Info"
4. Test with quotes: 'Artist "Song Title" Official'
5. Test worship patterns: "Song | Artist (worship together)"
6. Test no separator: "Just A Title Without Separators"
7. Test colon format: "Artist: Song Title"
8. Test double slash: "Song // Artist // Session"
9. Test empty/null title handling
10. Verify Phase 7 cleaning is applied to results
11. **Verify version was incremented**
12. **Check logs show parsing attempts**
13. **Verify metadata result formatting**

## Commit
After successful testing, commit with message:  
> *"Add smart title parser fallback for metadata (Phase 8)"*

*After verification, proceed to Phase 09.*
