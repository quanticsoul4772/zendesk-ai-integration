#!/usr/bin/env python3
"""
Test script for the analyze ticket command
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Test the analyze ticket command with a specific view ID"""
    try:
        # Import necessary command handler code
        from src.presentation.cli.command_handler import CommandHandler
        
        # Create command handler (this initializes all dependencies)
        command_handler = CommandHandler()
        
        # Execute analyzeticket command with view-id option
        result = command_handler.handle_command(["analyzeticket", "--view-id", "18002932412055", "--limit", "3"])
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
