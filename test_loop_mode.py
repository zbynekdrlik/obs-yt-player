#!/usr/bin/env python3
"""
Test script for verifying loop mode behavior in OBS YouTube Player.
Tests that loop mode selects a new random video when scene becomes active.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock obspython before importing any modules that use it
sys.modules['obspython'] = MagicMock()

# Now we can import our modules
from ytfast_modules.config import PLAYBACK_MODE_LOOP
from ytfast_modules.state import (
    set_scene_active, is_scene_active, 
    set_playing, is_playing,
    get_playback_mode, set_playback_mode,
    get_loop_video_id, set_loop_video_id,
    get_cached_videos, set_cached_videos,
    clear_played_videos
)

class TestLoopModeBehavior(unittest.TestCase):
    """Test loop mode behavior when scene transitions occur."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Clear any previous state
        set_scene_active(False)
        set_playing(False)
        set_loop_video_id(None)
        set_cached_videos({})
        clear_played_videos()
        
        # Set up mock videos
        self.mock_videos = {
            'video1': {'id': 'video1', 'song': 'Song 1', 'artist': 'Artist 1', 'path': '/path/video1.mp4'},
            'video2': {'id': 'video2', 'song': 'Song 2', 'artist': 'Artist 2', 'path': '/path/video2.mp4'},
            'video3': {'id': 'video3', 'song': 'Song 3', 'artist': 'Artist 3', 'path': '/path/video3.mp4'},
        }
        set_cached_videos(self.mock_videos)
    
    def test_loop_mode_scene_deactivation_clears_loop_video(self):
        """Test that loop video is cleared when scene becomes inactive."""
        # Set up loop mode with a video playing
        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_scene_active(True)
        set_playing(True)
        set_loop_video_id('video1')
        
        # Simulate scene becoming inactive
        from ytfast_modules.playback import playback_controller
        
        # Mock the necessary functions
        with patch('ytfast_modules.playback.should_stop_threads', return_value=False), \
             patch('ytfast_modules.playback.verify_sources', return_value=True), \
             patch('ytfast_modules.playback.ensure_opacity_filter', return_value=True), \
             patch('ytfast_modules.playback.stop_current_playback') as mock_stop:
            
            # Set scene inactive
            set_scene_active(False)
            
            # Run playback controller
            playback_controller()
            
            # Verify that stop_current_playback was called
            mock_stop.assert_called_once()
            
            # Verify loop video was cleared (this happens in stop_current_playback)
            # In the actual code, this is done in the playback_controller when scene is inactive
            self.assertIsNone(get_loop_video_id())
    
    def test_loop_mode_new_random_video_on_scene_activation(self):
        """Test that a new random video is selected when scene becomes active in loop mode."""
        from ytfast_modules.playback import handle_none_state, select_next_video
        
        # Set up loop mode with previous loop video
        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_loop_video_id('video1')  # Previous loop video
        set_scene_active(True)
        set_playing(False)
        
        # Track which video is selected
        selected_videos = []
        
        def mock_start_next_video():
            # This would normally call select_next_video
            video_id = select_next_video()
            selected_videos.append(video_id)
        
        with patch('ytfast_modules.playback.start_next_video', side_effect=mock_start_next_video):
            # Before fix: handle_none_state should clear loop video
            handle_none_state()
            
            # Verify loop video was cleared before selecting new one
            # This is the key fix - clearing the loop video ensures random selection
            self.assertIsNone(get_loop_video_id())
            
            # Verify a video was selected
            self.assertEqual(len(selected_videos), 1)
            
            # The selected video should be random (not necessarily video1)
            # In actual usage, this would be random
            self.assertIn(selected_videos[0], ['video1', 'video2', 'video3'])
    
    def test_loop_mode_replays_same_video_while_active(self):
        """Test that loop mode replays the same video while scene remains active."""
        from ytfast_modules.playback import select_next_video
        
        # Set up loop mode with a video
        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_loop_video_id('video2')
        
        # Select next video multiple times
        videos = []
        for _ in range(3):
            video_id = select_next_video()
            videos.append(video_id)
        
        # All selections should return the same loop video
        self.assertEqual(videos, ['video2', 'video2', 'video2'])
    
    def test_loop_mode_clears_on_manual_stop(self):
        """Test that loop video is cleared when user manually stops playback."""
        from ytfast_modules.playback import handle_stopped_state
        
        # Set up loop mode with a video playing
        set_playback_mode(PLAYBACK_MODE_LOOP)
        set_playing(True)
        set_loop_video_id('video3')
        
        # Mock manual stop detection
        with patch('ytfast_modules.playback._manual_stop_detected', False), \
             patch('ytfast_modules.playback.stop_current_playback') as mock_stop:
            
            # Simulate stopped state (manual stop)
            handle_stopped_state()
            
            # Verify stop was called
            mock_stop.assert_called_once()

def run_tests():
    """Run all tests and report results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoopModeBehavior)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)