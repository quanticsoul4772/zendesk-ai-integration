#!/usr/bin/env python3
"""
Helper script to load environment variables and run the main program.
This ensures that environment variables from .env are properly loaded.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    """Load environment variables and run the main program."""
    # Load environment variables from .env file
    env_file = ".env.fixed" if os.path.exists(".env.fixed") else ".env"
    load_dotenv(env_file)
    
    print(f"Loaded environment variables from {env_file}")
    
    # Verify critical environment variables
    required_vars = [
        "ZENDESK_EMAIL", 
        "ZENDESK_API_TOKEN", 
        "ZENDESK_SUBDOMAIN"
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            print(f"ERROR: Required environment variable {var} not found.")
            return 1
        else:
            print(f"Found environment variable: {var}")
    
    # Get command line arguments (excluding script name)
    cmd_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Construct command to run the main program
    cmd = [sys.executable, "-m", "src.main"] + cmd_args
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the main program with the loaded environment variables
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
