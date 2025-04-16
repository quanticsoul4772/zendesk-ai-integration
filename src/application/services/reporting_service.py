"""
Reporting Service

This module provides the implementation of the ReportingService interface.
It is responsible for generating various reports based on ticket data.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis
from src.domain.interfaces.repository_interfaces import TicketRepository, AnalysisRepository, ViewRepository
from src.domain.interfaces.reporter_interfaces import SentimentReporter, HardwareReporter, PendingReporter
from src.domain.interfaces.service_interfaces import ReportingService, TicketAnalysisService
from src.domain.exceptions import EntityNotFoundError

# Set up logging
logger = logging.getLogger(__name__)


class ReportingServiceImpl(ReportingService):
    """
    Implementation of the ReportingService interface.
    
    This service is responsible for generating various reports based on ticket data.
    """
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        analysis_repository: AnalysisRepository,
        view_repository: ViewRepository,
        sentiment_reporter: SentimentReporter,
        hardware_reporter: HardwareReporter,
        pending_reporter: PendingReporter,
        ticket_analysis_service: Optional[TicketAnalysisService] = None
    ):
        """
        Initialize the reporting service.
        
        Args:
            ticket_repository: Repository for ticket data
            analysis_repository: Repository for analysis data
            view_repository: Repository for view data
            sentiment_reporter: Reporter for sentiment analysis
            hardware_reporter: Reporter for hardware component reports
            pending_reporter: Reporter for pending support reports
            ticket_analysis_service: Optional service for ticket analysis
        """
        self.ticket_repository = ticket_repository
        self.analysis_repository = analysis_repository
        self.view_repository = view_repository
        self.sentiment_reporter = sentiment_reporter
        self.hardware_reporter = hardware_reporter
        self.pending_reporter = pending_reporter
        self.ticket_analysis_service = ticket_analysis_service
    
    def generate_sentiment_report(self, time_period: str = "week", view_id: Optional[int] = None) -> str:
        """
        Generate a sentiment analysis report.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            view_id: Optional view ID to filter by
            
        Returns:
            Report text
        """
        logger.info(f"Generating sentiment report for time period: {time_period}")
        
        # Calculate date range based on time period
        end_date = datetime.utcnow()
        
        if time_period == "day":
            from datetime import timedelta
            start_date = end_date - timedelta(days=1)
            days = 1
        elif time_period == "week":
            from datetime import timedelta
            start_date = end_date - timedelta(days=7)
            days = 7
        elif time_period == "month":
            from datetime import timedelta
            start_date = end_date - timedelta(days=30)
            days = 30
        elif time_period == "year":
            from datetime import timedelta
            start_date = end_date - timedelta(days=365)
            days = 365
        else:
            # Default to week
            from datetime import timedelta
            start_date = end_date - timedelta(days=7)
            days = 7
        
        # Get analyses for the time period
        analyses = self.analysis_repository.find_between_dates(start_date, end_date)
        
        # If a view ID is specified, filter analyses by view
        if view_id is not None:
            analyses = [a for a in analyses if a.source_view_id == view_id]
            
            # If no analyses found for the view, try to get the view name
            if not analyses:
                view = self.view_repository.get_view_by_id(view_id)
                view_name = view.get('title', f"View {view_id}") if view else f"View {view_id}"
                logger.warning(f"No analyses found for view: {view_name}")
        
        # Generate the report using the sentiment reporter
        title = f"Sentiment Analysis Report - Last {days} days"
        if view_id is not None:
            view = self.view_repository.get_view_by_id(view_id)
            view_name = view.get('title', f"View {view_id}") if view else f"View {view_id}"
            title += f" - {view_name}"
        
        report = self.sentiment_reporter.generate_report(analyses, title=title)
        
        logger.info(f"Generated sentiment report with {len(analyses)} analyses")
        
        return report
    
    def generate_hardware_report(self, view_id: Optional[int] = None, limit: Optional[int] = None, format_type: str = "text") -> str:
        """
        Generate a hardware component report.
        
        Args:
            view_id: Optional view ID to filter by
            limit: Maximum number of tickets to include
            format_type: Output format (text, html, etc.)
            
        Returns:
            Report text
        """
        logger.info(f"Generating hardware report for view ID: {view_id}")
        
        # Get tickets
        if view_id is not None:
            tickets = self.ticket_repository.get_tickets_from_view(view_id, limit)
            
            # If no tickets found, try to get the view name
            if not tickets:
                view = self.view_repository.get_view_by_id(view_id)
                view_name = view.get('title', f"View {view_id}") if view else f"View {view_id}"
                logger.warning(f"No tickets found for view: {view_name}")
                return f"No tickets found for view: {view_name}"
        else:
            # Get all open tickets if no view specified
            tickets = self.ticket_repository.get_tickets("open", limit)
        
        # Generate the report using the hardware reporter
        title = "Hardware Component Report"
        if view_id is not None:
            view = self.view_repository.get_view_by_id(view_id)
            view_name = view.get('title', f"View {view_id}") if view else f"View {view_id}"
            title += f" - {view_name}"
        
        report = self.hardware_reporter.generate_report(tickets, title=title, format=format_type)
        
        logger.info(f"Generated hardware report with {len(tickets)} tickets")
        
        return report
    
    def generate_pending_report(self, view_name: str, limit: Optional[int] = None) -> str:
        """
        Generate a pending ticket report.
        
        Args:
            view_name: Name of the pending view
            limit: Maximum number of tickets to include
            
        Returns:
            Report text
        """
        logger.info(f"Generating pending report for view: {view_name}")
        
        # Get tickets from the view
        tickets = self.ticket_repository.get_tickets_from_view_name(view_name, limit)
        
        if not tickets:
            logger.warning(f"No tickets found for view: {view_name}")
            return f"No tickets found for view: {view_name}"
        
        # Generate the report using the pending reporter
        report = self.pending_reporter.generate_report(tickets, view_name=view_name)
        
        logger.info(f"Generated pending report with {len(tickets)} tickets")
        
        return report
    
    def generate_multi_view_report(self, view_ids: List[int], report_type: str, limit: Optional[int] = None, format_type: str = "text") -> str:
        """
        Generate a multi-view report.
        
        Args:
            view_ids: List of view IDs to include
            report_type: Type of report ('sentiment', 'hardware', 'pending')
            limit: Maximum number of tickets per view
            format_type: Output format (text, html, etc.)
            
        Returns:
            Report text
        """
        logger.info(f"Generating {report_type} report for {len(view_ids)} views")
        
        # Get tickets from all views
        tickets = self.ticket_repository.get_tickets_from_multiple_views(view_ids, limit)
        
        if not tickets:
            logger.warning(f"No tickets found for the specified views")
            return "No tickets found for the specified views"
        
        # Get view names for the report
        view_map = self.view_repository.get_view_names_by_ids(view_ids)
        
        # Generate the appropriate report based on the report type
        if report_type == "sentiment":
            # For sentiment report, we need to analyze the tickets first
            if self.ticket_analysis_service:
                # Use existing analyses if available
                ticket_ids = [ticket.id for ticket in tickets]
                analyses = []
                
                for ticket_id in ticket_ids:
                    analysis = self.analysis_repository.get_by_ticket_id(str(ticket_id))
                    if analysis:
                        analyses.append(analysis)
                
                # If not all tickets have been analyzed, analyze them now
                if len(analyses) < len(tickets):
                    logger.info(f"Analyzing {len(tickets) - len(analyses)} unanalyzed tickets")
                    
                    # Identify tickets that haven't been analyzed
                    analyzed_ids = {int(analysis.ticket_id) for analysis in analyses}
                    unanalyzed_tickets = [ticket for ticket in tickets if ticket.id not in analyzed_ids]
                    
                    # Analyze unanalyzed tickets
                    for ticket in unanalyzed_tickets:
                        try:
                            analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
                            analyses.append(analysis)
                        except Exception as e:
                            logger.error(f"Error analyzing ticket {ticket.id}: {str(e)}")
                
                # Generate the report
                title = "Multi-View Sentiment Analysis Report"
                report = self.sentiment_reporter.generate_multi_view_report(analyses, view_map, title)
            else:
                logger.error("Ticket analysis service is required for sentiment reports")
                return "Cannot generate sentiment report without ticket analysis service"
        elif report_type == "hardware":
            # Generate hardware report
            title = "Multi-View Hardware Component Report"
            report = self.hardware_reporter.generate_multi_view_report(tickets, view_map, title, format=format_type)
        elif report_type == "pending":
            # Group tickets by view
            tickets_by_view = {}
            for ticket in tickets:
                if hasattr(ticket, 'source_view_id') and ticket.source_view_id in view_map:
                    view_name = view_map[ticket.source_view_id]
                    if view_name not in tickets_by_view:
                        tickets_by_view[view_name] = []
                    tickets_by_view[view_name].append(ticket)
            
            # Generate pending report
            report = self.pending_reporter.generate_multi_view_report(tickets_by_view)
        else:
            logger.error(f"Unknown report type: {report_type}")
            return f"Unknown report type: {report_type}"
        
        logger.info(f"Generated multi-view {report_type} report with {len(tickets)} tickets")
        
        return report
    
    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """
        Save a report to a file.
        
        Args:
            report: Report text
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to the saved report file
        """
        if not filename:
            # Generate a filename based on the current date and time
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"report_{timestamp}.txt"
        
        try:
            # Ensure the reports directory exists
            reports_dir = os.path.join(os.getcwd(), "reports")
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # Save the report to the file
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"Saved report to {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error saving report to {filename}: {str(e)}")
            
            # Try to save in the current directory as a fallback
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Saved report to {filename} in current directory")
                
                return filename
            except Exception as e2:
                logger.error(f"Error saving report to current directory: {str(e2)}")
                return ""
