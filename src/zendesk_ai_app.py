#!/usr/bin/env python3

"""
Zendesk AI Integration Application

This module provides the main entry point for the Zendesk AI Integration application.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from typing import Dict, Any, List, Optional

import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.utils.service_provider import ServiceProvider
from src.presentation.cli.command_handler import CommandHandler
from src.presentation.cli.commands import (
    AnalyzeTicketCommand,
    GenerateReportCommand,
    ListViewsCommand,
    InteractiveCommand,
    ScheduleCommand,
    WebhookCommand
)

# Command classes to register
COMMAND_CLASSES = [
    AnalyzeTicketCommand,
    GenerateReportCommand,
    ListViewsCommand,
    InteractiveCommand,
    ScheduleCommand,
    WebhookCommand
]


def configure_logging(level_name: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        level_name: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('zendesk_ai.log')
        ]
    )
    
    # Set lower log level for some noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("zenpy").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {level_name}")


def parse_args(args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Dictionary of parsed arguments
    """
    parser = argparse.ArgumentParser(description="Zendesk AI Integration")
    
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    
    # Parse known arguments to get the config file and log level
    parsed_args, remaining = parser.parse_known_args(args)
    
    # Configure logging with the specified level
    configure_logging(parsed_args.log_level)
    
    # Return the parsed arguments
    return vars(parsed_args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the application.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        parsed_args = parse_args(args)
        
        # Create service provider
        config_file = parsed_args.get("config")
        service_provider = ServiceProvider(config_file)
        
        # Create command handler
        command_handler = CommandHandler(service_provider)
        
        # Register commands
        command_handler.register_commands(COMMAND_CLASSES)
        
        # Run the command handler
        result = command_handler.run(args)
        
        # Return exit code based on success
        return 0 if result.get("success", False) else 1
    except Exception as e:
        logging.exception(f"Unhandled exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
