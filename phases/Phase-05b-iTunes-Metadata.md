# Phase 05b – iTunes Metadata Search

## Goal
Implement iTunes Search API as a secondary metadata source when AcoustID doesn't find a match. This provides metadata for commercial releases not yet in the AcoustID database.

## Version Increment
**This phase enhances existing features** → Keep same MINOR version (1.5.0)

## Requirements Reference
This phase extends the metadata retrieval from Phase 5, providing an additional online source before falling back to title parsing:
- **iTunes Search API** - Free, no authentication required
- Returns structured metadata: artist, song, album
- Good coverage of commercial and worship music

## Implementation Details

### 1. iTunes Search Function
```python
def search_itunes_metadata(search_query):
    """
    Search iTunes API for song metadata.
    Returns (song, artist) or (None, None)
    """
    try:
        # Clean up search query
        search_query = search_query.lower()
        
        # Remove common video suffixes
        for suffix in ['official music video', 'official video', 'lyrics', 'live', 
                       'worship together session', 'official', 'music video', 'hd', '4k',
                       '+ the choir room', 'the choir room']:
            search_query = search_query.replace(suffix, '').strip()
        
        # Replace multiple separators with spaces
        search_query = search_query.replace('//', ' ')
        search_query = search_query.replace('|', ' ')
        
        # Remove extra whitespace
        search_query = ' '.join(search_query.split())
        
        # Try multiple search strategies
        search_queries = []
        
        # Strategy 1: Full cleaned query
        search_queries.append(search_query)
        
        # Strategy 2: If "ft." or "feat." exists, try without featuring artist
        if 'ft.' in search_query or 'feat.' in search_query:
            # Extract main part before featuring
            main_part = re.split(r'\s+(?:ft\.|feat\.)\s+', search_query)[0]
            search_queries.append(main_part)
        
        # Strategy 3: Extract potential song and artist from patterns
        # Pattern: "song_name artist_name" or "artist_name song_name"
        words = search_query.split()
        if len(words) >= 3:
            # Try first few words as song name
            search_queries.append(' '.join(words[:3]))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in search_queries:
            if q not in seen and q:
                seen.add(q)
                unique_queries.append(q)
        
        # Try each search strategy
        for query in unique_queries:
            # URL encode the search query
            encoded_query = urllib.parse.quote(query)
            url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&limit=5"
            
            log(f"Searching iTunes API: {query}", "DEBUG")
            
            # Make request
            req = urllib.request.Request(url)
            req.add_header('User-Agent', f'OBS-YouTube-Player/{SCRIPT_VERSION}')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get('resultCount', 0) > 0:
                # Get first result
                result = data['results'][0]
                artist = result.get('artistName', '')
                song = result.get('trackName', '')
                album = result.get('collectionName', '')
                
                if artist and song:
                    log(f"iTunes match found: {artist} - {song} (Album: {album})", "DEBUG")
                    return song, artist
        
        log("No iTunes results found after trying multiple strategies", "DEBUG")
        return None, None
        
    except Exception as e:
        log(f"iTunes search error: {e}", "DEBUG")
        return None, None
```

### 2. Enhanced Metadata Extraction Wrapper
```python
def extract_metadata_from_title(title):
    """
    Enhanced title parser that tries multiple strategies.
    Returns (song, artist) or (None, None)
    """
    # First, try online searches
    song, artist = search_itunes_metadata(title)
    if song and artist:
        return song, artist
    
    # If online search fails, use smart title parsing (Phase 6)
    # This will be implemented in Phase 6
    return None, None
```

### 3. Integration with Process Worker
Update process_videos_worker to include iTunes search:
```python
# In process_videos_worker, after download:
# Try AcoustID metadata extraction
song, artist = get_acoustid_metadata(temp_path)

# If AcoustID fails, try online search
if not song or not artist:
    song, artist = extract_metadata_from_title(title)
    if song and artist:
        log(f"Found via online search: {artist} - {song}", "NORMAL")

# Store metadata for next phase
metadata = {
    'song': song,
    'artist': artist,
    'yt_title': title
}

# TODO: Continue to Phase 6 (Title Parser Fallback)
# If both AcoustID and iTunes fail, will use title parser in next phase
```

## iTunes API Details

### API Endpoint
- Base URL: `https://itunes.apple.com/search`
- No authentication required
- Rate limit: Reasonable usage (no official limit published)

### Search Parameters
- `term`: Search query (URL encoded)
- `media`: Set to "music" for songs only
- `limit`: Number of results (we use 5)

### Response Format
```json
{
  "resultCount": 1,
  "results": [{
    "artistName": "Artist Name",
    "trackName": "Song Title",
    "collectionName": "Album Name",
    "primaryGenreName": "Genre",
    "releaseDate": "2025-01-01T00:00:00Z",
    "trackTimeMillis": 240000,
    "artworkUrl100": "https://..."
  }]
}
```

## Search Strategies

### 1. Query Cleaning
- Remove video-specific suffixes
- Replace separators (//, |) with spaces
- Remove extra whitespace
- Handle featuring artists

### 2. Multiple Attempts
- Try full cleaned query first
- If featuring artists present, try without them
- Try with just first few words
- This handles various title formats

### 3. Examples
- "Ask Me Why // Michael Bethany Ft. Dwan Hill + The Choir Room"
  - Try 1: "ask me why michael bethany ft. dwan hill"
  - Try 2: "ask me why michael bethany"
  - Try 3: "ask me why michael"

## Key Considerations
- iTunes API is free and requires no authentication
- Good coverage of commercial and worship music
- May not have very new releases immediately
- Returns clean, structured metadata
- Handles various title formats with multiple search strategies
- Falls back gracefully if no match found

## Implementation Checklist
- [ ] Implement search_itunes_metadata function
- [ ] Add query cleaning logic
- [ ] Implement multiple search strategies
- [ ] Handle featuring artists properly
- [ ] Add proper error handling
- [ ] Update extract_metadata_from_title wrapper
- [ ] Integrate with process_videos_worker
- [ ] Add detailed logging for debugging
- [ ] Test with various title formats

## Testing Before Commit
1. Test with clean title: "Joy of the Lord"
2. Test with separators: "Song Name | Artist Name"
3. Test with featuring: "Song ft. Featured Artist"
4. Test with session info: "Song | Artist | Worship Together Session"
5. Test with multiple separators: "Song // Artist // Extra Info"
6. Test with no results (obscure song)
7. Test API error handling (no network)
8. Verify multiple search strategies work
9. Check that album info is logged
10. Test with non-English characters

## Benefits Over Local Database
- No maintenance required
- Always up to date
- No storage needed
- Free to use
- Good coverage of music

## Commit
After successful testing, commit with message:  
> *"Add iTunes metadata search as secondary source (Phase 5b)"*

*After verification, proceed to Phase 06 for title parser fallback.*