"""
CLI Package

This package contains the command-line interface for the Zendesk AI Integration application.
It uses the command pattern to handle different types of commands.
"""

from src.presentation.cli.command_handler import CommandHandler
from src.presentation.cli.commands import *

__all__ = [
    'CommandHandler',
    'AnalyzeTicketCommand',
    'GenerateReportCommand',
    'ListViewsCommand',
    'WebhookCommand',
    'ScheduleCommand',
    'InteractiveCommand'
]
