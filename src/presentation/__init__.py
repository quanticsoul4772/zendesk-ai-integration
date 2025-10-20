"""
Presentation Package

This package contains the presentation layer for the Zendesk AI Integration application.
It includes CLI and webhook interfaces for interacting with the application.
"""

from src.presentation.cli.command import Command
from src.presentation.cli.command_handler import CommandHandler

# Import command classes
from src.presentation.cli.commands import (
    AnalyzeTicketCommand,
    GenerateReportCommand,
    InteractiveCommand,
    ListViewsCommand,
    ScheduleCommand,
    WebhookCommand,
)
from src.presentation.cli.response_formatter import ResponseFormatter
from src.presentation.reporters.hardware_reporter import HardwareReporterImpl
from src.presentation.reporters.pending_reporter import PendingReporterImpl
from src.presentation.reporters.sentiment_reporter import SentimentReporterImpl
from src.presentation.webhook.webhook_handler import WebhookHandler

__all__ = [
    # CLI components
    'CommandHandler',
    'Command',
    'ResponseFormatter',

    # Webhook components
    'WebhookHandler',

    # Reporter implementations
    'SentimentReporterImpl',
    'HardwareReporterImpl',
    'PendingReporterImpl',

    # Command classes
    'AnalyzeTicketCommand',
    'GenerateReportCommand',
    'ListViewsCommand',
    'InteractiveCommand',
    'ScheduleCommand',
    'WebhookCommand'
]
