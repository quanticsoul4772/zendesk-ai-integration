"""
Use Cases Package

This package contains use cases for the Zendesk AI Integration application.
"""

from src.application.use_cases.analyze_ticket_use_case import AnalyzeTicketUseCase
from src.application.use_cases.generate_report_use_case import GenerateReportUseCase

__all__ = [
    'AnalyzeTicketUseCase',
    'GenerateReportUseCase'
]
