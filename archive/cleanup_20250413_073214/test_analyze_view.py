#!/usr/bin/env python3
"""
Test script for the analyzeticket command with a view ID
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the analyzeticket command with a view ID"""
    try:
        # Import necessary modules
        from src.presentation.cli.command_handler import CommandHandler
        
        # Create command handler (this initializes all dependencies)
        command_handler = CommandHandler()
        
        # Set up command line arguments
        args = ["analyzeticket", "--view-id", "18002932412055", "--limit", "3"]
        
        # Execute command
        print(f"Executing command: python -m src.main {' '.join(args)}")
        result = command_handler.handle_command(args)
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
