#!/usr/bin/env python3

"""
Fix Import Script

This script automatically updates all import statements in the codebase
to use the proper 'src.' prefix for absolute imports of the main packages.
"""

import os
import re
import sys
from pathlib import Path

# Define the regex patterns for imports to update
IMPORT_PATTERNS = [
    r'^from\s+(domain|infrastructure|application|presentation)\s+import',
    r'^from\s+(domain|infrastructure|application|presentation)\.',
    r'^import\s+(domain|infrastructure|application|presentation)\s+',
    r'^import\s+(domain|infrastructure|application|presentation)\.'
]

# Define the replacement functions for each pattern
def replace_import(match, line):
    # Don't modify imports in the modules directory
    if 'modules/' in line or 'modules\\' in line:
        return line
    
    # Add 'src.' prefix to the imports
    if line.startswith('from '):
        parts = line.split(' import ')
        if len(parts) == 2:
            fromPart = parts[0].replace('from ', 'from src.')
            return f"{fromPart} import {parts[1]}"
    elif line.startswith('import '):
        return line.replace('import ', 'import src.')
    
    return line

def process_file(file_path):
    """Process a single Python file and update its imports."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip files that already have the correct imports
    if 'from src.domain' in content or 'from src.infrastructure' in content:
        print(f"Skipping {file_path} - already has correct imports")
        return 0
    
    # Split into lines for easier processing
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        # Check if this line matches any of our import patterns
        for pattern in IMPORT_PATTERNS:
            if re.match(pattern, line):
                new_line = replace_import(None, line)
                if new_line != line:
                    lines[i] = new_line
                    modified = True
                break
    
    if modified:
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Updated imports in {file_path}")
        return 1
    else:
        print(f"No changes needed for {file_path}")
        return 0

def main():
    """Main function to process all Python files in the project."""
    # Get the project root directory
    project_root = Path(os.path.dirname(os.path.abspath(__file__)))
    src_dir = project_root / 'src'
    
    # Find all Python files in the src directory (excluding the modules directory)
    python_files = []
    for root, dirs, files in os.walk(src_dir):
        # Skip the modules directory
        if 'modules' in root.split(os.sep):
            continue
            
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to process")
    
    # Process each file
    modified_count = 0
    for file_path in python_files:
        modified_count += process_file(file_path)
    
    print(f"Updated imports in {modified_count} files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
