#!/usr/bin/env python3
"""
Zendesk AI Integration - Universal Installer

This script is a streamlined installer that works on Windows, macOS, and Linux.
It performs the following tasks:
1. Checks for Python 3.9+ installation
2. Downloads prerequisites checker and setup script
3. Runs the setup process

Usage: python install.py

Environment Variables:
    ZENDESK_AI_ORG: GitHub organization name (default: exxactcorp)
    ZENDESK_AI_REPO: GitHub repository name (default: zendesk-ai-integration)
    ZENDESK_AI_BRANCH: GitHub branch name (default: main)
    SKIP_CHECKSUM_VERIFY: Skip checksum verification (default: false)
"""

import os
import sys
import platform
import subprocess
import urllib.request
import tempfile
import shutil
import hashlib
import time
from pathlib import Path

# Terminal colors for better readability (when supported)
def supports_color():
    """Check if the terminal supports ANSI colors"""
    plat = platform.system()
    
    # Windows terminal detection (modern Windows Terminal support)
    if plat == 'Windows':
        if 'ANSICON' in os.environ or 'WT_SESSION' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
            return True
        return False
    
    # Unix systems (macOS and Linux)
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    term = os.environ.get('TERM', '')
    return is_a_tty and term != 'dumb'

if supports_color():
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'
else:
    GREEN = YELLOW = RED = BLUE = BOLD = END = ''

def print_header(message):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}=== {message} ==={END}\n")

def print_status(message, status=None):
    """Print a status message with optional status indicator"""
    if status == "success":
        status_str = f"{GREEN}✓{END} "
    elif status == "warning":
        status_str = f"{YELLOW}⚠{END} "
    elif status == "error":
        status_str = f"{RED}✗{END} "
    else:
        status_str = ""
    
    print(f"{status_str}{message}")

def check_python_version():
    """Verify Python version is 3.9 or higher"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} detected", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} detected (version 3.9+ required)", "error")
        print("Please install Python 3.9 or higher from https://www.python.org/downloads/")
        return False

def verify_checksum(file_path, expected_checksum):
    """
    Verify the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected SHA-256 checksum as a hex string
        
    Returns:
        True if the checksum matches, False otherwise
    """
    # Calculate file checksum
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # Read the file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Get the hexadecimal digest
        file_checksum = sha256_hash.hexdigest()
        
        # Compare with expected checksum
        return file_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        print(f"{RED}Error verifying checksum{END}: {str(e)}")
        return False

def download_with_progress(url, file_path):
    """
    Download a file with progress reporting for larger files.
    
    Args:
        url: URL to download from
        file_path: Path where the file should be saved
        
    Returns:
        True if download was successful, False otherwise
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            # Get file size if available
            file_size = int(response.headers.get('Content-Length', 0))
            
            # Use progress bar for larger files
            if file_size > 100000:  # For files larger than ~100KB
                with open(file_path, 'wb') as out_file:
                    downloaded = 0
                    block_size = 8192  # 8KB blocks
                    start_time = time.time()
                    
                    print()  # Start on a new line
                    
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                            
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        
                        # Calculate and display progress
                        if file_size > 0:
                            percent = downloaded * 100 / file_size
                            bar_length = 30
                            filled_length = int(bar_length * downloaded // file_size)
                            bar = '█' * filled_length + '░' * (bar_length - filled_length)
                            
                            # Calculate speed
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded / (1024 * elapsed_time)  # KB/s
                                print(f"\r  Progress: |{bar}| {percent:.1f}% ({downloaded/1024:.1f}KB/{file_size/1024:.1f}KB) {speed:.1f}KB/s", end='')
                            else:
                                print(f"\r  Progress: |{bar}| {percent:.1f}% ({downloaded/1024:.1f}KB/{file_size/1024:.1f}KB)", end='')
                    
                    print()  # End with a new line
            else:
                # For smaller files, just download without progress bar
                with open(file_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
        
        return True
    except urllib.error.URLError as e:
        print(f"{RED}URLError{END}: {e.reason}")
        return False
    except Exception as e:
        print(f"{RED}Error{END}: {str(e)}")
        return False

def download_files():
    """
    Download required installer files with improved error handling,
    retries, progress reporting, and checksum verification.
    """
    print_header("Downloading Setup Files")
    
    # Repository details - store organization and repository name separately for flexibility
    org_name = os.environ.get("ZENDESK_AI_ORG", "exxactcorp")
    repo_name = os.environ.get("ZENDESK_AI_REPO", "zendesk-ai-integration")
    branch = os.environ.get("ZENDESK_AI_BRANCH", "main")
    
    # Construct the repository URL
    repo_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{branch}"
    
    # Define files to download with their checksums (SHA-256)
    files_to_download = {
        "check_prerequisites.py": {
            "url": f"{repo_url}/check_prerequisites.py",
            "checksum": "8d74a2b78ac65f0daa77ac56a770a8262fe312539b4f6ca8f3c2d70c8cbdcfc1"
        },
        "setup.py": {
            "url": f"{repo_url}/setup.py",
            "checksum": "5e6bc76f67c1a9b9e5d56f6eb8c766cb7e0a9fa21fb83d8b5609e5075bce2285"
        },
        ".env.example": {
            "url": f"{repo_url}/.env.example",
            "checksum": "3a2b98f9eecd06a7a15a6fb062f3c8f3e6d3fd4c9eaec0c61d9638670be25521"
        },
        "requirements.txt": {
            "url": f"{repo_url}/requirements.txt",
            "checksum": "e3f0263a9b5586e9554ec30392ebcd1ccdda7abd692ab85b4d0c9b9affbcc37a"
        }
    }
    
    # Check if verification should be skipped (for development or testing)
    skip_verification = os.environ.get("SKIP_CHECKSUM_VERIFY", "").lower() in ("true", "1", "yes")
    
    # Track overall success
    success = True
    failed_files = []
    
    for filename, file_info in files_to_download.items():
        url = file_info["url"]
        expected_checksum = file_info["checksum"]
        file_path = Path(filename)
        
        print(f"Downloading {filename}...", end=" ")
        
        # Skip download if file already exists and checksum matches
        if file_path.exists():
            if skip_verification:
                print(f"{GREEN}Already exists (checksum verification skipped){END}")
                continue
                
            # Verify existing file checksum
            if verify_checksum(file_path, expected_checksum):
                print(f"{GREEN}Already exists (checksum verified){END}")
                continue
            else:
                print(f"{YELLOW}Already exists but checksum mismatch. Redownloading...{END}")
        
        # Try to download the file with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                download_success = download_with_progress(url, file_path)
                
                if not download_success:
                    print(f"{RED}Failed to download{END}")
                    success = False
                    failed_files.append(filename)
                    break
                
                # Skip verification if requested
                if skip_verification:
                    print(f"{GREEN}Downloaded successfully (checksum verification skipped){END}")
                    break
                
                # Verify checksum
                if verify_checksum(file_path, expected_checksum):
                    print(f"{GREEN}Downloaded and verified{END}")
                    break
                else:
                    # Checksum failed, retry if we have attempts left
                    if attempt < max_retries - 1:
                        print(f"{YELLOW}Checksum verification failed. Retrying... ({attempt+1}/{max_retries}){END}")
                        # Remove the corrupt file
                        file_path.unlink(missing_ok=True)
                    else:
                        print(f"{RED}Checksum verification failed after {max_retries} attempts{END}")
                        success = False
                        failed_files.append(filename)
                        # Keep the last downloaded file for debugging
            
            except Exception as e:
                # Handle download errors
                if attempt < max_retries - 1:
                    print(f"{YELLOW}Error: {str(e)}. Retrying... ({attempt+1}/{max_retries}){END}")
                else:
                    print(f"{RED}Failed{END}")
                    print(f"  Error: {str(e)}")
                    success = False
                    failed_files.append(filename)
    
    # Report on download failures if any
    if not success:
        print(f"\n{RED}Failed to download the following files: {', '.join(failed_files)}{END}")
        fallback_message = (
            f"\n{YELLOW}You can try manually downloading these files from:\n"
            f"https://github.com/{org_name}/{repo_name}/tree/{branch}{END}\n"
        )
        print(fallback_message)
    
    return success

def run_prerequisites_check():
    """Run the prerequisites checker"""
    print_header("Checking Prerequisites")
    
    prereq_script = Path("check_prerequisites.py")
    if not prereq_script.exists():
        print_status(f"{prereq_script} not found", "error")
        return False
    
    try:
        subprocess.run([sys.executable, str(prereq_script)], check=True)
        return True
    except subprocess.CalledProcessError:
        print_status("Prerequisite check failed", "error")
        return False

def run_setup():
    """Run the main setup script"""
    print_header("Running Setup")
    
    setup_script = Path("setup.py")
    if not setup_script.exists():
        print_status(f"{setup_script} not found", "error")
        return False
    
    try:
        subprocess.run([sys.executable, str(setup_script)], check=True)
        return True
    except subprocess.CalledProcessError:
        print_status("Setup failed", "error")
        return False

def main():
    """Main installer function"""
    print(f"\n{BOLD}Zendesk AI Integration - Universal Installer{END}\n")
    print(f"This installer will set up the Zendesk AI Integration on {platform.system()}.\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Download required files
    if not download_files():
        print_status("Failed to download required files", "error")
        sys.exit(1)
    
    # Run prerequisites check
    if not run_prerequisites_check():
        choice = input("\nContinue with setup anyway? (y/n): ").lower()
        if choice != 'y':
            print("Installation aborted.")
            sys.exit(1)
    
    # Run setup
    if not run_setup():
        print_status("Setup failed", "error")
        sys.exit(1)
    
    print(f"\n{GREEN}{BOLD}Installation completed successfully!{END}")

if __name__ == "__main__":
    main()
