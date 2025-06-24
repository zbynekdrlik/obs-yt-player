# Nested Scene Playback Feature

## Overview
As of version 3.3.0, the OBS YouTube Player now supports nested scene playback. This means videos will start playing not only when the YouTube player scene is directly selected in the program output, but also when it's included as a source within another scene.

## Use Cases

### 1. Multi-Camera Productions
Include the YouTube player scene alongside camera sources in a main production scene. Videos will play automatically when the production scene goes live.

### 2. Picture-in-Picture Layouts
Add the YouTube player scene as a smaller element within a larger scene layout. The videos will play whenever the parent scene is active.

### 3. Complex Scene Compositions
Create elaborate scene structures with multiple nested scenes. The YouTube player will detect its visibility at any nesting level.

## How It Works

The plugin now performs recursive scene detection to determine if the YouTube player scene is visible:

1. **Direct Detection**: Checks if the YouTube player scene is the current program scene
2. **Nested Detection**: Recursively checks all scene sources within the current program scene
3. **Visibility Check**: Only considers visible sources (hidden sources don't trigger playback)

## Setup Example

1. Create your YouTube player scene (e.g., "ytfast") with:
   - Media Source named "video"
   - Text Source named "title"

2. Create a main production scene (e.g., "Main Show")

3. Add the YouTube player scene as a source in the production scene:
   - Click "+" in Sources
   - Select "Scene"
   - Choose your YouTube player scene

4. When you switch to "Main Show", videos will automatically start playing

## Behavior Details

- **Automatic Start**: Videos begin playing when the scene becomes visible (directly or nested)
- **Automatic Stop**: Playback stops when the scene is no longer visible
- **Transition Support**: Handles OBS transitions gracefully
- **Multiple Levels**: Supports deeply nested scenes (scene within scene within scene)
- **Visibility Toggle**: Hiding/showing the nested scene source controls playback

## Playback Modes

All playback modes work with nested scenes:
- **Continuous**: Plays videos continuously while visible
- **Single**: Plays one video per scene activation
- **Loop**: Loops the current video while visible

## Log Messages

The plugin now provides detailed logging for nested scene detection:
- `Scene activated directly: ytfast` - Direct program scene
- `Scene activated as nested source in: Main Show` - Nested detection
- `Scene deactivated (no longer visible in: Main Show)` - No longer visible

## Technical Details

The implementation uses OBS's scene enumeration API to:
1. Get the current program scene
2. Enumerate all scene items within it
3. Check each item's source type and visibility
4. Recursively check nested scenes
5. Avoid infinite recursion with proper checks

## Troubleshooting

If nested playback isn't working:
1. Ensure the nested scene source is visible (eye icon enabled)
2. Check that source names match exactly (case-sensitive)
3. Verify the YouTube player scene works when selected directly
4. Check OBS logs for error messages

## Performance

The nested detection is optimized to:
- Only run when scenes change
- Release all OBS resources properly
- Avoid unnecessary recursive checks
- Maintain minimal CPU overhead
