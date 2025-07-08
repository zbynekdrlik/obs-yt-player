#!/usr/bin/env python3
"""
YouTube Player Instance Setup Helper
====================================

This script automates the process of creating new YouTube player instances
for OBS Studio by copying and configuring player folders.

Usage:
    python setup_new_instance.py <source> <target>
    
Example:
    python setup_new_instance.py main worship
    
This will create yt-player-worship/ from yt-player-main/
"""

import os
import shutil
import sys
import re
from pathlib import Path


def update_file_content(filepath, replacements):
    """Update file content with multiple replacements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  ⚠️  Error updating {filepath}: {e}")
        return False


def setup_instance(source_name, target_name):
    """Set up a new YouTube player instance from an existing one."""
    
    # Validate names
    if not re.match(r'^[a-zA-Z0-9_-]+$', target_name):
        print(f"❌ Error: Target name '{target_name}' contains invalid characters.")
        print("   Use only letters, numbers, hyphens, and underscores.")
        return False
    
    source_dir = f"yt-player-{source_name}"
    target_dir = f"yt-player-{target_name}"
    
    # Check if source exists
    if not os.path.exists(source_dir):
        print(f"❌ Error: Source directory '{source_dir}' not found.")
        print(f"   Available players: {list_available_players()}")
        return False
    
    # Check if target already exists
    if os.path.exists(target_dir):
        print(f"❌ Error: Target directory '{target_dir}' already exists.")
        response = input("   Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Operation cancelled.")
            return False
        print(f"   Removing existing {target_dir}...")
        shutil.rmtree(target_dir)
    
    print(f"\n🚀 Creating new YouTube player instance: {target_name}")
    print(f"   Source: {source_dir}")
    print(f"   Target: {target_dir}")
    
    # Copy the entire folder
    print(f"\n📁 Copying folder structure...")
    try:
        shutil.copytree(source_dir, target_dir)
        print(f"   ✅ Folder copied successfully")
    except Exception as e:
        print(f"   ❌ Error copying folder: {e}")
        return False
    
    # Define file mappings
    source_script = f"yt{source_name}.py"
    target_script = f"yt{target_name}.py"
    source_modules = f"yt{source_name}_modules"
    target_modules = f"yt{target_name}_modules"
    
    # Rename main script
    old_script_path = os.path.join(target_dir, source_script)
    new_script_path = os.path.join(target_dir, target_script)
    
    if os.path.exists(old_script_path):
        print(f"\n📝 Renaming main script...")
        os.rename(old_script_path, new_script_path)
        print(f"   ✅ {source_script} → {target_script}")
    else:
        print(f"\n⚠️  Warning: Main script {source_script} not found in {target_dir}")
    
    # Rename modules folder
    old_modules_path = os.path.join(target_dir, source_modules)
    new_modules_path = os.path.join(target_dir, target_modules)
    
    if os.path.exists(old_modules_path):
        print(f"\n📁 Renaming modules folder...")
        os.rename(old_modules_path, new_modules_path)
        print(f"   ✅ {source_modules}/ → {target_modules}/")
    else:
        print(f"\n⚠️  Warning: Modules folder {source_modules} not found in {target_dir}")
    
    # Update imports and configuration
    print(f"\n🔧 Updating Python files...")
    
    # Define replacements
    replacements = [
        (f"from {source_modules}", f"from {target_modules}"),
        (f"import {source_modules}", f"import {target_modules}"),
        (f'SCENE_NAME = "yt{source_name}"', f'SCENE_NAME = "yt{target_name}"'),
        (f'SCENE_NAME = \'yt{source_name}\'', f'SCENE_NAME = \'yt{target_name}\''),
        (f'scene_name = "yt{source_name}"', f'scene_name = "yt{target_name}"'),
        (f'scene_name = \'yt{source_name}\'', f'scene_name = \'yt{target_name}\''),
    ]
    
    # Update all Python files
    updated_count = 0
    for root, dirs, files in os.walk(target_dir):
        # Skip cache directories
        if 'cache' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if update_file_content(filepath, replacements):
                    updated_count += 1
                    print(f"   ✅ Updated: {os.path.relpath(filepath, target_dir)}")
    
    print(f"   📊 Updated {updated_count} Python files")
    
    # Clean up cache directory if it exists
    cache_dir = os.path.join(target_dir, "cache")
    if os.path.exists(cache_dir):
        print(f"\n🧹 Cleaning cache directory...")
        shutil.rmtree(cache_dir)
        os.makedirs(cache_dir)
        print(f"   ✅ Cache directory cleaned")
    
    # Create success summary
    print(f"\n✨ Success! New instance '{target_name}' created")
    print(f"\n📋 Configuration Summary:")
    print(f"   Directory: {target_dir}/")
    print(f"   Main Script: {target_script}")
    print(f"   Modules Folder: {target_modules}/")
    print(f"   OBS Scene Name: yt{target_name}")
    print(f"\n📌 Next Steps:")
    print(f"   1. In OBS, add the script from: {target_dir}/{target_script}")
    print(f"   2. Create a scene named: yt{target_name}")
    print(f"   3. Configure the playlist URL in script settings")
    
    return True


def list_available_players():
    """List all available player instances."""
    players = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('yt-player-'):
            player_name = item.replace('yt-player-', '')
            players.append(player_name)
    return players


def main():
    """Main entry point."""
    print("🎥 YouTube Player Instance Setup Helper")
    print("=" * 40)
    
    if len(sys.argv) == 1:
        # Interactive mode
        print("\nAvailable player instances:")
        players = list_available_players()
        if not players:
            print("❌ No player instances found. Please create yt-player-main/ first.")
            return
        
        for i, player in enumerate(players, 1):
            print(f"  {i}. {player}")
        
        print("\nUsage: python setup_new_instance.py <source> <target>")
        print("Example: python setup_new_instance.py main worship")
        return
    
    if len(sys.argv) != 3:
        print("\n❌ Error: Invalid number of arguments")
        print("Usage: python setup_new_instance.py <source> <target>")
        print("Example: python setup_new_instance.py main worship")
        return
    
    source_name = sys.argv[1]
    target_name = sys.argv[2]
    
    if source_name == target_name:
        print("❌ Error: Source and target names cannot be the same")
        return
    
    setup_instance(source_name, target_name)


if __name__ == "__main__":
    main()
