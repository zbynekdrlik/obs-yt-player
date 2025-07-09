#!/usr/bin/env python3
"""
Rename ytfast to ytplay Migration Script
========================================

This script renames all ytfast references to ytplay throughout the codebase.
Run this from the repository root.

Usage:
    python rename_to_ytplay.py
"""

import os
import re
import shutil
from pathlib import Path


def update_file_content(filepath, replacements):
    """Update file content with multiple replacements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ⚠️  Error updating {filepath}: {e}")
        return False


def rename_ytfast_to_ytplay():
    """Perform the complete rename operation."""
    print("🚀 Renaming ytfast to ytplay...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("yt-player-main"):
        print("❌ Error: yt-player-main directory not found.")
        print("   Please run this script from the repository root.")
        return False
    
    # Step 1: Rename main script
    print("\n📝 Step 1: Renaming main script...")
    old_script = "yt-player-main/ytfast.py"
    new_script = "yt-player-main/ytplay.py"
    
    if os.path.exists(old_script):
        if os.path.exists(new_script):
            os.remove(old_script)
            print(f"   ✅ Removed old {old_script} (ytplay.py already exists)")
        else:
            os.rename(old_script, new_script)
            print(f"   ✅ Renamed {old_script} → {new_script}")
    else:
        print(f"   ℹ️  {old_script} not found (may already be renamed)")
    
    # Step 2: Rename modules directory
    print("\n📁 Step 2: Renaming modules directory...")
    old_modules = "yt-player-main/ytfast_modules"
    new_modules = "yt-player-main/ytplay_modules"
    
    if os.path.exists(old_modules):
        if os.path.exists(new_modules):
            # Remove old directory if new one exists
            shutil.rmtree(old_modules)
            print(f"   ✅ Removed old {old_modules} (ytplay_modules already exists)")
        else:
            os.rename(old_modules, new_modules)
            print(f"   ✅ Renamed {old_modules} → {new_modules}")
    else:
        print(f"   ℹ️  {old_modules} not found (may already be renamed)")
    
    # Step 3: Update all Python files in yt-player-main
    print("\n🔧 Step 3: Updating Python files...")
    
    # Define replacements
    replacements = [
        # Module imports
        ("from ytfast_modules", "from ytplay_modules"),
        ("import ytfast_modules", "import ytplay_modules"),
        
        # Script path references in config.py
        ("ytfast.py'", "ytplay.py'"),
        ('ytfast.py"', 'ytplay.py"'),
        
        # Any hardcoded references
        ("ytfast-cache", "ytplay-cache"),
        
        # Scene name references (for default instance)
        ('SCENE_NAME = "ytfast"', 'SCENE_NAME = "ytplay"'),
        ("SCENE_NAME = 'ytfast'", "SCENE_NAME = 'ytplay'"),
    ]
    
    # Update all Python files in yt-player-main
    updated_count = 0
    for root, dirs, files in os.walk("yt-player-main"):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if update_file_content(filepath, replacements):
                    updated_count += 1
                    print(f"   ✅ Updated: {os.path.relpath(filepath)}")
    
    print(f"   📊 Updated {updated_count} Python files")
    
    # Step 4: Update setup_new_instance.py
    print("\n📋 Step 4: Updating setup_new_instance.py...")
    setup_replacements = [
        # Update default source references
        ("ytfast.py", "ytplay.py"),
        ("ytfast_modules", "ytplay_modules"),
        ('source_script = f"yt{source_name}.py"', 'source_script = f"yt{source_name}.py"'),
        
        # Update the example in comments
        ("# Example:\n    python setup_new_instance.py main worship", 
         "# Example:\n    python setup_new_instance.py play worship"),
        ("Example: python setup_new_instance.py main worship",
         "Example: python setup_new_instance.py play worship"),
         
        # Update folder examples in output
        ("yt-player-main/", "yt-player-play/"),
    ]
    
    if update_file_content("setup_new_instance.py", setup_replacements):
        print("   ✅ Updated setup_new_instance.py")
    
    # Step 5: Update documentation
    print("\n📚 Step 5: Updating documentation...")
    
    doc_replacements = [
        ("ytfast.py", "ytplay.py"),
        ("ytfast_modules", "ytplay_modules"),
        ("ytfast", "ytplay"),  # General references
        
        # But preserve folder name references that shouldn't change
        ("yt-player-play/", "yt-player-main/"),  # Revert this specific change
    ]
    
    # Update README.md
    if update_file_content("README.md", doc_replacements):
        print("   ✅ Updated README.md")
    
    # Update docs directory
    doc_files_updated = 0
    if os.path.exists("docs"):
        for file in os.listdir("docs"):
            if file.endswith('.md'):
                filepath = os.path.join("docs", file)
                if update_file_content(filepath, doc_replacements):
                    doc_files_updated += 1
                    print(f"   ✅ Updated: {filepath}")
    
    print(f"   📊 Updated {doc_files_updated} documentation files")
    
    # Step 6: Update THREAD_PROGRESS.md
    print("\n📝 Step 6: Updating THREAD_PROGRESS.md...")
    
    thread_content = """# Thread Progress Tracking

## CRITICAL CURRENT STATE
**⚠️ EXACTLY WHERE WE ARE RIGHT NOW:**
- [x] Successfully renamed ytfast → ytplay throughout codebase
- [x] Main script: ytfast.py → ytplay.py
- [x] Modules folder: ytfast_modules/ → ytplay_modules/
- [x] Updated all imports and references
- [ ] **Ready for testing**: Need to verify everything works after rename

## Rename Operation Completed
1. ✅ Renamed main script to ytplay.py
2. ✅ Renamed modules folder to ytplay_modules/
3. ✅ Updated all imports in Python files
4. ✅ Updated config.py references
5. ✅ Updated documentation
6. ✅ Updated setup_new_instance.py

## Next Steps
1. **Test the renamed script in OBS**
2. **Verify all functionality works**
3. **Update version to 4.0.0**
4. **Prepare for PR merge**

## Version for Release
**v4.0.0** - Major changes:
- Folder-based multi-instance architecture
- Renamed from ytfast to ytplay
- Complete isolation between instances

## Testing Checklist
- [ ] Script loads in OBS without errors
- [ ] Video playback works
- [ ] Playlist sync works
- [ ] All playback modes work
- [ ] Multi-instance setup works with helper script

## Critical Information
- Branch: `feature/folder-based-instances`
- PR: #29
- Status: Rename complete, ready for testing
"""
    
    with open("THREAD_PROGRESS.md", "w", encoding="utf-8") as f:
        f.write(thread_content)
    print("   ✅ Updated THREAD_PROGRESS.md")
    
    # Final summary
    print("\n✨ Rename operation completed successfully!")
    print("\n📋 Summary of changes:")
    print("   • ytfast.py → ytplay.py")
    print("   • ytfast_modules/ → ytplay_modules/")
    print("   • Updated all imports and references")
    print("   • Updated documentation")
    print("\n🎯 Next steps:")
    print("   1. Test the script in OBS")
    print("   2. Verify all functionality")
    print("   3. Update version to 4.0.0")
    print("   4. Commit and push changes")
    
    return True


def main():
    """Main entry point."""
    print("🔄 YTFast → YTPlay Rename Tool")
    print("=" * 40)
    
    # Confirm operation
    print("\nThis will rename all ytfast references to ytplay.")
    print("Make sure you have committed any pending changes first!")
    
    response = input("\nProceed with rename? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Perform rename
    success = rename_ytfast_to_ytplay()
    
    if success:
        print("\n✅ Done! Please test the changes before committing.")
    else:
        print("\n❌ Rename failed. Check the errors above.")


if __name__ == "__main__":
    main()
