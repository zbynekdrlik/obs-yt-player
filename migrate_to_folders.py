#!/usr/bin/env python3
"""
Migration Script for OBS YouTube Player
======================================

Migrates from the old single-file setup to the new folder-based architecture.

This script will:
1. Create the new folder structure
2. Move existing files to the appropriate locations
3. Update OBS to use the new script path
4. Preserve all settings and cache
"""

import os
import shutil
import sys
from pathlib import Path


def migrate_to_folders():
    """Migrate from old single-file setup to folder-based structure."""
    
    print("🚀 OBS YouTube Player Migration Tool")
    print("=" * 40)
    print("\nThis will migrate your existing setup to the new folder-based architecture.")
    
    # Check if we're in the right directory
    old_script = "ytfast.py"
    old_modules = "ytfast_modules"
    
    if not os.path.exists(old_script):
        print(f"\n❌ Error: {old_script} not found in current directory.")
        print("   Please run this script from your OBS scripts directory.")
        return False
    
    # Define new structure
    new_dir = "yt-player-main"
    new_script = "ytplay.py"
    new_modules = "ytplay_modules"
    
    # Check if new structure already exists
    if os.path.exists(new_dir):
        print(f"\n⚠️  Warning: {new_dir} already exists.")
        response = input("   Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Migration cancelled.")
            return False
        print(f"   Removing existing {new_dir}...")
        shutil.rmtree(new_dir)
    
    print(f"\n📁 Creating new folder structure...")
    os.makedirs(new_dir, exist_ok=True)
    
    # Move main script
    if os.path.exists(old_script):
        print(f"📝 Moving and renaming main script...")
        shutil.move(old_script, os.path.join(new_dir, new_script))
        print(f"   ✅ {old_script} → {new_dir}/{new_script}")
    
    # Move modules folder
    if os.path.exists(old_modules):
        print(f"📁 Moving and renaming modules folder...")
        shutil.move(old_modules, os.path.join(new_dir, new_modules))
        print(f"   ✅ {old_modules}/ → {new_dir}/{new_modules}/")
    
    # Move cache if it exists
    cache_candidates = ["cache", "ytfast-cache", f"{old_script.split('.')[0]}-cache"]
    for cache_dir in cache_candidates:
        if os.path.exists(cache_dir):
            print(f"💾 Moving cache directory...")
            shutil.move(cache_dir, os.path.join(new_dir, "cache"))
            print(f"   ✅ {cache_dir}/ → {new_dir}/cache/")
            break
    
    # Move any other related files
    moved_files = []
    for file in os.listdir('.'):
        if file.startswith('ytfast') and file not in [old_script, old_modules]:
            if os.path.isfile(file):
                shutil.move(file, os.path.join(new_dir, file))
                moved_files.append(file)
    
    if moved_files:
        print(f"📄 Moved additional files: {', '.join(moved_files)}")
    
    # Update imports in the new structure
    print(f"\n🔧 Updating imports...")
    update_imports(new_dir, old_modules, new_modules)
    
    # Create migration report
    print(f"\n✨ Migration completed successfully!")
    print(f"\n📋 Migration Summary:")
    print(f"   Old location: ./{old_script}")
    print(f"   New location: ./{new_dir}/{new_script}")
    print(f"\n⚠️  IMPORTANT - Update OBS:")
    print(f"   1. In OBS: Tools → Scripts")
    print(f"   2. Remove the old script: {old_script}")
    print(f"   3. Add the new script: {new_dir}/{new_script}")
    print(f"   4. Your settings will be preserved")
    
    # Create a backup note
    backup_file = "MIGRATION_BACKUP_INFO.txt"
    with open(backup_file, 'w') as f:
        f.write(f"Migration completed on {Path.ctime(Path(new_dir))}\n")
        f.write(f"Old script: {old_script}\n")
        f.write(f"New script: {new_dir}/{new_script}\n")
        f.write("\nIf you need to revert, manually move files back to original locations.\n")
    
    print(f"\n📝 Backup info saved to: {backup_file}")
    
    return True


def update_imports(directory, old_module, new_module):
    """Update all Python imports in the directory."""
    updated_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Skip cache directories
        if 'cache' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace imports
                    new_content = content.replace(f'from {old_module}', f'from {new_module}')
                    new_content = new_content.replace(f'import {old_module}', f'import {new_module}')
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        updated_count += 1
                        print(f"   ✅ Updated: {os.path.relpath(filepath, directory)}")
                
                except Exception as e:
                    print(f"   ⚠️  Error updating {filepath}: {e}")
    
    print(f"   📊 Updated {updated_count} files")


def main():
    """Main entry point."""
    try:
        success = migrate_to_folders()
        if success:
            print("\n✅ Migration successful! Please update your OBS script reference.")
        else:
            print("\n❌ Migration failed or was cancelled.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
