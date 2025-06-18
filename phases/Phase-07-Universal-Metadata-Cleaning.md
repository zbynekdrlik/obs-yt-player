# Phase 07 – Universal Metadata Cleaning

## Goal
Apply consistent metadata cleaning to ALL sources (AcoustID, iTunes, title parsing) to ensure clean, consistent song titles without annotations or extra information.

## Version Increment
**This phase adds new features** → Increment MINOR version (e.g., from 1.6.0 to 1.7.0)

## Requirements Reference
This phase implements the metadata cleaning requirement from `02-requirements.md`:
- Apply universal song title cleaning to ALL metadata sources
- Remove annotations like (Live), [Official], (feat. Artist) from every result
- Log all cleaning transformations for debugging

## Implementation Details

### 1. Core Cleaning Function
```python
def clean_featuring_from_song(song):
    """
    Remove ALL bracket phrases from song title including multiple consecutive brackets.
    Handles: (feat. X), [Live], {Official}, (Audio), etc.
    """
    if not song:
        return song
    
    original_song = song
    log(f"Song title cleaning - Original: '{original_song}'")
    
    # Define bracket types and their patterns
    bracket_pairs = [
        ('(', ')'),  # Parentheses
        ('[', ']'),  # Square brackets  
        ('{', '}'),  # Curly brackets
    ]
    
    # Common annotation patterns to remove (case-insensitive)
    annotation_patterns = [
        # Featuring patterns
        r'feat\.?\s+[^)}\]]*',
        r'ft\.?\s+[^)}\]]*', 
        r'featuring\s+[^)}\]]*',
        
        # Video/audio descriptors
        r'official\s*(?:music\s*)?video',
        r'official\s*audio',
        r'music\s*video',
        r'lyric\s*video',
        r'lyrics?\s*video',
        r'lyrics?',
        r'audio',
        r'video',
        
        # Performance descriptors
        r'live',
        r'acoustic',
        r'unplugged',
        r'session',
        r'worship\s+together\s+session',
        r'en\s+vivo',
        
        # Quality descriptors
        r'hd',
        r'4k',
        r'high\s+quality',
        
        # Miscellaneous
        r'official',
        r'cover',
        r'remix',
        r'radio\s+edit',
        r'extended\s+version',
        r'choir\s+room',
        r'video\s+oficial',
    ]
    
    # Step 1: Remove complete bracket phrases that contain annotations
    cleaned = song
    iteration = 0
    max_iterations = 10  # Prevent infinite loops
    
    while iteration < max_iterations:
        iteration += 1
        original_length = len(cleaned)
        
        # For each bracket type
        for open_bracket, close_bracket in bracket_pairs:
            # Find all bracket pairs of this type
            bracket_pattern = re.escape(open_bracket) + r'([^' + re.escape(open_bracket) + re.escape(close_bracket) + r']*)' + re.escape(close_bracket)
            
            def should_remove_bracket(match):
                content = match.group(1).strip().lower()
                if not content:
                    return True  # Remove empty brackets
                
                # Check if content matches any annotation pattern
                for pattern in annotation_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return True
                
                # Check for additional numeric/year patterns
                if re.match(r'^\d{4}$', content):  # Year like (2019)
                    return True
                if re.match(r'^[0-9\s\-:]+$', content):  # Time stamps or numbers
                    return True
                
                return False
            
            # Remove matching brackets
            def replace_bracket(match):
                if should_remove_bracket(match):
                    log(f"Removing bracket phrase: '{match.group(0)}'")
                    return ''
                return match.group(0)
            
            cleaned = re.sub(bracket_pattern, replace_bracket, cleaned)
        
        # Clean up whitespace and check if we made changes
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) == original_length:
            break  # No more changes
    
    # Step 2: Remove trailing annotation phrases without brackets
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
        new_cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        if new_cleaned != cleaned:
            log(f"Removing trailing phrase: '{pattern}' from '{cleaned}'")
            cleaned = new_cleaned
    
    # Step 3: Final cleanup
    cleaned = cleaned.strip()
    
    # Remove any remaining double spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove trailing punctuation that might be left behind
    cleaned = re.sub(r'[,\-\|\s]+$', '', cleaned).strip()
    
    if cleaned != original_song:
        log(f"Song title cleaned: '{original_song}' → '{cleaned}'")
    
    return cleaned or original_song  # Return original if cleaning resulted in empty string
```

### 2. Universal Application Function
```python
def apply_universal_song_cleaning(song, artist, source):
    """
    Apply universal song title cleaning to metadata from ANY source.
    This is the final step that ensures ALL song titles are clean regardless of source.
    """
    if not song:
        return song, artist
    
    original_song = song
    
    # Apply the comprehensive cleaning function
    cleaned_song = clean_featuring_from_song(song)
    
    # Log the cleaning if it changed anything
    if cleaned_song != original_song:
        log(f"Universal cleaning applied to {source} result: '{original_song}' → '{cleaned_song}'")
    
    return cleaned_song, artist
```

### 3. Integration Points
Apply cleaning at these key points in the code:

#### AcoustID Results (in process_videos_worker):
```python
# Try AcoustID metadata extraction
song, artist = get_acoustid_metadata(temp_path)
metadata_source = "AcoustID" if (song and artist) else None

# Apply universal cleaning to AcoustID results if found
if song and artist:
    song, artist = apply_universal_song_cleaning(song, artist, "AcoustID")
```

#### iTunes Results (in search_itunes_metadata):
```python
# In search_itunes_metadata, before returning results:
if song_itunes and artist_itunes:
    # Apply universal cleaning to iTunes results
    song_itunes, artist_itunes = apply_universal_song_cleaning(song_itunes, artist_itunes, "iTunes")
    return song_itunes, artist_itunes, "iTunes"
```

#### Title Parsing Results (in extract_metadata_from_title):
```python
# Apply universal cleaning to parsed results
song_parsed, artist_parsed = apply_universal_song_cleaning(song_parsed, artist_parsed, "title_parsing")
return song_parsed, artist_parsed, "title_parsing"
```

## Cleaning Examples

### Bracket Removal:
- "Song Title (Official Music Video)" → "Song Title"
- "Song Title [Official Audio]" → "Song Title"
- "Song Title (feat. Artist B)" → "Song Title"
- "Song Title (Live at Chapel)" → "Song Title"
- "Song Title [HD] (2023)" → "Song Title"

### Trailing Phrase Removal:
- "Song Title feat. Artist B" → "Song Title"
- "Song Title Official Video" → "Song Title"
- "Song Title Live" → "Song Title"
- "Song Title HD" → "Song Title"

### Multiple Annotations:
- "Song Title (feat. Artist B) [Official Video] HD" → "Song Title"
- "Song Title (Live) (Acoustic Version)" → "Song Title"

## Key Considerations
- Always returns cleaned title (never empty)
- Preserves original case in results
- Logs all transformations for debugging
- Handles multiple consecutive brackets
- Removes both bracketed and trailing annotations
- Applied consistently to ALL metadata sources
- Works iteratively to handle nested/multiple brackets

## Implementation Checklist
- [x] Update `SCRIPT_VERSION` (increment MINOR version)
- [x] Implement clean_featuring_from_song function
- [x] Implement apply_universal_song_cleaning wrapper
- [x] Apply to AcoustID results
- [x] Apply to iTunes results
- [x] Apply to title parsing results
- [x] Add comprehensive annotation patterns
- [x] Add detailed transformation logging
- [x] Handle edge cases (empty results, no changes)

## Testing Before Commit
1. Test AcoustID result with annotations: Verify cleaning applied
2. Test iTunes result with (feat.): Verify featuring removed
3. Test title parsing with [Official Video]: Verify suffix removed
4. Test multiple brackets: "(Live) [HD] (2023)"
5. Test trailing phrases: "Song Title feat. Artist B"
6. Test empty/null inputs
7. Verify all sources log cleaning transformations
8. Check that original titles are preserved if cleaning fails
9. **Verify version was incremented**
10. **Check logs show all cleaning operations**

## Commit
After successful testing, commit with message:  
> *"Add universal metadata cleaning for all sources (Phase 7)"*

*After verification, proceed to Phase 08.*
