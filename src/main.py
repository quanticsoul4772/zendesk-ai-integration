"""
Main Application Entry Point

This module provides the main entry point for the Zendesk AI Integration application.
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any, List, Optional, Type
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Add src directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.infrastructure.service_provider import ServiceProvider
from src.presentation.cli.command import Command
from src.presentation.cli.command_handler import CommandHandler
from src.presentation.cli.commands.analyze_ticket_command import AnalyzeTicketCommand
from src.presentation.cli.commands.generate_report_command import GenerateReportCommand
from src.presentation.cli.commands.list_views_command import ListViewsCommand
from src.presentation.cli.commands.webhook_command import WebhookCommand
from src.presentation.cli.commands.schedule_command import ScheduleCommand
from src.presentation.cli.commands.interactive_command import InteractiveCommand


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    # Set up logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Configure logging
    logging_config = {
        "level": numeric_level,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }

    # Add file handler if log file specified
    if log_file:
        logging_config["filename"] = log_file

    # Apply configuration
    logging.basicConfig(**logging_config)


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code
    """
    # Parse command-line arguments for logging configuration
    parser = argparse.ArgumentParser(description="Zendesk AI Integration")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file"
    )
    parser.add_argument(
        "--config-file",
        help="Path to configuration file"
    )

    # Parse arguments without consuming them (so they're available to commands)
    args, _ = parser.parse_known_args()

    # Set up logging
    setup_logging(args.log_level, args.log_file)

    try:
        # Create service provider (not used directly by CommandHandler)
        service_provider = ServiceProvider(args.config_file)

        # Create command handler
        command_handler = CommandHandler()

        # Commands are already registered in the CommandHandler's __init__ method
        # So we don't need to register them again here
        # command_classes: List[Type[Command]] = [
        #     AnalyzeTicketCommand,
        #     GenerateReportCommand,
        #     ListViewsCommand,
        #     WebhookCommand,
        #     ScheduleCommand,
        #     InteractiveCommand
        # ]
        # command_handler.register_commands(command_classes)

        # Run the command handler
        result = command_handler.handle_command()

        # Return exit code (handle_command returns the exit code directly)
        return result
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        logging.exception(f"Unhandled exception: {e}")
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
