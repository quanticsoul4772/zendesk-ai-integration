"""
Reporter Adapter

This module provides adapters that present the legacy reporter interfaces
but use the new reporter implementations internally.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from src.domain.interfaces.reporter_interfaces import (
    SentimentReporter,
    HardwareReporter,
    PendingReporter
)
from src.presentation.reporters.sentiment_reporter import SentimentReporterImpl
from src.presentation.reporters.hardware_reporter import HardwareReporterImpl
from src.presentation.reporters.pending_reporter import PendingReporterImpl

# Set up logging
logger = logging.getLogger(__name__)


class SentimentReporterAdapter:
    """
    Adapter that presents a legacy SentimentReporter interface but uses the
    new SentimentReporterImpl internally.
    """
    
    def __init__(self, reporter=None):
        """
        Initialize the adapter.
        
        Args:
            reporter: Optional SentimentReporterImpl instance
        """
        self._reporter = reporter or SentimentReporterImpl()
        
        # Legacy compatibility attributes
        self.zendesk_client = None
        self.ai_analyzer = None
        self.db_repository = None
        
        logger.debug("SentimentReporterAdapter initialized")
    
    def set_services(self, zendesk_client, ai_analyzer, db_repository):
        """
        Set services used by the reporter.
        
        Args:
            zendesk_client: Zendesk client instance
            ai_analyzer: AI analyzer instance
            db_repository: DB repository instance
        """
        logger.debug("SentimentReporterAdapter.set_services called")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Update the reporter with repositories if necessary
        if hasattr(self._reporter, 'set_repositories'):
            self._reporter.set_repositories(
                ticket_repository=zendesk_client,
                analysis_repository=db_repository
            )
    
    def generate_report(self, view=None, days=30, enhanced=False, format_type="text"):
        """
        Generate a sentiment analysis report.
        
        Args:
            view: View ID or name (optional)
            days: Number of days to include
            enhanced: Whether to use enhanced sentiment analysis
            format_type: Output format (text, html, etc.)
            
        Returns:
            Report content
        """
        logger.debug(f"SentimentReporterAdapter.generate_report called for view {view}, days={days}, enhanced={enhanced}")
        
        return self._reporter.generate_report(
            view_id_or_name=view,
            days=days,
            enhanced=enhanced,
            format_type=format_type
        )
    
    def get_report_filename(self, view=None, days=30, enhanced=False, format_type="text"):
        """
        Get a filename for the report.
        
        Args:
            view: View ID or name (optional)
            days: Number of days to include
            enhanced: Whether to use enhanced sentiment analysis
            format_type: Output format (text, html, etc.)
            
        Returns:
            Filename
        """
        logger.debug(f"SentimentReporterAdapter.get_report_filename called for view {view}")
        
        return self._reporter.get_report_filename(
            view_id_or_name=view,
            days=days,
            enhanced=enhanced,
            format_type=format_type
        )
    
    def analyze_view(self, view, days=30, enhanced=False):
        """
        Analyze tickets in a view.
        
        Args:
            view: View ID or name
            days: Number of days to include
            enhanced: Whether to use enhanced sentiment analysis
            
        Returns:
            Analysis results
        """
        logger.debug(f"SentimentReporterAdapter.analyze_view called for view {view}, days={days}")
        
        return self._reporter.analyze_view(
            view_id_or_name=view,
            days=days,
            enhanced=enhanced
        )


class HardwareReporterAdapter:
    """
    Adapter that presents a legacy HardwareReporter interface but uses the
    new HardwareReporterImpl internally.
    """
    
    def __init__(self, reporter=None):
        """
        Initialize the adapter.
        
        Args:
            reporter: Optional HardwareReporterImpl instance
        """
        self._reporter = reporter or HardwareReporterImpl()
        
        # Legacy compatibility attributes
        self.zendesk_client = None
        self.ai_analyzer = None
        self.db_repository = None
        
        logger.debug("HardwareReporterAdapter initialized")
    
    def set_services(self, zendesk_client, ai_analyzer, db_repository):
        """
        Set services used by the reporter.
        
        Args:
            zendesk_client: Zendesk client instance
            ai_analyzer: AI analyzer instance
            db_repository: DB repository instance
        """
        logger.debug("HardwareReporterAdapter.set_services called")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Update the reporter with repositories if necessary
        if hasattr(self._reporter, 'set_repositories'):
            self._reporter.set_repositories(
                ticket_repository=zendesk_client,
                analysis_repository=db_repository
            )
    
    def generate_report(self, view=None, days=30, format_type="text"):
        """
        Generate a hardware components report.
        
        Args:
            view: View ID or name (optional)
            days: Number of days to include
            format_type: Output format (text, html, etc.)
            
        Returns:
            Report content
        """
        logger.debug(f"HardwareReporterAdapter.generate_report called for view {view}, days={days}")
        
        return self._reporter.generate_report(
            view_id_or_name=view,
            days=days,
            format_type=format_type
        )
    
    def get_report_filename(self, view=None, days=30, format_type="text"):
        """
        Get a filename for the report.
        
        Args:
            view: View ID or name (optional)
            days: Number of days to include
            format_type: Output format (text, html, etc.)
            
        Returns:
            Filename
        """
        logger.debug(f"HardwareReporterAdapter.get_report_filename called for view {view}")
        
        return self._reporter.get_report_filename(
            view_id_or_name=view,
            days=days,
            format_type=format_type
        )
    
    def analyze_view(self, view, days=30):
        """
        Analyze tickets in a view.
        
        Args:
            view: View ID or name
            days: Number of days to include
            
        Returns:
            Analysis results
        """
        logger.debug(f"HardwareReporterAdapter.analyze_view called for view {view}, days={days}")
        
        return self._reporter.analyze_view(
            view_id_or_name=view,
            days=days
        )


class PendingReporterAdapter:
    """
    Adapter that presents a legacy PendingReporter interface but uses the
    new PendingReporterImpl internally.
    """
    
    def __init__(self, reporter=None):
        """
        Initialize the adapter.
        
        Args:
            reporter: Optional PendingReporterImpl instance
        """
        self._reporter = reporter or PendingReporterImpl()
        
        # Legacy compatibility attributes
        self.zendesk_client = None
        self.ai_analyzer = None
        self.db_repository = None
        
        logger.debug("PendingReporterAdapter initialized")
    
    def set_services(self, zendesk_client, ai_analyzer, db_repository):
        """
        Set services used by the reporter.
        
        Args:
            zendesk_client: Zendesk client instance
            ai_analyzer: AI analyzer instance
            db_repository: DB repository instance
        """
        logger.debug("PendingReporterAdapter.set_services called")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Update the reporter with repositories if necessary
        if hasattr(self._reporter, 'set_repositories'):
            self._reporter.set_repositories(
                ticket_repository=zendesk_client,
                analysis_repository=db_repository
            )
    
    def generate_report(self, view=None, format_type="text"):
        """
        Generate a pending tickets report.
        
        Args:
            view: View ID or name (optional)
            format_type: Output format (text, html, etc.)
            
        Returns:
            Report content
        """
        logger.debug(f"PendingReporterAdapter.generate_report called for view {view}")
        
        return self._reporter.generate_report(
            view_id_or_name=view,
            format_type=format_type
        )
    
    def get_report_filename(self, view=None, format_type="text"):
        """
        Get a filename for the report.
        
        Args:
            view: View ID or name (optional)
            format_type: Output format (text, html, etc.)
            
        Returns:
            Filename
        """
        logger.debug(f"PendingReporterAdapter.get_report_filename called for view {view}")
        
        return self._reporter.get_report_filename(
            view_id_or_name=view,
            format_type=format_type
        )
    
    def analyze_view(self, view):
        """
        Analyze tickets in a view.
        
        Args:
            view: View ID or name
            
        Returns:
            Analysis results
        """
        logger.debug(f"PendingReporterAdapter.analyze_view called for view {view}")
        
        return self._reporter.analyze_view(
            view_id_or_name=view
        )
