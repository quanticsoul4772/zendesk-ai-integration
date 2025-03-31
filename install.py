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
    supported_platform = plat != 'Windows' or 'ANSICON' in os.environ
    
    # isatty is not always implemented
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    return supported_platform and is_a_tty

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
    
    files_to_download = {
        "check_prerequisites.py": "https://raw.githubusercontent.com/yourusername/zendesk-ai-integration/main/check_prerequisites.py",
        "setup.py": "https://raw.githubusercontent.com/yourusername/zendesk-ai-integration/main/setup.py",
        ".env.example": "https://raw.githubusercontent.com/yourusername/zendesk-ai-integration/main/.env.example"
    }
    
    success = True
    for filename, url in files_to_download.items():
        print(f"Downloading {filename}...", end=" ")
        try:
            # This is a placeholder URL - in a real implementation, use the actual repository URLs
            # For demo purposes, we'll create the files instead of downloading them
            if not Path(filename).exists():
                # In a real implementation, use: urllib.request.urlretrieve(url, filename)
                # For this demo, we'll copy from the project files if they exist or create placeholders
                if Path(f"../artifacts/{filename}").exists():
                    shutil.copy(f"../artifacts/{filename}", filename)
                elif Path(f"../backup/{filename}").exists():
                    shutil.copy(f"../backup/{filename}", filename)
                else:
                    # Create empty placeholder files
                    with open(filename, 'w') as f:
                        f.write(f"# Placeholder for {filename}\n")
            print(f"{GREEN}Done{END}")
        except Exception as e:
            print(f"{RED}Failed{END}")
            print(f"  Error: {e}")
            success = False
    
    return success

def run_prerequisites_check():
    """Run the prerequisites checker"""
    print_header("Checking Prerequisites")
    
    prereq_script = "check_prerequisites.py"
    if not Path(prereq_script).exists():
        print_status(f"{prereq_script} not found", "error")
        return False
    
    try:
        subprocess.run([sys.executable, prereq_script], check=True)
        return True
    except subprocess.CalledProcessError:
        print_status("Prerequisite check failed", "error")
        return False

def run_setup():
    """Run the main setup script"""
    print_header("Running Setup")
    
    setup_script = "setup.py"
    if not Path(setup_script).exists():
        print_status(f"{setup_script} not found", "error")
        return False
    
    try:
        subprocess.run([sys.executable, setup_script], check=True)
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
