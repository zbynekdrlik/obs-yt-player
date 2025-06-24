"""
Test script for nested scene playback detection.
This test should be run in OBS with proper scene setup.
"""

import unittest
import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ytfast_modules.scene import is_scene_visible_nested, is_scene_active_or_nested

class TestNestedScenePlayback(unittest.TestCase):
    """Test cases for nested scene detection functionality."""
    
    def test_imports(self):
        """Test that the new functions are importable."""
        self.assertTrue(callable(is_scene_visible_nested))
        self.assertTrue(callable(is_scene_active_or_nested))
        print("✓ Import test passed")
    
    def test_function_signatures(self):
        """Test that functions have correct signatures."""
        import inspect
        
        # Check is_scene_visible_nested signature
        sig = inspect.signature(is_scene_visible_nested)
        params = list(sig.parameters.keys())
        self.assertIn('scene_name', params)
        self.assertIn('check_scene_source', params)
        print("✓ is_scene_visible_nested signature test passed")
        
        # Check is_scene_active_or_nested signature
        sig = inspect.signature(is_scene_active_or_nested)
        params = list(sig.parameters.keys())
        self.assertEqual(len(params), 0)  # Should take no parameters
        print("✓ is_scene_active_or_nested signature test passed")
    
    def test_module_docstring(self):
        """Test that the module has been updated with nested scene info."""
        from ytfast_modules import scene
        self.assertIn("nested", scene.__doc__.lower())
        print("✓ Module docstring test passed")


def run_tests():
    """Run all tests and return results."""
    print("\n" + "="*60)
    print("OBS YouTube Player - Nested Scene Playback Tests")
    print("Version: 3.3.0")
    print("="*60 + "\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNestedScenePlayback)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


def manual_test_instructions():
    """Print instructions for manual testing in OBS."""
    print("\n" + "="*60)
    print("MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    print("""
To test nested scene playback in OBS:

1. Setup:
   - Create a scene named 'ytfast' with Media Source 'video' and Text Source 'title'
   - Create another scene (e.g., 'Main Scene')
   - Add the 'ytfast' scene as a source in 'Main Scene'

2. Test Direct Playback:
   - Switch to 'ytfast' scene directly
   - Videos should start playing
   - Switch away - playback should stop after transition

3. Test Nested Playback:
   - Switch to 'Main Scene' (which contains ytfast as a source)
   - Videos should start playing even though ytfast is nested
   - The log should show: "Scene activated as nested source in: Main Scene"

4. Test Visibility Toggle:
   - While in 'Main Scene', hide the ytfast source
   - Playback should stop
   - Show the ytfast source again
   - Playback should resume

5. Test Multiple Levels:
   - Create a third scene that includes 'Main Scene' as a source
   - Switch to this third scene
   - Videos should still play (recursive detection)

Expected Log Messages:
- "Scene activated as nested source in: [parent scene name]"
- "Scene deactivated (no longer visible in: [parent scene name])"
""")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run automated tests
    success = run_tests()
    
    # Print manual test instructions
    manual_test_instructions()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
