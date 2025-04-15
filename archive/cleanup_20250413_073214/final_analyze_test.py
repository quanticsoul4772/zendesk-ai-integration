#!/usr/bin/env python3
"""
Final test for the analyze ticket command with our fixes
"""

import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the analyze command with different options"""
    
    # Test script
    print("\n=== Testing custom fields handling with test_analyze_view_fix.py ===")
    subprocess.run(["python", "test_analyze_view_fix.py"], check=False)
    
    # Test actual command
    print("\n=== Testing analyzeticket command with view ===")
    
    # Command to run
    cmd = [
        "python", "-m", "src.main", 
        "analyzeticket", 
        "--view-id", "29753646016023", 
        "--limit", "2"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print("\nSTDOUT:")
    print(result.stdout)
    
    # Print errors if any
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
