# 12‑Playback Modes

This document describes the three playback modes implemented in the OBS YouTube Player.

## Overview

The script supports three distinct playback modes that control how videos play when the scene is active:

1. **Continuous Mode** (default)
2. **Single Mode**
3. **Loop Mode**

Users can select the desired mode via a dropdown in the OBS script properties.

## Mode Behaviors

### Continuous Mode
- **Default mode** - plays all videos in the playlist randomly forever
- **Scene Active**: Videos play normally, advancing to the next random video when one ends
- **Scene Inactive**: Stops playback immediately
- **Use Case**: Background music or video playlist that plays continuously while scene is live

### Single Mode
- Plays **one video only** then stops
- **Scene Active**: Plays a single random video and stops
- **Scene Inactive**: Stops playback immediately
- **Restart Behavior**: When scene becomes active again, plays a new random video
- **Use Case**: Intro/outro videos, special segments that should play once

### Loop Mode
- Repeats the **same video** continuously
- **Scene Active**: First video is randomly selected, then loops indefinitely
- **Scene Inactive**: Stops playback and clears the loop selection
- **Restart Behavior**: When scene becomes active again, selects a new random video to loop
- **Use Case**: Background ambience, hold music, repeated content

## Common Behaviors

All modes share these behaviors:
- **Stop playback** when scene becomes inactive (switching to another scene)
- **Start playback** when scene becomes active (if videos are available)
- Respect title display timing (fade in/out)
- Handle pre-loaded videos appropriately

## Implementation Details

### State Management
- `playback_mode`: Stores current mode setting
- `first_video_played`: Tracks if first video has played (for Single mode)
- `loop_video_id`: Stores the video ID to loop (for Loop mode)

### Mode Switching
- Changing modes takes effect immediately
- In Loop mode: If switching while playing, current video becomes the loop video
- State is reset appropriately when switching modes

### Scene Transition Handling
- All modes stop playback when scene becomes inactive
- When scene becomes active again:
  - **Continuous**: Starts playing random videos
  - **Single**: Plays one new random video
  - **Loop**: Selects a new random video to loop

### Pre-loaded Video Handling
- If OBS has a video pre-loaded when script starts:
  - **Continuous**: Lets it play and continues with playlist
  - **Single**: Counts it as the one video and stops after
  - **Loop**: Sets it as the loop video

## Configuration

In script properties:
```
Playback Mode: [Dropdown]
  - Continuous (Play all videos)
  - Single (Play one video and stop)  
  - Loop (Repeat current video)
```

## Code Structure

Key files:
- `config.py`: Mode constants and default setting
- `state.py`: Mode state management functions
- `playback_controller.py`: Main logic for mode behaviors
- `state_handlers.py`: Specific handlers for each media state

The playback controller checks the current mode and scene state to determine behavior, ensuring smooth transitions and proper cleanup when switching modes or scenes.

*Prev → 11‑Final_Integration.md | Next → Phase documentation continues*