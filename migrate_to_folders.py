#!/usr/bin/env python3
"""
Migration Script: Single-File to Folder-Based Structure
=======================================================

This script helps migrate from the old single-file YouTube player setup
to the new folder-based structure.

It will:
1. Create yt-player-main/ directory
2. Move ytfast.py and ytfast_modules/ into it
3. Update .gitignore if needed
4. Provide instructions for updating OBS

Usage:
    python migrate_to_folders.py
"""

import os
import shutil
import sys
from pathlib import Path


def check_current_structure():
    """Check if we're in the right directory with the expected files."""
    required_files = ['ytfast.py', 'ytfast_modules']
    missing = []
    
    for item in required_files:
        if not os.path.exists(item):
            missing.append(item)
    
    if missing:
        print(f"❌ Error: Missing required files/folders: {', '.join(missing)}")
        print("   Please run this script from your obs-scripts directory")
        print("   that contains ytfast.py and ytfast_modules/")
        return False
    
    return True


def check_destination():
    """Check if destination already exists."""
    if os.path.exists('yt-player-main'):
        print("⚠️  Warning: yt-player-main/ already exists")
        response = input("   Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Migration cancelled.")
            return False
        print("   Removing existing yt-player-main/...")
        shutil.rmtree('yt-player-main')
    
    return True


def create_folder_structure():
    """Create the new folder structure."""
    print("\n📁 Creating folder structure...")
    
    # Create main directory
    os.makedirs('yt-player-main', exist_ok=True)
    print("   ✅ Created yt-player-main/")
    
    # Create cache directory
    os.makedirs('yt-player-main/cache', exist_ok=True)
    print("   ✅ Created yt-player-main/cache/")
    
    return True


def move_files():
    """Move files to the new structure."""
    print("\n📦 Moving files...")
    
    # Move ytfast.py
    if os.path.exists('ytfast.py'):
        shutil.move('ytfast.py', 'yt-player-main/ytfast.py')
        print("   ✅ Moved ytfast.py → yt-player-main/ytfast.py")
    
    # Move ytfast_modules
    if os.path.exists('ytfast_modules'):
        shutil.move('ytfast_modules', 'yt-player-main/ytfast_modules')
        print("   ✅ Moved ytfast_modules/ → yt-player-main/ytfast_modules/")
    
    # Move cache contents if they exist
    if os.path.exists('cache'):
        print("\n📋 Found existing cache directory")
        response = input("   Do you want to move cache contents? (y/N): ")
        if response.lower() == 'y':
            # Move contents, not the directory itself
            for item in os.listdir('cache'):
                src = os.path.join('cache', item)
                dst = os.path.join('yt-player-main', 'cache', item)
                shutil.move(src, dst)
            os.rmdir('cache')
            print("   ✅ Moved cache contents")
        else:
            print("   ⏭️  Skipped cache contents")
    
    return True


def update_gitignore():
    """Update .gitignore if needed."""
    print("\n📝 Checking .gitignore...")
    
    gitignore_additions = [
        "# YouTube Player instances (uncomment to ignore specific instances)",
        "# yt-player-*/",
        "# !yt-player-main/",
        "",
        "# Or ignore all except main",
        "# yt-player-*/*",
        "# !yt-player-main/*",
        ""
    ]
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            content = f.read()
        
        if 'yt-player-' not in content:
            print("   📝 Adding folder patterns to .gitignore...")
            with open('.gitignore', 'a') as f:
                f.write('\n' + '\n'.join(gitignore_additions))
            print("   ✅ Updated .gitignore")
        else:
            print("   ✅ .gitignore already has yt-player patterns")
    else:
        print("   ℹ️  No .gitignore found, skipping")
    
    return True


def create_readme():
    """Create a README in the yt-player-main directory."""
    readme_content = """# YouTube Player - Main Instance

This is the main YouTube player instance for OBS Studio.

## Quick Start

1. In OBS, remove the old script reference
2. Add this script: `yt-player-main/ytfast.py`
3. Your settings should be preserved

## Creating Additional Instances

Use the helper script in the parent directory:

```bash
cd ..
python setup_new_instance.py main worship
```

This will create a new `yt-player-worship/` instance.

## Configuration

- Scene name: `ytfast`
- Cache location: `yt-player-main/cache/`
- Modules: `yt-player-main/ytfast_modules/`

See `docs/FOLDER_BASED_INSTANCES.md` for more information.
"""
    
    with open('yt-player-main/README.md', 'w') as f:
        f.write(readme_content)
    
    print("\n📄 Created README.md in yt-player-main/")
    return True


def print_next_steps():
    """Print instructions for what to do next."""
    print("\n" + "="*50)
    print("✨ Migration Complete!")
    print("="*50)
    
    print("\n📋 Next Steps:")
    print("\n1. Update OBS:")
    print("   - Open OBS Studio")
    print("   - Go to Tools → Scripts")
    print("   - Remove the old ytfast.py reference")
    print("   - Click + and add: yt-player-main/ytfast.py")
    print("   - Your settings should be preserved")
    
    print("\n2. Test the setup:")
    print("   - Verify the script loads correctly")
    print("   - Check that your playlist still works")
    print("   - Ensure videos play as expected")
    
    print("\n3. Create additional instances (optional):")
    print("   python setup_new_instance.py main worship")
    print("   python setup_new_instance.py main kids")
    
    print("\n📁 New Structure:")
    print("   yt-player-main/")
    print("   ├── ytfast.py")
    print("   ├── ytfast_modules/")
    print("   ├── cache/")
    print("   └── README.md")
    
    print("\n📚 Documentation:")
    print("   See docs/FOLDER_BASED_INSTANCES.md for detailed information")
    
    print("\n⚠️  Important:")
    print("   - The old file locations no longer exist")
    print("   - You MUST update OBS to use the new path")
    print("   - Each instance now lives in its own folder")


def main():
    """Main migration process."""
    print("🔄 YouTube Player Migration Tool")
    print("   Single-File → Folder-Based Structure")
    print("="*40)
    
    # Check prerequisites
    if not check_current_structure():
        return False
    
    if not check_destination():
        return False
    
    print("\n📋 This will:")
    print("   1. Create yt-player-main/ directory")
    print("   2. Move ytfast.py into it")
    print("   3. Move ytfast_modules/ into it")
    print("   4. Create cache directory")
    print("   5. Update .gitignore (optional)")
    
    response = input("\nProceed with migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return False
    
    # Perform migration
    if not create_folder_structure():
        return False
    
    if not move_files():
        return False
    
    update_gitignore()
    create_readme()
    
    # Show next steps
    print_next_steps()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during migration: {e}")
        sys.exit(1)
