"""
Command Handler Implementation

This module defines the CommandHandler class that manages command registration
and execution in the CLI interface.
"""

import argparse
import logging
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Type

from src.presentation.cli.command import Command

# Import commands
from src.presentation.cli.commands.analyze_ticket_command import AnalyzeTicketCommand
from src.presentation.cli.commands.generate_report_command import GenerateReportCommand
from src.presentation.cli.commands.interactive_command import InteractiveCommand
from src.presentation.cli.commands.list_views_command import ListViewsCommand
from src.presentation.cli.commands.schedule_command import ScheduleCommand
from src.presentation.cli.commands.webhook_command import WebhookCommand
from src.presentation.cli.response_formatter import ResponseFormatter

# Set up logging
logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Handles registration and execution of CLI commands.

    This class implements the command pattern by registering commands
    and executing them based on user input.
    """

    def __init__(self):
        """Initialize the command handler."""
        from src.infrastructure.utils.dependency_injection import DependencyContainer

        # Create dependency container
        self.dependency_container = DependencyContainer()
        self._initialize_services()

        # Initialize command parser
        self.parser = argparse.ArgumentParser(
            description="Zendesk AI Integration",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python zendesk_cli.py views
  python zendesk_cli.py analyze ticket --ticket-id 12345
  python zendesk_cli.py analyze view --view-id 67890
  python zendesk_cli.py report --type sentiment --days 7
  python zendesk_cli.py interactive
  python zendesk_cli.py webhook --host 0.0.0.0 --port 5000
"""
        )

        # Add global options
        self._add_global_options()

        # Create subparsers for commands
        self.subparsers = self.parser.add_subparsers(dest="command", help="Command to execute")
        self.commands: Dict[str, Type[Command]] = {}
        self.response_formatter = ResponseFormatter()

        # Register all commands
        self._register_all_commands()

    def _add_global_options(self):
        """Add global options to the parser."""
        self.parser.add_argument(
            "--config",
            help="Path to configuration file"
        )

        self.parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Logging level"
        )

    def _initialize_services(self):
        """Initialize all required services."""
        try:
            # Initialize repositories
            from src.application.services.reporting_service import ReportingServiceImpl
            from src.application.services.scheduler_service import SchedulerServiceImpl
            from src.application.services.ticket_analysis_service import (
                TicketAnalysisServiceImpl,
            )
            from src.application.services.webhook_service import WebhookServiceImpl

            # Initialize use cases
            from src.application.use_cases.analyze_ticket_use_case import (
                AnalyzeTicketUseCase,
            )
            from src.application.use_cases.generate_report_use_case import (
                GenerateReportUseCase,
            )

            # Initialize services
            from src.infrastructure.external_services.claude_service import (
                ClaudeService,
            )
            from src.infrastructure.external_services.openai_service import (
                OpenAIService,
            )
            from src.infrastructure.repositories.mongodb_repository import (
                MongoDBRepository,
            )
            from src.infrastructure.repositories.zendesk_repository import (
                ZendeskRepository,
            )
            from src.presentation.reporters.hardware_reporter import (
                HardwareReporterImpl,
            )
            from src.presentation.reporters.pending_reporter import PendingReporterImpl

            # Initialize reporters
            from src.presentation.reporters.sentiment_reporter import (
                SentimentReporterImpl,
            )

            # Create instances and register with dependency container
            ticket_repo = ZendeskRepository()
            analysis_repo = MongoDBRepository()

            claude_service = ClaudeService()
            openai_service = OpenAIService()

            ticket_analysis_service = TicketAnalysisServiceImpl(ticket_repo, analysis_repo, openai_service)
            webhook_service = WebhookServiceImpl(ticket_repo, analysis_repo, ticket_analysis_service)
            # Create reporters
            sentiment_reporter = SentimentReporterImpl()
            hardware_reporter = HardwareReporterImpl()
            pending_reporter = PendingReporterImpl()

            reporting_service = ReportingServiceImpl(
                ticket_repository=ticket_repo,
                analysis_repository=analysis_repo,
                view_repository=ticket_repo,  # ZendeskRepository also implements ViewRepository
                sentiment_reporter=sentiment_reporter,
                hardware_reporter=hardware_reporter,
                pending_reporter=pending_reporter,
                ticket_analysis_service=ticket_analysis_service
            )
            scheduler_service = SchedulerServiceImpl()

            analyze_ticket_use_case = AnalyzeTicketUseCase(ticket_repo, ticket_analysis_service)
            generate_report_use_case = GenerateReportUseCase(reporting_service)

            # Register all services with the dependency container
            from src.domain.interfaces.ai_service_interfaces import (
                AIService,
                EnhancedAIService,
            )
            from src.domain.interfaces.reporter_interfaces import (
                HardwareReporter,
                PendingReporter,
                SentimentReporter,
            )
            from src.domain.interfaces.repository_interfaces import (
                AnalysisRepository,
                TicketRepository,
                ViewRepository,
            )
            from src.domain.interfaces.service_interfaces import (
                ReportingService,
                SchedulerService,
                TicketAnalysisService,
                WebhookService,
            )

            # Register repositories and services by interface
            self.dependency_container.register_instance(TicketRepository, ticket_repo)
            self.dependency_container.register_instance(AnalysisRepository, analysis_repo)
            self.dependency_container.register_instance(ViewRepository, ticket_repo)  # ZendeskRepository implements ViewRepository too

            # Register AI services
            self.dependency_container.register_instance(AIService, claude_service, "claude")
            self.dependency_container.register_instance(AIService, openai_service, "openai")
            self.dependency_container.register_instance(EnhancedAIService, claude_service)

            # Register application services
            self.dependency_container.register_instance(TicketAnalysisService, ticket_analysis_service)
            self.dependency_container.register_instance(WebhookService, webhook_service)
            self.dependency_container.register_instance(ReportingService, reporting_service)
            self.dependency_container.register_instance(SchedulerService, scheduler_service)

            # Register reporters
            self.dependency_container.register_instance(SentimentReporter, sentiment_reporter)
            self.dependency_container.register_instance(HardwareReporter, hardware_reporter)
            self.dependency_container.register_instance(PendingReporter, pending_reporter)

            # Register use cases by name (not interfaces)
            self.dependency_container.register_instance("analyze_ticket_use_case", analyze_ticket_use_case)
            self.dependency_container.register_instance("generate_report_use_case", generate_report_use_case)

            logger.debug("Services initialized successfully")

        except Exception as e:
            logger.exception(f"Error initializing services: {e}")
            raise

    def _register_all_commands(self):
        """Register all available commands."""
        self.register_commands([
            AnalyzeTicketCommand,
            GenerateReportCommand,
            ListViewsCommand,
            InteractiveCommand,
            ScheduleCommand,
            WebhookCommand
        ])

    def register_command(self, command_class: Type[Command]) -> None:
        """
        Register a command with the handler.

        Args:
            command_class: Command class to register
        """
        try:
            # Create a temporary instance to access properties
            command_instance = command_class(self.dependency_container)

            # Get the name
            name = command_instance.name

            # Get the description
            description = command_instance.description

            subparser = self.subparsers.add_parser(name, help=description)

            # Add command-specific arguments
            command_instance.add_arguments(subparser)

            # Register the command
            self.commands[name] = command_class

            logger.debug(f"Registered command: {name}")

        except Exception as e:
            logger.exception(f"Error registering command {command_class.__name__}: {e}")
            raise

    def register_commands(self, command_classes: List[Type[Command]]) -> None:
        """
        Register multiple commands with the handler.

        Args:
            command_classes: List of command classes to register
        """
        for command_class in command_classes:
            self.register_command(command_class)

    def _configure_logging(self, log_level: str) -> None:
        """
        Configure logging based on the specified log level.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {log_level}")

        # Configure root logger
        logging.getLogger().setLevel(numeric_level)

        # Configure our logger
        logger.setLevel(numeric_level)

        logger.debug(f"Logging configured with level: {log_level}")

    def handle_command(self, args: Optional[List[str]] = None) -> int:
        """
        Parse arguments and execute the appropriate command.

        Args:
            args: Command-line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Parse arguments
            parsed_args = self.parser.parse_args(args)

            # Configure logging based on specified log level
            if hasattr(parsed_args, 'log_level'):
                self._configure_logging(parsed_args.log_level)

            # Load configuration if specified
            if hasattr(parsed_args, 'config') and parsed_args.config:
                self._load_configuration(parsed_args.config)

            # Show help if no command specified
            if not parsed_args.command:
                self.parser.print_help()
                return 1

            # Convert namespace to dictionary
            args_dict = vars(parsed_args)

            # Get the command class
            command_class = self.commands.get(parsed_args.command)
            if not command_class:
                print(f"Error: Command not found: {parsed_args.command}")
                return 1

            # Create and execute the command
            command = command_class(self.dependency_container)
            logger.info(f"Executing command: {parsed_args.command}")
            result = command.execute(args_dict)

            # Check result and determine exit code
            if isinstance(result, dict) and 'success' in result:
                return 0 if result['success'] else 1
            return 0

        except KeyboardInterrupt:
            logger.info("Operation interrupted by user")
            print("\nOperation interrupted by user")
            return 1

        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            print(f"Error: {e}")
            return 1

    def _load_configuration(self, config_path: str) -> None:
        """
        Load configuration from a file.

        Args:
            config_path: Path to the configuration file
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.info(f"Loading configuration from {config_path}")

        # Implementation will depend on the configuration format
        # For now, just log that we'd load it
        logger.info(f"Configuration loading not yet implemented")


if __name__ == "__main__":
    # When run directly, display available commands
    handler = CommandHandler()

    # Show help
    handler.parser.parse_args(['-h'])
