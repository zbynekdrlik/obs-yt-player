# Phase 06 – Title Parser Fallback

## Goal
Implement smart title parsing as a fallback when Gemini metadata extraction fails. This ensures every video gets reasonable metadata.

## Version Increment
**This phase adds new features** → Increment version appropriately

## Requirements Reference
This phase implements the fallback metadata extraction from `02-requirements.md`:
- Parse YouTube titles when Gemini fails
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
        
        # Remove basic video suffixes from song (comprehensive cleaning in Phase 7)
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

### 2. Update Metadata Extraction
```python
def extract_metadata_from_title(title):
    """
    Title parser that always returns metadata - never None. This is the final fallback step.
    Returns (song, artist, source)
    """
    # Try smart title parsing
    song_parsed, artist_parsed = parse_title_smart(title)
    
    if song_parsed and artist_parsed:
        log(f"Using parsed metadata: {artist_parsed} - {song_parsed}")
        # Note: Universal cleaning will be applied in Phase 7
        return song_parsed, artist_parsed, "title_parsing"
    
    # Conservative fallback
    log("No reliable artist/song could be parsed - using conservative fallback")
    return title, "Unknown Artist", "title_parsing"
```

### 3. Integration with Metadata Flow
In the metadata extraction flow (now Gemini-only):
```python
# In get_video_metadata:
# Always try Gemini if API key is configured
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
```

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

### Note on Cleaning:
This phase does basic suffix removal during parsing. Comprehensive metadata cleaning (removing all brackets, features, etc.) is handled by the universal cleaning function in Phase 7.

## Key Considerations
- Always returns some metadata (never None, None, None)
- Logs parsing attempts for debugging
- Handles multiple separator types
- Basic suffix removal during parsing
- Handles featuring artists detection
- Case-insensitive pattern matching
- Preserves original case in results
- Falls back to "Unknown Artist" if needed

## Implementation Checklist
- [ ] Update `SCRIPT_VERSION` appropriately
- [ ] Implement parse_title_smart function
- [ ] Update extract_metadata_from_title
- [ ] Add pattern matching for various formats
- [ ] Add quote detection pattern
- [ ] Ensure fallback always returns something
- [ ] Add detailed logging of parsing attempts
- [ ] Update metadata flow integration
- [ ] Remove references to Phase 8 cleaning (will be Phase 7)

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
10. **Verify version was incremented**
11. **Check logs show parsing attempts**

## Commit
After successful testing, commit with message:  
> *"Add smart title parser fallback for metadata (Phase 6)"*

*After verification, proceed to Phase 07.*

*Prev → Phase-05-Gemini-Metadata.md | Next → Phase-07-Universal-Metadata-Cleaning.md*