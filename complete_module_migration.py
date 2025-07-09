#!/usr/bin/env python3
"""
Complete the ytfast to ytplay module migration.
This script copies remaining module files and updates imports.
"""

import os
import re
import shutil
from pathlib import Path

# Files already migrated
MIGRATED_FILES = {
    '__init__.py',
    'config.py',
    'logger.py',
    'state.py'
}

# All module files
ALL_MODULE_FILES = {
    '__init__.py', 'cache.py', 'config.py', 'download.py', 
    'gemini_metadata.py', 'logger.py', 'media_control.py', 
    'metadata.py', 'normalize.py', 'opacity_control.py', 
    'playback.py', 'playback_controller.py', 'playlist.py', 
    'reprocess.py', 'scene.py', 'state.py', 'state_handlers.py', 
    'title_manager.py', 'tools.py', 'utils.py', 'video_selector.py'
}

def migrate_remaining_modules():
    """Migrate remaining module files from ytfast_modules to ytplay_modules."""
    
    old_modules_dir = "yt-player-main/ytfast_modules"
    new_modules_dir = "yt-player-main/ytplay_modules"
    
    # Get files to migrate
    files_to_migrate = ALL_MODULE_FILES - MIGRATED_FILES
    
    print(f"Files to migrate: {len(files_to_migrate)}")
    print("=" * 50)
    
    for filename in sorted(files_to_migrate):
        old_path = os.path.join(old_modules_dir, filename)
        new_path = os.path.join(new_modules_dir, filename)
        
        if not os.path.exists(old_path):
            print(f"❌ {filename} not found in {old_modules_dir}")
            continue
        
        try:
            # Read the file
            with open(old_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update imports from ytfast_modules to ytplay_modules
            updated_content = content.replace('from ytfast_modules', 'from ytplay_modules')
            updated_content = updated_content.replace('import ytfast_modules', 'import ytplay_modules')
            
            # Write to new location
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Migrated: {filename}")
            
        except Exception as e:
            print(f"❌ Error migrating {filename}: {e}")
    
    print("\n✨ Module migration complete!")
    print("\nNext steps:")
    print("1. Run this script locally")
    print("2. Delete the old ytfast_modules directory")
    print("3. Update documentation")
    print("4. Test everything works")

if __name__ == "__main__":
    migrate_remaining_modules()
