#!/usr/bin/env python3

"""
Entry point script for running the Zendesk AI Integration application.
This script configures the Python path properly to ensure all modules can be imported.
"""

import os
import sys
import logging
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Verify environment variables are loaded
    if not os.getenv("ZENDESK_EMAIL") or not os.getenv("ZENDESK_API_TOKEN") or not os.getenv("ZENDESK_SUBDOMAIN"):
        print("Warning: Zendesk credentials not loaded from .env file")
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to the Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('zendesk_ai.log')
        ]
    )
    
    # Import and run the main function from zendesk_ai_app
    from src.zendesk_ai_app import main
    
    # Run the application with the command-line arguments
    return main()

if __name__ == "__main__":
    sys.exit(main())
