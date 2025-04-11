"""
Menu Actions Module - Updated with View Status Checking

This module extends the basic menu system with action handlers that connect
to the actual functionality in the Zendesk AI integration, including view status checking.
"""

import os
import sys
import logging
import webbrowser
import subprocess
from datetime import datetime as dt
from typing import Dict, Any, Optional, List

# Import base menu class
from .zendesk_menu import ZendeskMenu

# Set up logging
logger = logging.getLogger(__name__)

class ZendeskMenuActions(ZendeskMenu):
    """
    Extended ZendeskMenu class with concrete action implementations.
    
    This class implements the action handlers that connect the interactive menu
    to the actual functionality in the Zendesk AI integration.
    """
    
    def __init__(self, zendesk_client, ai_analyzer=None, db_repository=None, report_modules=None):
        """
        Initialize the ZendeskMenuActions with required components.
        
        Args:
            zendesk_client: Instance of ZendeskClient for API interactions
            ai_analyzer: Optional AI analyzer for sentiment analysis
            db_repository: Optional database repository for storing analysis results
            report_modules: Optional dictionary of report modules
        """
        super().__init__(zendesk_client, db_repository)
        
        self.ai_analyzer = ai_analyzer
        self.report_modules = report_modules or {}
        
        # Override action handlers with real implementations
        self.action_handlers = {
            "run_sentiment_analysis": self._action_run_sentiment_analysis,
            "generate_report": self._action_generate_report,
            "view_tickets": self._action_view_tickets,
            "check_views_for_tickets": self._action_check_views_for_tickets
        }
        
        logger.info("Initialized ZendeskMenuActions with action handlers")
        
    def _display_progress_message(self, message: str) -> None:
        """
        Display a progress message to the user.
        
        Args:
            message: The message to display
        """
        # Clear the line and display the message
        print(f"\r{message}", end="", flush=True)
        
    def _display_result_and_wait(self, message: str) -> None:
        """
        Display a result message and wait for user input.
        
        Args:
            message: The message to display
        """
        print(f"\n{message}")
        input("\nPress Enter to continue...")
        
    def _action_run_sentiment_analysis(self, view_id: int, view_name: str) -> None:
        """
        Run sentiment analysis on tickets from a view.
        
        Args:
            view_id: ID of the selected view
            view_name: Name of the selected view
        """
        if not self.ai_analyzer:
            self._display_result_and_wait("AI Analyzer not available. Cannot run sentiment analysis.")
            return
            
        if not self.db_repository:
            self._display_result_and_wait("Database repository not available. Cannot store analysis results.")
            return
            
        try:
            # Display a progress message
            self._display_progress_message(f"Fetching tickets from view: {view_name}...")
            
            # Fetch tickets from the view
            tickets = self.zendesk_client.fetch_tickets_from_view(view_id)
            
            # Update the view status cache based on whether tickets were found
            has_tickets = len(tickets) > 0
            self._view_status_cache[view_id] = has_tickets
            
            if not tickets:
                self._display_result_and_wait(f"No tickets found in view: {view_name}")
                return
                
            # Display progress
            self._display_progress_message(f"Analyzing {len(tickets)} tickets from view: {view_name}...")
            
            # Use Claude for analysis (can be changed to use OpenAI if preferred)
            use_claude = True
            
            # Use batch processing to analyze tickets
            analyses = self.ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
            
            # Save all analyses to database
            for analysis in analyses:
                self.db_repository.save_analysis(analysis)
            
            # Display result
            self._display_result_and_wait(
                f"Successfully analyzed {len(analyses)} tickets from view: {view_name}\n"
                f"Results have been saved to the database."
            )
            
        except Exception as e:
            logger.exception(f"Error running sentiment analysis: {e}")
            self._display_result_and_wait(f"Error running sentiment analysis: {str(e)}")
            
    def _action_generate_report(self, view_id: int, view_name: str, report_type: str = "pending") -> None:
        """
        Generate a report for a view.
        
        Args:
            view_id: ID of the selected view
            view_name: Name of the selected view
            report_type: Type of report to generate ("pending" or "enhanced")
        """
        if report_type == "pending":
            if "pending" not in self.report_modules:
                self._display_result_and_wait("Pending reporter module not available.")
                return
                
            try:
                # Display a progress message
                self._display_progress_message(f"Generating pending report for view: {view_name}...")
                
                # Generate the report
                reporter = self.report_modules["pending"]
                report = reporter.generate_report(self.zendesk_client, self.db_repository, pending_view=view_name)
                
                # Save the report to a file
                timestamp = dt.utcnow().strftime('%Y%m%d_%H%M')
                filename = f"pending_report_{timestamp}.txt"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                # Display the report
                print("\n" + report)
                
                # Wait for user input
                self._display_result_and_wait(f"Report saved to: {filename}")
                
            except Exception as e:
                logger.exception(f"Error generating pending report: {e}")
                self._display_result_and_wait(f"Error generating pending report: {str(e)}")
                
        elif report_type == "enhanced":
            if "sentiment_enhanced" not in self.report_modules:
                self._display_result_and_wait("Enhanced sentiment reporter module not available.")
                return
                
            try:
                # Display a progress message
                self._display_progress_message(f"Generating enhanced sentiment report for view: {view_name}...")
                
                # First, check if view has tickets
                if view_id in self._view_status_cache and self._view_status_cache[view_id] is False:
                    # We know this view has no tickets
                    self._display_result_and_wait(
                        f"View '{view_name}' is empty. No tickets to report on.\n"
                        f"Please choose a different view or run sentiment analysis first."
                    )
                    return
                
                # Fetch recent analyses from the database for this view
                if self.db_repository:
                    # Calculate date range (last 7 days)
                    from datetime import datetime, timedelta
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=7)
                    
                    # Get analyses for this view
                    analyses = self.db_repository.find_analyses_for_view(view_id, start_date, end_date)
                    
                    if not analyses:
                        # If no analyses found, check if the view has tickets first
                        if view_id not in self._view_status_cache:
                            # Check if view has tickets
                            tickets = self.zendesk_client.fetch_tickets_from_view(view_id, limit=1)
                            has_tickets = len(tickets) > 0
                            self._view_status_cache[view_id] = has_tickets
                            
                            if not has_tickets:
                                self._display_result_and_wait(
                                    f"View '{view_name}' is empty. No tickets to report on.\n"
                                    f"Please choose a different view."
                                )
                                return
                        
                        # If view has tickets but no analyses, offer to run analysis first
                        prompt = input("\nNo recent analyses found for this view. Run sentiment analysis first? (y/n): ")
                        if prompt.lower() == 'y':
                            self._action_run_sentiment_analysis(view_id, view_name)
                            # Try again with fresh data
                            analyses = self.db_repository.find_analyses_for_view(view_id, start_date, end_date)
                        else:
                            self._display_result_and_wait("Report generation canceled.")
                            return
                            
                    # Generate the report
                    reporter = self.report_modules["sentiment_enhanced"]
                    title = f"Enhanced Sentiment Analysis Report - {view_name}"
                    report = reporter.generate_report(analyses, title=title)
                    
                    # Save the report to a file
                    timestamp = dt.now().strftime('%Y%m%d_%H%M')
                    filename = f"enhanced_sentiment_report_{timestamp}.txt"
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    # Display the report
                    print("\n" + report)
                    
                    # Wait for user input
                    self._display_result_and_wait(f"Report saved to: {filename}")
                else:
                    self._display_result_and_wait("Database repository not available. Cannot generate report.")
                    
            except Exception as e:
                logger.exception(f"Error generating enhanced sentiment report: {e}")
                self._display_result_and_wait(f"Error generating enhanced sentiment report: {str(e)}")
                
    def _action_view_tickets(self, view_id: int, view_name: str) -> None:
        """
        Open the view in a web browser.
        
        Args:
            view_id: ID of the selected view
            view_name: Name of the selected view
        """
        try:
            # Get the Zendesk subdomain from environment or ZendeskClient
            subdomain = os.getenv("ZENDESK_SUBDOMAIN")
            
            if not subdomain:
                # Try to extract from the ZendeskClient if possible
                if hasattr(self.zendesk_client, 'client') and hasattr(self.zendesk_client.client, 'subdomain'):
                    subdomain = self.zendesk_client.client.subdomain
                else:
                    self._display_result_and_wait("Zendesk subdomain not found. Cannot open view in browser.")
                    return
            
            # Construct the URL
            url = f"https://{subdomain}.zendesk.com/agent/filters/{view_id}"
            
            # Open in browser
            self._display_progress_message(f"Opening view in browser: {view_name}...")
            webbrowser.open(url)
            
            # Wait for user input
            self._display_result_and_wait(f"Opened view in browser: {url}")
            
        except Exception as e:
            logger.exception(f"Error opening view in browser: {e}")
            self._display_result_and_wait(f"Error opening view in browser: {str(e)}")
            
    def _action_check_views_for_tickets(self, view_ids: List[int] = None) -> None:
        """
        Check which views have tickets and update the status cache.
        
        Args:
            view_ids: Optional list of view IDs to check. If None, all views are checked.
        """
        try:
            # If no view IDs provided, check all views
            if view_ids is None:
                all_views = {}
                for view in self.views:
                    if hasattr(view, 'title') and hasattr(view, 'id'):
                        all_views[view.title] = view.id
                view_ids = list(all_views.values())
            
            # Show progress message
            self._display_progress_message(f"Checking {len(view_ids)} views for tickets...")
            
            # Check each view
            views_with_tickets = 0
            views_without_tickets = 0
            
            for i, view_id in enumerate(view_ids):
                # Update progress message
                progress_percent = int((i + 1) / len(view_ids) * 100)
                self._display_progress_message(f"Checking views for tickets: {i + 1}/{len(view_ids)} ({progress_percent}%)...")
                
                try:
                    # Fetch one ticket to check if view has any tickets
                    tickets = self.zendesk_client.fetch_tickets_from_view(view_id, limit=1)
                    has_tickets = len(tickets) > 0
                    self._view_status_cache[view_id] = has_tickets
                    
                    if has_tickets:
                        views_with_tickets += 1
                    else:
                        views_without_tickets += 1
                        
                except Exception as e:
                    logger.error(f"Error checking view {view_id} status: {e}")
                    # If there's an error, we don't know the status
                    self._view_status_cache[view_id] = None
            
            # Display completion message
            self._display_result_and_wait(
                f"Successfully checked {len(view_ids)} views:\n"
                f"- Views with tickets: {views_with_tickets}\n"
                f"- Empty views: {views_without_tickets}\n"
                f"\nView status indicators have been updated in the menus."
            )
            
        except Exception as e:
            logger.exception(f"Error checking views for tickets: {e}")
            self._display_result_and_wait(f"Error checking views for tickets: {str(e)}")
