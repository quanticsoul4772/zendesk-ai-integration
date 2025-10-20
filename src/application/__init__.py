"""
Application Package

This package contains the application layer for the Zendesk AI Integration application.
It includes service implementations, use cases, and DTOs.
"""

from src.application.dtos.analysis_dto import AnalysisDTO
from src.application.dtos.report_dto import ReportDTO

# Import DTOs for easier access
from src.application.dtos.ticket_dto import TicketDTO
from src.application.services.reporting_service import ReportingServiceImpl
from src.application.services.scheduler_service import SchedulerServiceImpl

# Import service implementations for easier access
from src.application.services.ticket_analysis_service import TicketAnalysisServiceImpl
from src.application.services.webhook_service import WebhookServiceImpl

# Import use cases for easier access
from src.application.use_cases.analyze_ticket_use_case import AnalyzeTicketUseCase
from src.application.use_cases.generate_report_use_case import GenerateReportUseCase

__all__ = [
    # Service implementations
    'TicketAnalysisServiceImpl',
    'ReportingServiceImpl',
    'WebhookServiceImpl',
    'SchedulerServiceImpl',

    # Use cases
    'AnalyzeTicketUseCase',
    'GenerateReportUseCase',

    # DTOs
    'TicketDTO',
    'AnalysisDTO',
    'ReportDTO'
]
