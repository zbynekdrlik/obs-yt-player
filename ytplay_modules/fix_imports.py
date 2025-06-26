#!/usr/bin/env python3
"""
Temporary script to fix relative imports in all modules.
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Track if we made changes
    original_content = content
    
    # Fix relative imports
    # Pattern to match: from .module import ...
    content = re.sub(r'from \.([a-zA-Z_]+)', r'from ytplay_modules.\1', content)
    
    # Pattern to match: from . import module
    content = re.sub(r'from \. import', 'from ytplay_modules import', content)
    
    # Return True if we made changes
    return content != original_content, content

def main():
    """Fix imports in all Python files."""
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and filename != 'fix_imports.py':
            filepath = os.path.join(modules_dir, filename)
            changed, new_content = fix_imports_in_file(filepath)
            
            if changed:
                print(f"Fixed imports in {filename}")
                with open(filepath, 'w') as f:
                    f.write(new_content)
            else:
                print(f"No changes needed in {filename}")

if __name__ == '__main__':
    main()
