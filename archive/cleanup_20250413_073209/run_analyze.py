#!/usr/bin/env python3
"""
Script to run the analyzeticket command
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the analyzeticket command with a view ID"""
    
    # Command to run
    cmd = [
        "python", "-m", "src.main", 
        "analyzeticket", 
        "--view-id", "15990417987223", 
        "--limit", "5"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print("\nSTDOUT:")
    print(result.stdout)
    
    # Print errors if any
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    # Return exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
