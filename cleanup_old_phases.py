#!/usr/bin/env python3
"""
Script to help clean up old phase files from the repository.
Run this to see which files need to be deleted.
"""

# Files that should be KEPT (new clean naming)
keep_files = [
    "phases/Phase-01-Scaffolding.md",
    "phases/Phase-02-Dependency-Setup.md",
    "phases/Phase-03-Playlist-Sync.md",
    "phases/Phase-04-Caching.md",
    "phases/Phase-05-Audio-Normalization.md",
    "phases/Phase-06-Playback-Control.md",
    "phases/Phase-07-Metadata.md",
    "phases/Phase-08-Final-Review.md",
    "phases/README.md"
]

# Files that need to be DELETED (old naming convention)
delete_files = [
    "phases/05-Phase-01-Scaffolding.md",
    "phases/06-Phase-02-Dependency-Setup.md",
    "phases/06-Phase-02-Playlist-Sync.md",
    "phases/07-Phase-03-Caching.md",
    "phases/07-Phase-03-Playlist-Sync.md",
    "phases/08-Phase-04-Audio-Normalization.md",
    "phases/08-Phase-04-Caching.md",
    "phases/09-Phase-05-Audio-Normalization.md",
    "phases/09-Phase-05-Playback-Control.md",
    "phases/10-Phase-06-Metadata.md",
    "phases/10-Phase-06-Playback-Control.md",
    "phases/11-Phase-07-Final-Review.md",
    "phases/11-Phase-07-Metadata.md",
    "phases/12-Phase-08-Final-Review.md"
]

print("FILES TO DELETE:")
print("================")
for f in delete_files:
    print(f"- {f}")

print("\n\nFILES TO KEEP:")
print("==============")
for f in keep_files:
    print(f"✓ {f}")

print("\n\nTo delete these files using GitHub CLI:")
print("======================================")
print("gh api -X DELETE /repos/zbynekdrlik/obs-yt-player/contents/{path} -f message='Remove old phase file' -f sha={sha}")
print("\nNote: You'll need to get the SHA for each file first.")
