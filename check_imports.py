#!/usr/bin/env python3
"""
Temporary script to check which files still need import fixes.
"""

import os
import re

def check_file(filepath):
    """Check if a file has problematic imports."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for relative imports that need fixing
    if re.search(r'^from \.[a-zA-Z_]', content, re.MULTILINE):
        issues.append("Has relative imports (from .)")
    
    # Check for direct imports without ytplay_modules prefix
    # But exclude standard library imports
    direct_imports = re.findall(r'^from ([a-zA-Z_]+) import', content, re.MULTILINE)
    direct_imports += re.findall(r'^import ([a-zA-Z_]+)', content, re.MULTILINE)
    
    # Known standard library modules and third-party modules
    known_modules = {
        'os', 'sys', 'time', 'threading', 'subprocess', 'json', 'queue',
        're', 'pathlib', 'urllib', 'zipfile', 'datetime', 'tempfile',
        'obspython', 'requests', 'google', 'typing'
    }
    
    # Known ytplay_modules that should have prefix
    ytplay_modules = {
        'config', 'state', 'logger', 'main', 'ui', 'tools', 'cache',
        'scene', 'utils', 'playlist', 'download', 'metadata',
        'gemini_metadata', 'normalize', 'playback', 'reprocess'
    }
    
    for module in direct_imports:
        if module in ytplay_modules:
            issues.append(f"Direct import of {module} (should be ytplay_modules.{module})")
    
    return issues

def main():
    """Check all Python files in ytplay_modules."""
    modules_dir = 'ytplay_modules'
    
    print("Checking imports in ytplay_modules...\n")
    
    files_with_issues = []
    
    for filename in sorted(os.listdir(modules_dir)):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(modules_dir, filename)
            issues = check_file(filepath)
            
            if issues:
                files_with_issues.append((filename, issues))
                print(f"❌ {filename}:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print(f"✅ {filename}: OK")
    
    print(f"\nSummary: {len(files_with_issues)} files need fixing")
    
    return files_with_issues

if __name__ == '__main__':
    files = main()
