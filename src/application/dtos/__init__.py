"""
DTOs Package

This package contains Data Transfer Objects (DTOs) for the Zendesk AI Integration application.
"""

from src.application.dtos.analysis_dto import AnalysisDTO, SentimentAnalysisDTO
from src.application.dtos.report_dto import ReportDTO
from src.application.dtos.ticket_dto import TicketDTO

__all__ = [
    'TicketDTO',
    'AnalysisDTO',
    'SentimentAnalysisDTO',
    'ReportDTO'
]
