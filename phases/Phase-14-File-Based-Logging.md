# Phase 14: File-Based Logging

## Overview
Implement comprehensive file-based logging to complement OBS console output, enabling better debugging and analysis of multi-threaded operations.

## Requirements
- Log to both OBS console and individual files per session
- Include thread information in file logs
- Create logs in `{cache_dir}/logs/` directory
- Prevent duplicate files from quick OBS reloads
- Maintain backward compatibility with existing console logging

## Implementation Details

### Enhanced Logger Module (`logger.py`)
1. **Dual Output System**
   - Console output: Standard OBS format
   - File output: Enhanced format with thread identification

2. **File Management**
   - Create `logs/` subdirectory in cache directory
   - Generate unique filenames with timestamps
   - Example: `ytfast_20250622_183209.log`

3. **Session Management**
   - Write session header with start time
   - Buffer early messages before file creation
   - Write session footer with end time
   - Proper cleanup on script unload

4. **Thread Safety**
   - Use threading locks for file operations
   - Thread-safe message buffering
   - Concurrent write protection

5. **Intelligent Initialization**
   - 1-second delay before creating log file
   - Prevents duplicate files from quick reloads
   - Buffers messages during delay period

### Log File Format
```
=== ytfast Log Session ===
Started: 2025-06-22 18:32:09
========================================

[2025-06-22 18:32:08] [MainThread] Script version 2.9.2 loaded
[2025-06-22 18:32:08] [Thread: Thread-1] Cache directory ready
[2025-06-22 18:32:08] [Thread: Thread-2] Starting playlist synchronization
...

========================================
Session ended: 2025-06-22 18:32:18
========================================
```

### Integration Points
1. **Main Script (`ytfast.py`)**
   - Import `cleanup_logging` from logger
   - Call cleanup in `script_unload()`

2. **Configuration (`config.py`)**
   - Version increment for tracking changes
   - No new configuration constants needed

## Benefits
- **Debugging**: Track issues across multiple threads
- **History**: Logs persist after OBS closes
- **Analysis**: Separate files for easy comparison
- **Thread Visibility**: Identify which thread executes each operation

## Testing
1. Load script and verify log file creation
2. Check that only one file is created per session
3. Verify all console messages appear in file
4. Confirm proper cleanup on script unload
5. Test thread information accuracy

## Future Enhancements
- Log rotation based on size or age
- Log level filtering (debug/info/error)
- Compression of old logs
- Log viewer tool

*Prev → Phase-13-Gemini-Integration.md | Next → TBD*
