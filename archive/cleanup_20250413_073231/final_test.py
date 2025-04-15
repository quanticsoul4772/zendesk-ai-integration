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
    """Run the analyzeticket command to test our fixes"""
    
    # Command to run
    cmd = [
        "python", "-m", "src.main", 
        "analyzeticket", 
        "--view-id", "29753646016023", 
        "--limit", "2"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
