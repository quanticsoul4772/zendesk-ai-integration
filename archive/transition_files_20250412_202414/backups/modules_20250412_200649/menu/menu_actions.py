"""
Menu Actions Module

This module provides backward compatibility for the menu actions module.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)


class ZendeskMenuActions:
    """
    Legacy menu actions class.
    
    This is a compatibility stub that delegates to the new implementation.
    """
    
    def __init__(self, zendesk_client=None, ai_analyzer=None, db_repository=None):
        """
        Initialize the menu actions.
        
        Args:
            zendesk_client: ZendeskClient instance
            ai_analyzer: AIAnalyzer instance
            db_repository: DBRepository instance
        """
        logger.debug("ZendeskMenuActions initialized (compatibility mode)")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
    
    def analyze_view(self, view_id, use_claude=False):
        """
        Analyze a view.
        
        Args:
            view_id: ID of the view to analyze
            use_claude: Whether to use Claude for analysis
            
        Returns:
            Analysis results
        """
        logger.debug(f"Analyzing view {view_id} (compatibility mode)")
        
        # Import here to avoid circular imports
        from src.presentation.cli.commands.analyze_ticket_command import AnalyzeTicketCommand
        
        command = AnalyzeTicketCommand()
        return command.analyze_view(view_id, use_claude)
    
    def generate_report(self, view_id, report_type, days=30):
        """
        Generate a report.
        
        Args:
            view_id: ID of the view to report on
            report_type: Type of report to generate
            days: Number of days to include in the report
            
        Returns:
            Report content
        """
        logger.debug(f"Generating {report_type} report for view {view_id} (compatibility mode)")
        
        # Import here to avoid circular imports
        from src.presentation.cli.commands.generate_report_command import GenerateReportCommand
        
        command = GenerateReportCommand()
        return command.generate_report(view_id, report_type, days)
