#!/usr/bin/env python3

"""
Zendesk AI Integration CLI

This script provides a command-line interface to run the Zendesk AI Integration
application using the clean architecture implementation.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
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
logger = logging.getLogger(__name__)

def run_clean_architecture_cli():
    """Run the application using the clean architecture implementation."""
    logger.info("Using clean architecture implementation")
    
    try:
        # Import command handler
        from src.presentation.cli.command_handler import CommandHandler
        
        # Create command handler
        command_handler = CommandHandler()
        
        # Parse arguments and execute command
        return command_handler.handle_command()
        
    except Exception as e:
        logger.exception(f"Error in CLI: {e}")
        return 1

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env loading")
    
    # Execute the CLI
    sys.exit(run_clean_architecture_cli())
