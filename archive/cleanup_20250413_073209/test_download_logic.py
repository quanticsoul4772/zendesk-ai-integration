#!/usr/bin/env python3
"""
Test Script for File Download Logic

This script provides an easy way to test the improved file download logic
in install.py without running the entire installation process.

Usage:
  python test_download_logic.py
"""

import os
import sys
import platform
import hashlib
import tempfile
from pathlib import Path

# Import functions from install.py
try:
    from install import download_files, verify_checksum, download_with_progress
    from install import GREEN, RED, YELLOW, BLUE, BOLD, END
except ImportError:
    print("Error: Could not import functions from install.py")
    sys.exit(1)

def main():
    """Test the file download logic"""
    print(f"\n{BOLD}Testing File Download Logic{END}\n")
    
    # Create a temporary directory for test downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        print(f"Using temporary directory: {test_dir}")
        
        # Change to test directory
        os.chdir(test_dir)
        
        # Test the download process
        print(f"\n{BOLD}Testing main download_files function:{END}")
        result = download_files()
        
        if result:
            print(f"\n{GREEN}Test passed: Files downloaded successfully{END}")
        else:
            print(f"\n{RED}Test failed: Some files could not be downloaded{END}")
        
        # List downloaded files
        print(f"\n{BOLD}Files downloaded:{END}")
        for file_path in test_dir.glob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"- {file_path.name} ({size} bytes)")
    
    print(f"\n{BOLD}Test completed{END}")

if __name__ == "__main__":
    main()
