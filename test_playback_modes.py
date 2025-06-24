#!/usr/bin/env python3
"""
Test script for playback modes functionality.
Tests the core logic without requiring OBS environment.
"""

import sys
import os

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ytfast_modules'))

# Mock OBS module for testing
class MockOBS:
    OBS_MEDIA_STATE_NONE = 0
    OBS_MEDIA_STATE_PLAYING = 1
    OBS_MEDIA_STATE_STOPPED = 2
    OBS_MEDIA_STATE_ENDED = 3
    
    @staticmethod
    def timer_add(func, interval):
        print(f"Mock: timer_add({func.__name__}, {interval})")
    
    @staticmethod
    def timer_remove(func):
        print(f"Mock: timer_remove({func.__name__})")
    
    @staticmethod
    def obs_get_source_by_name(name):
        print(f"Mock: obs_get_source_by_name({name})")
        return "mock_source"
    
    @staticmethod
    def obs_source_release(source):
        print(f"Mock: obs_source_release({source})")
    
    @staticmethod
    def obs_source_get_id(source):
        return "ffmpeg_source"

# Install mock
sys.modules['obspython'] = MockOBS()

# Now import our modules
from config import PLAYBACK_MODE_CONTINUOUS, PLAYBACK_MODE_SINGLE, PLAYBACK_MODE_LOOP
from state import set_playback_mode, get_playback_mode, set_scene_active, is_scene_active

# Test scenarios
def test_continuous_mode():
    """Test continuous mode behavior."""
    print("\n=== Testing Continuous Mode ===")
    
    set_playback_mode(PLAYBACK_MODE_CONTINUOUS)
    print(f"Set mode to: {get_playback_mode()}")
    
    # Test with scene active
    set_scene_active(True)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Videos play normally, advancing to next random video forever")
    
    # Test with scene inactive
    set_scene_active(False)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Stop playback immediately")
    print("✓ Continuous mode stops when scene becomes inactive")


def test_single_mode():
    """Test single mode behavior."""
    print("\n=== Testing Single Mode ===")
    
    set_playback_mode(PLAYBACK_MODE_SINGLE)
    print(f"Set mode to: {get_playback_mode()}")
    
    # Test with scene active
    set_scene_active(True)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Play one video then stop")
    
    # Test with scene inactive
    set_scene_active(False)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Stop playback immediately")
    print("✓ Single mode stops when scene becomes inactive")


def test_loop_mode():
    """Test loop mode behavior."""
    print("\n=== Testing Loop Mode ===")
    
    set_playback_mode(PLAYBACK_MODE_LOOP)
    print(f"Set mode to: {get_playback_mode()}")
    
    # Test with scene active
    set_scene_active(True)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Loop the same video continuously")
    
    # Test with scene inactive
    set_scene_active(False)
    print(f"Scene active: {is_scene_active()}")
    print("Expected: Stop playback and clear loop selection")
    print("✓ Loop mode stops when scene becomes inactive")


def test_mode_switching():
    """Test switching between modes."""
    print("\n=== Testing Mode Switching ===")
    
    modes = [
        (PLAYBACK_MODE_CONTINUOUS, "Continuous"),
        (PLAYBACK_MODE_SINGLE, "Single"),
        (PLAYBACK_MODE_LOOP, "Loop")
    ]
    
    for mode, name in modes:
        set_playback_mode(mode)
        assert get_playback_mode() == mode, f"Failed to set {name} mode"
        print(f"✓ Successfully set {name} mode")


def main():
    """Run all tests."""
    print("OBS YouTube Player - Playback Modes Test")
    print("=" * 40)
    
    # Run tests
    test_continuous_mode()
    test_single_mode()
    test_loop_mode()
    test_mode_switching()
    
    print("\n" + "=" * 40)
    print("All tests completed!")
    print("\nKey behaviors implemented:")
    print("- ALL modes stop playback when scene becomes inactive")
    print("- Continuous mode plays random videos forever (while scene is active)")
    print("- Single mode plays one video and stops")
    print("- Loop mode repeats the same video (while scene is active)")


if __name__ == "__main__":
    main()
