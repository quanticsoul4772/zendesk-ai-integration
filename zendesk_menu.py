#!/usr/bin/env python3
"""
Launcher script for the Zendesk AI Integration interactive menu.

This script provides a convenient way to launch the interactive menu
without having to remember the command-line arguments.
"""

import sys
import os
import subprocess
import platform

def main():
    """Launch the Zendesk AI Integration interactive menu."""
    # Get the path to the Python executable
    python_executable = sys.executable
    
    # Build the command to run the application in interactive mode
    command = [python_executable, "-m", "src.zendesk_ai_app", "--mode", "interactive"]
    
    # Print a message to the user
    print("Launching Zendesk AI Integration interactive menu...")
    print(f"Using Python executable: {python_executable}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print("=" * 60)
    
    try:
        # Run the command
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Zendesk AI Integration: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
