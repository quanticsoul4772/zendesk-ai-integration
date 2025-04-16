#!/usr/bin/env python3
"""
Update Checksums for File Download Logic

This script calculates SHA-256 checksums for the files downloaded by install.py
and updates the checksums in the install.py script.

Usage:
  python update_checksums.py

Environment Variables:
    ZENDESK_AI_ORG: GitHub organization name (default: exxactcorp)
    ZENDESK_AI_REPO: GitHub repository name (default: zendesk-ai-integration)
    ZENDESK_AI_BRANCH: GitHub branch name (default: main)
"""

import os
import sys
import hashlib
import tempfile
import re
import urllib.request
from pathlib import Path

def calculate_checksum(file_path):
    """Calculate SHA-256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # Read the file in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Get the hexadecimal digest
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating checksum for {file_path}: {str(e)}")
        return None

def download_file(url, file_path):
    """Download a file from URL"""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(file_path, 'wb') as out_file:
                out_file.write(response.read())
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def update_install_py(checksums):
    """Update checksums in install.py"""
    install_py_path = Path("install.py")
    
    if not install_py_path.exists():
        print("Error: install.py not found in current directory")
        return False
    
    # Read the content of install.py
    with open(install_py_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update each checksum
    updated_content = content
    for filename, checksum in checksums.items():
        # Create a regex pattern to find and replace the checksum
        pattern = rf'"{filename}":\s*{{\s*"url":\s*f"{{repo_url}}/{filename}",\s*"checksum":\s*"[a-fA-F0-9]+"'
        replacement = f'"{filename}": {{"url": f"{{repo_url}}/{filename}", "checksum": "{checksum}"'
        
        # Replace the checksum
        updated_content = re.sub(pattern, replacement, updated_content)
    
    # Write the updated content back to install.py
    with open(install_py_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    return True

def main():
    """Main function to update checksums"""
    print("Updating checksums for install.py...\n")
    
    # Repository details
    org_name = os.environ.get("ZENDESK_AI_ORG", "exxactcorp")
    repo_name = os.environ.get("ZENDESK_AI_REPO", "zendesk-ai-integration")
    branch = os.environ.get("ZENDESK_AI_BRANCH", "main")
    
    # Construct the repository URL
    repo_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{branch}"
    
    # Files to download and calculate checksums for
    files = [
        "check_prerequisites.py",
        "setup.py",
        ".env.example",
        "requirements.txt"
    ]
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Dictionary to store checksums
        checksums = {}
        
        # Download each file and calculate its checksum
        for filename in files:
            file_url = f"{repo_url}/{filename}"
            file_path = temp_path / filename
            
            print(f"Downloading {filename}...")
            if download_file(file_url, file_path):
                checksum = calculate_checksum(file_path)
                if checksum:
                    checksums[filename] = checksum
                    print(f"  Checksum: {checksum}")
                else:
                    print(f"  Failed to calculate checksum")
            else:
                print(f"  Failed to download file")
        
        # Update install.py with new checksums
        if checksums:
            if update_install_py(checksums):
                print("\nUpdated checksums in install.py successfully")
            else:
                print("\nFailed to update checksums in install.py")
        else:
            print("\nNo checksums to update")

if __name__ == "__main__":
    main()
