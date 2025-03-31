#!/usr/bin/env python3
"""
Zendesk AI Integration - Universal Installer

This script is a streamlined installer that works on Windows, macOS, and Linux.
It performs the following tasks:
1. Checks for Python 3.9+ installation
2. Downloads prerequisites checker and setup script
3. Runs the setup process

Usage: python install.py
"""

import os
import sys
import platform
import subprocess
import urllib.request
import tempfile
import shutil
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

def download_files():
    """Download required installer files"""
    print_header("Downloading Setup Files")
    
    # Update with the actual repository URL
    repo_url = "https://raw.githubusercontent.com/yourusername/zendesk-ai-integration/main"
    
    files_to_download = {
        "check_prerequisites.py": f"{repo_url}/check_prerequisites.py",
        "setup.py": f"{repo_url}/setup.py",
        ".env.example": f"{repo_url}/.env.example"
    }
    
    success = True
    for filename, url in files_to_download.items():
        file_path = Path(filename)
        print(f"Downloading {filename}...", end=" ")
        try:
            # Skip download if file already exists
            if file_path.exists():
                print(f"{GREEN}Already exists{END}")
                continue
                
            # Download the file with proper error handling
            try:
                with urllib.request.urlopen(url, timeout=30) as response, open(file_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                print(f"{GREEN}Done{END}")
            except urllib.error.URLError as e:
                print(f"{RED}Failed{END}")
                print(f"  Error: {e.reason}")
                success = False
            except Exception as e:
                print(f"{RED}Failed{END}")
                print(f"  Error: {e}")
                success = False
        except Exception as e:
            print(f"{RED}Failed{END}")
            print(f"  Error: {e}")
            success = False
    
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
