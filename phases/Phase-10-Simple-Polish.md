# Phase 10 – Simple Polish

## Goal
Add minimal polish to ensure cached videos are valid and improve time display formatting.

## Version Increment
**Minor improvements** → Increment to appropriate version

## Simplified Requirements
This phase adds only essential improvements without over-engineering:
- Validate cached video files are playable
- Add human-readable time formatting
- Keep all existing functionality intact

## Implementation Details

### 1. Video File Validation
Add simple validation during cache scanning to ensure files are valid:

```python
# Add to cache.py
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

# Update scan_existing_cache() to validate files:
# Skip invalid files and log them
```

### 2. Time Formatting
Add simple duration formatting for better readability:

```python
# Add to utils.py
def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds is None or seconds < 0:
        return "unknown"
        
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
        
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds}s"
        
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {seconds}s"
```

### 3. Apply Formatting
Update progress logging to use formatted time:
- Download progress messages
- Playback progress messages
- Video duration displays
- Metadata/fingerprint duration logs

## Testing Checklist
- [ ] Cache scan skips invalid files
- [ ] Corrupted files are logged and skipped
- [ ] Time displays as "3m 45s" instead of "225s"
- [ ] All existing functionality continues to work
- [ ] No breaking changes

## Implementation Summary
1. Add `validate_video_file()` to cache module
2. Add `format_duration()` to utils module  
3. Update logging to use formatted durations
4. Version bump appropriately

## What We're NOT Doing
- No complex error recovery systems
- No resource monitoring
- No unnecessary refactoring
- No breaking changes

## Commit
After testing, commit with message:
*"Simple polish - video validation and time formatting (Phase 10)"*

**Keep it simple, keep it working!**

*Prev → Phase-09-Playback-Control.md | Next → Phase-11-File-Based-Logging.md*
