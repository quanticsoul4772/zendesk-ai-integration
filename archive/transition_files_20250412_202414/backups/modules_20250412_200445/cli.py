"""
CLI Module

This module provides backward compatibility for the CLI module.
"""

import logging
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


class CommandLineInterface:
    """
    Legacy command line interface class.
    
    This is a compatibility stub that delegates to the new CLI implementation.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        logger.debug("CommandLineInterface initialized (compatibility mode)")
        
        # Compatibility attributes
        self.commands = {}
        self.descriptions = {}
    
    def register_command(self, name, function, description=""):
        """
        Register a command.
        
        Args:
            name: Command name
            function: Command function
            description: Command description
        """
        logger.debug(f"Registering command {name} (compatibility mode)")
        self.commands[name] = function
        self.descriptions[name] = description
    
    def run(self, args=None):
        """
        Run the CLI.
        
        Args:
            args: Command line arguments
        """
        logger.debug("Running CLI (compatibility mode)")
        
        # Import here to avoid circular imports
        from src.presentation.cli.command_handler import CommandHandler
        
        handler = CommandHandler()
        return handler.handle_command(args)
