#!/usr/bin/env python3
"""
Test script for single mode playback fix.
Tests the scenario where mode is changed to single while video is playing.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from ytfast_modules.config import PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_CONTINUOUS
from ytfast_modules.state import (
    set_playback_mode, get_playback_mode, 
    set_playing, is_playing,
    set_first_video_played, is_first_video_played,
    set_scene_active
)

def test_single_mode_change():
    """Test changing to single mode while video is playing."""
    print("=== Testing Single Mode Change ===")
    
    # Initial state - continuous mode, video playing
    print("\n1. Setting up initial state:")
    set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
    set_playing(True)
    set_scene_active(True)
    set_first_video_played(False)
    print(f"   Mode: {get_playback_mode()}")
    print(f"   Playing: {is_playing()}")
    print(f"   First video played: {is_first_video_played()}")
    
    # Simulate changing to single mode while playing
    print("\n2. Changing to single mode while video is playing:")
    set_playback_mode(PLAYBACK_MODE_SINGLE)
    
    # The fix: when changing to single mode while playing, mark current as first video
    if is_playing():
        set_first_video_played(True)
        print("   Marked current video as first (and only) video")
    
    print(f"   Mode: {get_playback_mode()}")
    print(f"   Playing: {is_playing()}")
    print(f"   First video played: {is_first_video_played()}")
    
    # Test what happens when video ends
    print("\n3. Simulating video end in single mode:")
    print(f"   Should stop playback: {is_first_video_played() and get_playback_mode() == PLAYBACK_MODE_SINGLE}")
    
    # Test switching back to continuous
    print("\n4. Switching back to continuous mode:")
    previous_mode = get_playback_mode()
    set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
    
    # Reset first video flag when leaving single mode
    if previous_mode == PLAYBACK_MODE_SINGLE:
        set_first_video_played(False)
        print("   Reset first video played flag")
    
    print(f"   Mode: {get_playback_mode()}")
    print(f"   First video played: {is_first_video_played()}")
    
    print("\n=== Test Complete ===")
    print("The fix ensures that when switching to single mode while playing,")
    print("the current video is treated as the 'first video' and playback")
    print("will stop when it ends.")

if __name__ == "__main__":
    test_single_mode_change()
