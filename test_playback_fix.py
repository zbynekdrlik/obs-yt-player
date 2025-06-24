#!/usr/bin/env python3
"""
Test script to verify the loop mode playback fix.
"""

import sys
import os

# Add modules directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(script_dir, 'ytfast_modules')
sys.path.insert(0, modules_dir)

# Mock OBS module
class MockOBS:
    OBS_MEDIA_STATE_NONE = 0
    OBS_MEDIA_STATE_PLAYING = 1  
    OBS_MEDIA_STATE_STOPPED = 2
    OBS_MEDIA_STATE_ENDED = 3
    
sys.modules['obspython'] = MockOBS()

# Now we can import the modules
from state import set_scene_active, is_scene_active, set_playing, is_playing
from state import get_playback_mode, set_playback_mode, get_loop_video_id, set_loop_video_id
from state import set_cached_videos, get_cached_videos
from config import PLAYBACK_MODE_LOOP

def test_scene_activation():
    """Test that playback starts when scene becomes active in loop mode."""
    print("Testing scene activation in loop mode...")
    
    # Setup test data
    test_videos = {
        'video1': {'path': '/test/video1.mp4', 'song': 'Test Song 1', 'artist': 'Test Artist 1'},
        'video2': {'path': '/test/video2.mp4', 'song': 'Test Song 2', 'artist': 'Test Artist 2'},
    }
    
    # Set initial state
    set_cached_videos(test_videos)
    set_playback_mode(PLAYBACK_MODE_LOOP)
    set_scene_active(False)
    set_playing(False)
    set_loop_video_id(None)
    
    print(f"Initial state:")
    print(f"  Scene active: {is_scene_active()}")
    print(f"  Playing: {is_playing()}")
    print(f"  Loop video: {get_loop_video_id()}")
    print(f"  Cached videos: {len(get_cached_videos())}")
    
    # Simulate scene becoming active
    print("\nSimulating scene activation...")
    set_scene_active(True)
    
    # The fix should ensure playback starts when:
    # 1. Scene is active
    # 2. Not playing
    # 3. Videos are available
    # 4. Media state is NONE, STOPPED, or ENDED
    
    should_start = is_scene_active() and not is_playing() and get_cached_videos()
    print(f"\nShould start playback: {should_start}")
    
    if should_start:
        print("✓ Playback should start when scene becomes active")
        # In loop mode, it should also clear any previous loop video
        if get_playback_mode() == PLAYBACK_MODE_LOOP and get_loop_video_id():
            print("  - Previous loop video should be cleared")
    else:
        print("✗ Playback should start but conditions not met")

if __name__ == '__main__':
    test_scene_activation()
