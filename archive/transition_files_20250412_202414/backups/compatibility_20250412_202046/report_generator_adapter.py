"""
Report Generator Adapter

This module provides adapter functions that present the legacy report_generator.py interfaces
but use the new ReportingService implementation internally.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from src.application.services.reporting_service import ReportingService
from src.presentation.reporters.sentiment_reporter import SentimentReporterImpl
from src.presentation.reporters.hardware_reporter import HardwareReporterImpl
from src.presentation.reporters.pending_reporter import PendingReporterImpl
from src.infrastructure.compatibility.zendesk_adapter import ZendeskClientAdapter
from src.infrastructure.compatibility.ai_analyzer_adapter import AIAnalyzerAdapter
from src.infrastructure.compatibility.db_repository_adapter import DBRepositoryAdapter
from src.infrastructure.compatibility.reporter_adapter import (
    SentimentReporterAdapter,
    HardwareReporterAdapter,
    PendingReporterAdapter
)

# Set up logging
logger = logging.getLogger(__name__)

# Create a concrete implementation of ReportingService
class ReportingServiceImpl(ReportingService):
    """
    Concrete implementation of ReportingService interface.
    
    This class implements the abstract methods of ReportingService.
    """
    
    def __init__(self):
        """
        Initialize the reporting service.
        """
        logger.debug("ReportingServiceImpl initialized")
        self.sentiment_reporter = SentimentReporterImpl()
        self.hardware_reporter = HardwareReporterImpl()
        self.pending_reporter = PendingReporterImpl()
    
    def generate_sentiment_report(self, time_period="week", view_id=None):
        """
        Generate a sentiment analysis report.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            view_id: Optional view ID to filter by
            
        Returns:
            Report text
        """
        days = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365
        }.get(time_period, 30)
        
        return self.sentiment_reporter.generate_report(
            view_id_or_name=view_id,
            days=days,
            enhanced=False,
            format_type="text"
        )
    
    def generate_hardware_report(self, view_id=None, limit=None):
        """
        Generate a hardware component report.
        
        Args:
            view_id: Optional view ID to filter by
            limit: Maximum number of tickets to include
            
        Returns:
            Report text
        """
        return self.hardware_reporter.generate_report(
            view_id_or_name=view_id,
            days=30,
            format_type="text"
        )
    
    def generate_pending_report(self, view_name, limit=None):
        """
        Generate a pending ticket report.
        
        Args:
            view_name: Name of the pending view
            limit: Maximum number of tickets to include
            
        Returns:
            Report text
        """
        return self.pending_reporter.generate_report(
            view_id_or_name=view_name,
            format_type="text"
        )
    
    def generate_multi_view_report(self, view_ids, report_type, limit=None):
        """
        Generate a multi-view report.
        
        Args:
            view_ids: List of view IDs to include
            report_type: Type of report ('sentiment', 'hardware', 'pending')
            limit: Maximum number of tickets per view
            
        Returns:
            Report text
        """
        if report_type == "sentiment":
            reporter = self.sentiment_reporter
        elif report_type == "hardware":
            reporter = self.hardware_reporter
        elif report_type == "pending":
            reporter = self.pending_reporter
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return "Multi-view report not implemented yet"
    
    def save_report(self, report, filename=None):
        """
        Save a report to a file.
        
        Args:
            report: Report text
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to the saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        return filename

# Global instance of ReportingService
_reporting_service = None

def get_reporting_service():
    """
    Get or create a ReportingService instance.
    
    Returns:
        ReportingService instance
    """
    global _reporting_service
    
    if _reporting_service is None:
        _reporting_service = ReportingServiceImpl()
        logger.debug("Created new ReportingServiceImpl instance")
    
    return _reporting_service

def generate_summary_report(zendesk_client, ai_analyzer, db_repository, view_id=None, days=30, format_type="text"):
    """
    Generate a summary report with sentiment analysis.
    
    Args:
        zendesk_client: ZendeskClient instance
        ai_analyzer: AIAnalyzer instance
        db_repository: DBRepository instance
        view_id: Optional view ID
        days: Number of days to include in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Report content
    """
    logger.debug(f"generate_summary_report called for view {view_id}, days={days}")
    
    reporting_service = get_reporting_service()
    
    # Use a dedicated sentiment reporter
    sentiment_reporter = SentimentReporterAdapter()
    sentiment_reporter.set_services(zendesk_client, ai_analyzer, db_repository)
    
    return sentiment_reporter.generate_report(
        view=view_id,
        days=days,
        enhanced=False,
        format_type=format_type
    )

def generate_enhanced_summary_report(zendesk_client, ai_analyzer, db_repository, view_id=None, days=30, format_type="text"):
    """
    Generate an enhanced summary report with detailed sentiment analysis.
    
    Args:
        zendesk_client: ZendeskClient instance
        ai_analyzer: AIAnalyzer instance
        db_repository: DBRepository instance
        view_id: Optional view ID
        days: Number of days to include in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Report content
    """
    logger.debug(f"generate_enhanced_summary_report called for view {view_id}, days={days}")
    
    reporting_service = get_reporting_service()
    
    # Use a dedicated sentiment reporter
    sentiment_reporter = SentimentReporterAdapter()
    sentiment_reporter.set_services(zendesk_client, ai_analyzer, db_repository)
    
    return sentiment_reporter.generate_report(
        view=view_id,
        days=days,
        enhanced=True,
        format_type=format_type
    )

def generate_hardware_report(zendesk_client, ai_analyzer, db_repository, view_id=None, days=30, format_type="text"):
    """
    Generate a hardware components report.
    
    Args:
        zendesk_client: ZendeskClient instance
        ai_analyzer: AIAnalyzer instance
        db_repository: DBRepository instance
        view_id: Optional view ID
        days: Number of days to include in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Report content
    """
    logger.debug(f"generate_hardware_report called for view {view_id}, days={days}")
    
    reporting_service = get_reporting_service()
    
    # Use a dedicated hardware reporter
    hardware_reporter = HardwareReporterAdapter()
    hardware_reporter.set_services(zendesk_client, ai_analyzer, db_repository)
    
    return hardware_reporter.generate_report(
        view=view_id,
        days=days,
        format_type=format_type
    )

def generate_pending_report(zendesk_client, ai_analyzer, db_repository, view_id=None, format_type="text"):
    """
    Generate a pending tickets report.
    
    Args:
        zendesk_client: ZendeskClient instance
        ai_analyzer: AIAnalyzer instance
        db_repository: DBRepository instance
        view_id: Optional view ID
        format_type: Output format (text, html, etc.)
        
    Returns:
        Report content
    """
    logger.debug(f"generate_pending_report called for view {view_id}")
    
    reporting_service = get_reporting_service()
    
    # Use a dedicated pending reporter
    pending_reporter = PendingReporterAdapter()
    pending_reporter.set_services(zendesk_client, ai_analyzer, db_repository)
    
    return pending_reporter.generate_report(
        view=view_id,
        format_type=format_type
    )

def get_summary_report_filename(view_id=None, days=30, format_type="text"):
    """
    Get a filename for the summary report.
    
    Args:
        view_id: Optional view ID
        days: Number of days included in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Filename
    """
    logger.debug(f"get_summary_report_filename called for view {view_id}")
    
    reporting_service = get_reporting_service()
    
    # Create a temporary reporter to get the filename
    reporter = SentimentReporterAdapter()
    
    return reporter.get_report_filename(
        view=view_id,
        days=days,
        enhanced=False,
        format_type=format_type
    )

def get_enhanced_summary_report_filename(view_id=None, days=30, format_type="text"):
    """
    Get a filename for the enhanced summary report.
    
    Args:
        view_id: Optional view ID
        days: Number of days included in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Filename
    """
    logger.debug(f"get_enhanced_summary_report_filename called for view {view_id}")
    
    reporting_service = get_reporting_service()
    
    # Create a temporary reporter to get the filename
    reporter = SentimentReporterAdapter()
    
    return reporter.get_report_filename(
        view=view_id,
        days=days,
        enhanced=True,
        format_type=format_type
    )

def get_hardware_report_filename(view_id=None, days=30, format_type="text"):
    """
    Get a filename for the hardware report.
    
    Args:
        view_id: Optional view ID
        days: Number of days included in the report
        format_type: Output format (text, html, etc.)
        
    Returns:
        Filename
    """
    logger.debug(f"get_hardware_report_filename called for view {view_id}")
    
    reporting_service = get_reporting_service()
    
    # Create a temporary reporter to get the filename
    reporter = HardwareReporterAdapter()
    
    return reporter.get_report_filename(
        view=view_id,
        days=days,
        format_type=format_type
    )

def get_pending_report_filename(view_id=None, format_type="text"):
    """
    Get a filename for the pending report.
    
    Args:
        view_id: Optional view ID
        format_type: Output format (text, html, etc.)
        
    Returns:
        Filename
    """
    logger.debug(f"get_pending_report_filename called for view {view_id}")
    
    reporting_service = get_reporting_service()
    
    # Create a temporary reporter to get the filename
    reporter = PendingReporterAdapter()
    
    return reporter.get_report_filename(
        view=view_id,
        format_type=format_type
    )
