# Phase 07 – Title Parser Fallback

## Goal
Implement smart title parsing as a fallback when online metadata sources (AcoustID, iTunes) fail. This ensures every video gets reasonable metadata even without online matches.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.5.0 to 1.6.0)

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
    log(f"Parsing title: {title}")
    
    # Clean the title
    cleaned = title.strip()
    
    # Remove common video suffixes
    suffixes_to_remove = [
        'official music video', 'official video', 'official audio',
        'music video', 'lyrics video', 'lyric video', 'lyrics',
        'hd', '4k', 'live', 'acoustic', 'cover', 'remix',
        'feat.', 'ft.', 'featuring', '(audio)', '[audio]',
        'worship together session', 'official', 'video'
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
    
    # Try different separator patterns
    separators = [
        ' - ',     # Most common: "Artist - Song"
        ' – ',     # Em dash variant
        ' — ',     # En dash variant  
        ' | ',     # Pipe separator
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
                
                # Determine which is artist and which is song
                # Common patterns:
                # "Artist - Song" (most common)
                # "Song by Artist"
                # "Song | Artist"
                
                if sep == ' by ':
                    # "Song by Artist" pattern
                    song, artist = part1, part2
                else:
                    # Try to determine based on content
                    # If part2 contains "feat" or "ft", it's likely the song
                    if any(x in part2.lower() for x in ['feat', 'ft.']):
                        artist, song = part1, part2
                    else:
                        # Default assumption: Artist - Song
                        artist, song = part1, part2
                
                # Clean up featuring artists from song title
                song = clean_featuring_from_song(song)
                
                log(f"Parsed: Artist='{artist}', Song='{song}'")
                return song, artist
    
    # No separator found - try other patterns
    
    # Pattern: "Artist: Song Title"
    if ':' in cleaned:
        parts = cleaned.split(':', 1)
        if len(parts) == 2:
            artist, song = parts[0].strip(), parts[1].strip()
            song = clean_featuring_from_song(song)
            log(f"Parsed (colon): Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Pattern: Quoted song title
    quote_match = re.search(r'[""](.*?)[""]', cleaned)
    if quote_match:
        song = quote_match.group(1)
        # Remove the quoted part to find artist
        artist = cleaned.replace(quote_match.group(0), '').strip()
        if artist and song:
            log(f"Parsed (quotes): Artist='{artist}', Song='{song}'")
            return song, artist
    
    # Last resort: Use whole title as song, "Unknown Artist"
    song = clean_featuring_from_song(cleaned)
    artist = "Unknown Artist"
    log(f"Parsed (fallback): Artist='{artist}', Song='{song}'")
    return song, artist

def clean_featuring_from_song(song):
    """
    Remove featuring artist info from song title.
    """
    # Remove featuring patterns
    feat_patterns = [
        r'\s*\(feat\..*?\)',
        r'\s*\[feat\..*?\]',
        r'\s*\(ft\..*?\)',
        r'\s*\[ft\..*?\]',
        r'\s*feat\..*$',
        r'\s*ft\..*$',
        r'\s*featuring.*$'
    ]
    
    for pattern in feat_patterns:
        song = re.sub(pattern, '', song, flags=re.IGNORECASE)
    
    return song.strip()
```

### 2. Update Metadata Extraction Wrapper
Update the extract_metadata_from_title function:
```python
def extract_metadata_from_title(title):
    """
    Enhanced title parser that tries multiple strategies.
    Returns (song, artist) or (None, None)
    """
    # First, try online searches (iTunes)
    song, artist = search_itunes_metadata(title)
    if song and artist:
        return song, artist
    
    # Fall back to smart title parsing
    song, artist = parse_title_smart(title)
    if song and artist:
        log(f"Using parsed metadata: {artist} - {song}")
        return song, artist
    
    return None, None
```

### 3. Integration with Process Worker
Update process_videos_worker:
```python
# In process_videos_worker, after download:
# Try AcoustID metadata extraction
song, artist = get_acoustid_metadata(temp_path)

# If AcoustID fails, try title-based extraction (iTunes + parsing)
if not song or not artist:
    song, artist = extract_metadata_from_title(title)
    if song and artist:
        source = "iTunes" if "iTunes match found" in recent_logs else "parsed"
        log(f"Metadata from {source}: {artist} - {song}")
else:
    log(f"Metadata from AcoustID: {artist} - {song}")

# Ensure we always have some metadata
if not song or not artist:
    # This shouldn't happen with our fallback parser
    song = title
    artist = "Unknown Artist"
    log(f"Using minimal metadata: {artist} - {song}")

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
log(f"    Source: {metadata_source if metadata_source else 'fallback'}")
log(f"=====================================")

# TODO: Continue to Phase 8 (Audio Normalization)
```

## Metadata Result Logging
Each processed video shows a clear, formatted metadata result:
```
=== METADATA RESULT for 'Video Title' ===
    Artist: Artist Name
    Song: Song Title
    Source: AcoustID/iTunes/parsed/fallback
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

### Suffix Removal:
- Official Music Video
- Official Video/Audio
- Lyrics/Lyric Video
- HD/4K
- Live/Acoustic
- (Audio)/[Audio]
- Worship Together Session

## Key Considerations
- Always returns some metadata (never None, None)
- Logs transformations for debugging
- Handles multiple separator types
- Removes common YouTube suffixes
- Handles featuring artists properly
- Case-insensitive suffix matching
- Preserves original case in results
- Falls back to "Unknown Artist" if needed
- Provides clear metadata result logging

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` (increment MINOR version)
- [x] Implement parse_title_smart function
- [x] Implement clean_featuring_from_song helper
- [x] Update extract_metadata_from_title
- [x] Add comprehensive title cleaning
- [x] Handle multiple separator types
- [x] Add quote detection pattern
- [x] Ensure fallback always returns something
- [x] Add detailed logging of transformations
- [x] Update process_videos_worker integration
- [x] Implement metadata result logging

## Testing Before Commit
1. Test basic format: "Artist - Song"
2. Test reverse format: "Song by Artist"
3. Test pipe separator: "Artist | Song | Extra Info"
4. Test with quotes: 'Artist "Song Title" Official'
5. Test featuring: "Song - Artist ft. Guest"
6. Test multiple suffixes: "Song (Official Video) [HD]"
7. Test no separator: "Just A Title Without Separators"
8. Test colon format: "Artist: Song Title"
9. Test double slash: "Song // Artist // Session"
10. Test empty/null title handling
11. **Verify version was incremented**
12. **Check logs show transformations**
13. **Verify metadata result formatting**

## Commit
After successful testing, commit with message:  
> *"Add smart title parser fallback for metadata (Phase 7)"*

*After verification, proceed to Phase 08.*
