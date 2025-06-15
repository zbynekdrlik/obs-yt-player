# Script to identify old phase files to be deleted
old_files = [
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

print("Files to delete:")
for f in old_files:
    print(f"- {f}")

print("\nNew clean structure:")
for i in range(1, 9):
    print(f"- phases/Phase-{i:02d}-*.md")