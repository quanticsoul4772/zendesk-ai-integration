"""
Command-Line Interface Module

This module handles parsing command-line arguments and executing
the appropriate actions based on the specified mode.
"""

import argparse
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_sentiment_reporter(format_arg="enhanced", db_repository=None):
    """
    Get a unified sentiment reporter instance with the appropriate format setting.
    
    Args:
        format_arg: Format to use ("enhanced" or "standard")
        db_repository: Database repository instance
        
    Returns:
        Initialized reporter instance
    """
    from modules.reporters import SentimentReporter
    
    # Determine the mode based on format_arg
    enhanced_mode = format_arg == "enhanced"
    
    # Create the reporter with the appropriate settings
    return SentimentReporter(db_repository=db_repository, enhanced_mode=enhanced_mode)
class CommandLineInterface:
    """
    Handles parsing command-line arguments and executing the appropriate actions.
    """
    
    def __init__(self):
        """Initialize the command-line interface."""
        self.parser = argparse.ArgumentParser(description="Zendesk AI Integration App")
        self._setup_arguments()
    
    def _setup_arguments(self):
        """Set up command-line arguments."""
        self.parser.add_argument(
            "--mode", 
            choices=["run", "webhook", "schedule", "summary", "report", "pending", "list-views", "sentiment", "multi-view", "interactive"], 
            default="run",
            help="Operation mode"
        )
        
        self.parser.add_argument(
            "--status", 
            default="open",
            help="Ticket status to filter by (open, new, pending, solved, closed, all)"
        )
        
        self.parser.add_argument(
            "--limit", 
            type=int, 
            help="Maximum number of tickets to retrieve"
        )
        
        self.parser.add_argument(
            "--days", 
            type=int,
            help="Number of days back to include in summary"
        )
        
        self.parser.add_argument(
            "--view", 
            help="Zendesk view ID to analyze"
        )
        
        self.parser.add_argument(
            "--views", 
            help="Comma-separated list of Zendesk view IDs to analyze (e.g., '12345,67890')"
        )
        
        self.parser.add_argument(
            "--view-name", 
            help="Name of the Zendesk view to analyze"
        )
        
        self.parser.add_argument(
            "--view-names", 
            help="Comma-separated list of Zendesk view names to analyze (e.g., 'Support Queue,Pending Support')"
        )
        
        self.parser.add_argument(
            "--pending-view", 
            help="Name of the pending support view to analyze"
        )
        
        # Enhanced sentiment analysis is now the standard - no flags needed
        
        self.parser.add_argument(
            "--use-claude", 
            action="store_true", 
            help="Use Claude AI for sentiment analysis (default: True)"
        )
        
        self.parser.add_argument(
            "--use-openai", 
            action="store_true", 
            help="Use OpenAI for sentiment analysis instead of Claude"
        )
        
        self.parser.add_argument(
            "--reanalyze", 
            action="store_true", 
            help="Reanalyze existing tickets in the database with AI sentiment analysis"
        )
        
        self.parser.add_argument(
            "--component-report", 
            action="store_true", 
            help="Generate a hardware component report"
        )
        
        self.parser.add_argument(
            "--output", 
            help="Filename to save the report to (will be created in current directory)"
        )
        
        self.parser.add_argument(
            "--format", 
            choices=["standard", "enhanced"],
            default="enhanced",
            help="Report format to use (standard or enhanced with descriptive labels)"
        )
        
        self.parser.add_argument(
            "--add-comments", 
            action="store_true", 
            help="Add private comments to tickets with analysis results"
        )
        
        self.parser.add_argument(
            "--host", 
            default="0.0.0.0", 
            help="Host address for webhook server"
        )
        
        self.parser.add_argument(
            "--port", 
            type=int, 
            default=5000, 
            help="Port for webhook server"
        )
    
    def parse_args(self):
        """
        Parse command-line arguments.
        
        Returns:
            Parsed arguments
        """
        return self.parser.parse_args()
    
    def execute(self, args, zendesk_client, ai_analyzer, db_repository, report_modules):
        """
        Execute the appropriate action based on the specified mode.
        
        Args:
            args: Parsed command-line arguments
            zendesk_client: ZendeskClient instance
            ai_analyzer: AIAnalyzer instance
            db_repository: DBRepository instance
            report_modules: Dict with report generator modules
            
        Returns:
            Boolean indicating success
        """
        # Enhanced sentiment analysis is now the standard
        use_enhanced = True
        
        # Determine which AI provider to use
        use_claude = not args.use_openai  # Use Claude by default unless OpenAI is specified
        
        try:
            # Handle different modes
            if args.mode == "run":
                return self._handle_run_mode(args, zendesk_client, ai_analyzer, db_repository, 
                                            use_enhanced, use_claude, report_modules)
                
            elif args.mode == "webhook":
                return self._handle_webhook_mode(args, zendesk_client, ai_analyzer, db_repository)
                
            elif args.mode == "schedule":
                return self._handle_schedule_mode(args, zendesk_client, ai_analyzer, db_repository)
                
            elif args.mode == "summary":
                return self._handle_summary_mode(args, zendesk_client, db_repository)
                
            elif args.mode == "report":
                return self._handle_report_mode(args, zendesk_client, report_modules)
                
            elif args.mode == "pending":
                return self._handle_pending_mode(args, zendesk_client, report_modules, db_repository)
                
            elif args.mode == "list-views":
                return self._handle_list_views_mode(args, zendesk_client)
                
            elif args.mode == "sentiment":
                return self._handle_sentiment_mode(args, zendesk_client, ai_analyzer, db_repository, report_modules, use_enhanced, use_claude)
                
            elif args.mode == "multi-view":
                return self._handle_multi_view_mode(args, zendesk_client, ai_analyzer, db_repository, report_modules, use_enhanced, use_claude)
                
            elif args.mode == "interactive":
                return self._handle_interactive_mode(args, zendesk_client, db_repository)
                
            else:
                logger.error(f"Unknown mode: {args.mode}")
                return False
                
        except KeyboardInterrupt:
            logger.info("Operation interrupted by user.")
            return False
        except Exception as e:
            logger.exception(f"Error in {args.mode} mode: {e}")
            return False
    
    def _handle_run_mode(self, args, zendesk_client, ai_analyzer, db_repository, 
                         use_enhanced, use_claude, report_modules):
        """Handle 'run' mode: analyze tickets and update them."""
        # Handle multi-view analysis if views are specified
        if args.views:
            return self._handle_multi_view_mode(args, zendesk_client, ai_analyzer, db_repository, 
                                               report_modules, use_enhanced, use_claude)
        elif args.view_names:
            return self._handle_multi_view_names_mode(args, zendesk_client, ai_analyzer, db_repository, 
                                                    report_modules, use_enhanced, use_claude)
        
        # Handle reanalysis mode if specified
        if args.reanalyze:
            return self._handle_reanalysis_mode(args, zendesk_client, ai_analyzer, db_repository, use_enhanced, use_claude)
            
        if args.view:
            logger.info(f"Fetching & processing tickets from view {args.view}...")
            tickets = zendesk_client.fetch_tickets_from_view(args.view, args.limit)
            
            if args.component_report:
                hardware_reporter = report_modules.get("hardware")
                if hardware_reporter:
                    report = hardware_reporter.generate_report(tickets)
                    print(report)
                    
                    # Optionally save to file
                    report_filename = args.output
                    if not report_filename:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                        report_filename = f"hardware_report_{timestamp}.txt"
                    
                    with open(report_filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    logger.info(f"Hardware component report generated with {len(tickets)} tickets and saved to {report_filename}")
                else:
                    logger.error("Hardware reporter module not available.")
            else:
                # Use batch processing to analyze tickets
                logger.info(f"Processing {len(tickets)} tickets using batch processing...")
                
                # Use the batch processor to analyze all tickets in parallel
                analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
                
                # Save all analyses to database
                for analysis in analyses:
                    db_repository.save_analysis(analysis)
                
                logger.info(f"Processed {len(analyses)} tickets using batch processing. Done.")
        else:
            logger.info(f"Fetching & analyzing tickets with status: {args.status}")
            tickets = zendesk_client.fetch_tickets(args.status, args.limit)
            
            # Use batch processing to analyze tickets
            logger.info(f"Processing {len(tickets)} tickets using batch processing...")
            
            # Use the batch processor to analyze all tickets in parallel
            analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
            
            # Save all analyses to database
            for analysis in analyses:
                db_repository.save_analysis(analysis)
            
            logger.info(f"Processed {len(analyses)} tickets using batch processing. Done.")
        
        return True
        
    def _handle_interactive_mode(self, args, zendesk_client, db_repository):
        """Handle 'interactive' mode: show interactive menu for view navigation."""
        # Import the menu system
        try:
            from modules.menu.menu_actions import ZendeskMenuActions
            logger.info("Starting interactive menu mode...")
            
            # Check if required components are available for full functionality
            from modules import ai_analyzer as ai_module
            ai_analyzer = None
            if hasattr(ai_module, 'AIAnalyzer'):
                ai_analyzer = ai_module.AIAnalyzer()
            
            # Get report modules
            report_modules = {}
            try:
                from modules.reporters.pending_report import PendingReporter
                report_modules["pending"] = PendingReporter()
            except ImportError:
                logger.warning("PendingReporter module not available")
            
            try:
                from modules.reporters import SentimentReporter
                report_modules["sentiment"] = SentimentReporter(db_repository=db_repository, enhanced_mode=True)
            except ImportError:
                logger.warning("SentimentReporter module not available")
            
            # Initialize the menu system with all available components
            menu = ZendeskMenuActions(
                zendesk_client=zendesk_client,
                ai_analyzer=ai_analyzer,
                db_repository=db_repository,
                report_modules=report_modules
            )
            
            # Start the menu
            menu.start()
            return True
        except ImportError as e:
            logger.error(f"Error importing menu module: {e}")
            print("\nThe interactive menu requires additional dependencies.")
            print("Please install the required package with: pip install simple-term-menu\n")
            return False
        except Exception as e:
            logger.exception(f"Error in interactive menu: {e}")
            return False
    
    def _handle_multi_view_mode(self, args, zendesk_client, ai_analyzer, db_repository, 
                               report_modules, use_enhanced, use_claude):
        """Handle multi-view mode: analyze tickets from multiple views."""
        # Save args for access in _generate_multi_view_report
        self.args = args
        
        # Get a sentiment reporter instance with the appropriate format
        reporter = get_sentiment_reporter(format_arg=args.format, db_repository=db_repository)
        """Handle multi-view mode: analyze tickets from multiple views."""
        # Reporter already initialized
        
        # Get view IDs from the views argument
        if args.views:
            view_ids = [int(view_id.strip()) for view_id in args.views.split(",") if view_id.strip()]
        elif args.view_names:
            # If view names are provided, use the multi-view-names handler instead
            return self._handle_multi_view_names_mode(args, zendesk_client, ai_analyzer, db_repository, 
                                                  report_modules, use_enhanced, use_claude)
        elif args.mode == "multi-view":
            logger.error("No views specified. Use --views parameter with comma-separated view IDs or --view-names with comma-separated view names")
            return False
        else:
            # Called from run mode without views parameter
            logger.error("No views specified. Use --views parameter with comma-separated view IDs or --view-names with comma-separated view names")
            return False
            
        logger.info(f"Analyzing tickets from {len(view_ids)} views: {view_ids}")
        
        # Force refresh the views cache to ensure we have fresh data
        zendesk_client.cache.force_refresh_views()
        logger.info("Forced refresh of views cache before fetching tickets")
        
        # Get view names for better reporting
        view_map = zendesk_client.get_view_names_by_ids(view_ids)
        
        # Fetch tickets from all views
        tickets = zendesk_client.fetch_tickets_from_multiple_views(view_ids, args.limit, args.status)
        
        if not tickets:
            logger.error("No tickets found in the specified views")
            return False
            
        logger.info(f"Analyzing {len(tickets)} unique tickets from {len(view_ids)} views...")
        
        # If component report is requested, generate it
        if args.component_report:
            hardware_reporter = report_modules.get("hardware")
            if hardware_reporter:
                report = hardware_reporter.generate_multi_view_report(tickets, view_map)
                print(report)
                
                # Optionally save to file
                report_filename = args.output
                if not report_filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    report_filename = f"multi_view_hardware_report_{timestamp}.txt"
                
                with open(report_filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Multi-view hardware report generated with {len(tickets)} tickets and saved to {report_filename}")
                return True
            else:
                logger.error("Hardware reporter module not available.")
                return False
        
        # Use batch processing to analyze tickets
        logger.info(f"Processing {len(tickets)} tickets from {len(view_ids)} views using batch processing...")
        
        # Use the batch processor to analyze all tickets in parallel
        analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
        
        # Add view information to the analyses and save to database
        for analysis in analyses:
            ticket_id = analysis.get('ticket_id')
            # Find the corresponding ticket to get the view ID
            for ticket in tickets:
                if ticket.id == ticket_id and hasattr(ticket, 'source_view_id'):
                    analysis['source_view_id'] = getattr(ticket, 'source_view_id')
                    analysis['source_view_name'] = view_map.get(analysis['source_view_id'], "Unknown View")
                    break
            
            # Save analysis to database
            db_repository.save_analysis(analysis)
        
        logger.info(f"Processed {len(analyses)} tickets from {len(view_ids)} views using batch processing.")
        
        # Generate a multi-view report
        title = f"Multi-View Sentiment Analysis Report"
        report = self._generate_multi_view_report(analyses, view_map, title, reporter, zendesk_client, ai_analyzer, db_repository)
        
        # Output the report
        print(report)
        
        # Optionally save to file
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Multi-view report saved to {args.output}")
        else:
            # Save with auto-generated filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"multi_view_report_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Multi-view report saved to {filename}")
        
        return True
        
    def _handle_multi_view_names_mode(self, args, zendesk_client, ai_analyzer, db_repository, 
                                    report_modules, use_enhanced, use_claude):
        """Handle multi-view mode with view names instead of IDs."""
        # Import the unified sentiment reporter for multi-view reporting
        from modules.reporters import SentimentReporter
        
        # Initialize the reporter with appropriate settings
        sentiment_reporter = SentimentReporter(db_repository=db_repository, enhanced_mode=(args.format == "enhanced"))
        
        # Get view names from the view-names argument
        if args.view_names:
            view_names = [name.strip() for name in args.view_names.split(",") if name.strip()]
        else:
            logger.error("No view names specified. Use --view-names parameter with comma-separated view names")
            return False
            
        logger.info(f"Analyzing tickets from {len(view_names)} views by name: {view_names}")
        
        # Fetch tickets from all views
        tickets = zendesk_client.fetch_tickets_from_multiple_view_names(view_names, args.limit, args.status)
        
        if not tickets:
            logger.error("No tickets found in the specified views")
            return False
            
        logger.info(f"Analyzing {len(tickets)} unique tickets from {len(view_names)} views...")
        
        # Use batch processing to analyze tickets
        logger.info(f"Processing {len(tickets)} tickets from {len(view_names)} views using batch processing...")
        
        # Use the batch processor to analyze all tickets in parallel
        analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
        
        # Add view information to the analyses and save to database
        for analysis in analyses:
            ticket_id = analysis.get('ticket_id')
            # Find the corresponding ticket to get the view information
            for ticket in tickets:
                if ticket.id == ticket_id:
                    if hasattr(ticket, 'source_view_id'):
                        analysis['source_view_id'] = getattr(ticket, 'source_view_id')
                    if hasattr(ticket, 'source_view_name'):
                        analysis['source_view_name'] = getattr(ticket, 'source_view_name')
                    break
            
            # Save analysis to database
            db_repository.save_analysis(analysis)
        
        logger.info(f"Processed {len(analyses)} tickets from {len(view_names)} views using batch processing.")
        
        # Generate a multi-view report
        title = f"Multi-View Sentiment Analysis Report"
        
        # Create a view_map for reporting
        view_map = {}
        for analysis in analyses:
            if 'source_view_id' in analysis and 'source_view_name' in analysis:
                view_map[analysis['source_view_id']] = analysis['source_view_name']
        
        report = self._generate_multi_view_report(analyses, view_map, title, reporter, zendesk_client, ai_analyzer, db_repository)
        
        # Output the report
        print(report)
        
        # Optionally save to file
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Multi-view report saved to {args.output}")
        else:
            # Save with auto-generated filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"multi_view_report_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Multi-view report saved to {filename}")
        
        return True
    
    def _generate_multi_view_report(self, analyses, view_map, title, reporter=None, zendesk_client=None, ai_analyzer=None, db_repository=None):
        """Generate a report for tickets from multiple views."""
        # If no reporter is provided, initialize a new one based on format
        if reporter is None:
            from modules.reporters import SentimentReporter
            enhanced_mode = hasattr(self, 'args') and getattr(self.args, 'format', 'standard') == 'enhanced'
            reporter = SentimentReporter(db_repository=db_repository, enhanced_mode=enhanced_mode)
        """
        Generate a report for tickets from multiple views.
        
        Args:
            analyses: List of analysis results with source_view_id attributes
            view_map: Dict mapping view IDs to view names
            title: Title for the report
            
        Returns:
            Formatted report text
        """
        if not analyses:
            return "No analyses found for reporting."
        
        # Group analyses by view
        view_analyses = {}
        for analysis in analyses:
            view_id = analysis.get('source_view_id', 'unknown')
            if view_id not in view_analyses:
                view_analyses[view_id] = []
            view_analyses[view_id].append(analysis)
        
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"MULTI-VIEW SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total Tickets Analyzed: {len(analyses)}\n"
        report += f"Total Views: {len(view_analyses)}\n\n"
        
        # Views summary section
        report += "TICKETS BY VIEW\n--------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}")
            report += f"{view_name}: {len(view_tickets)} tickets\n"
        report += "\n"
        
        # Combined sentiment analysis
        report += "COMBINED SENTIMENT ANALYSIS\n-------------------------\n"
        report += reporter.generate_report(analyses, zendesk_client, ai_analyzer, db_repository)[61:]
        
        # Per-view sentiment analysis
        report += "\nPER-VIEW SENTIMENT ANALYSIS\n--------------------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}")
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            
            # Get sentiment distribution for this view
            polarity_counts = reporter._count_sentiment_polarities(view_tickets)
            report += "Sentiment Distribution:\n"
            for polarity, count in sorted(polarity_counts.items()):
                report += f"  {polarity}: {count}\n"
            
            # Get priority distribution for this view
            if hasattr(reporter, '_count_priority_scores'):
                priority_counts = reporter._count_priority_scores(view_tickets)
                high_priority = sum(count for score, count in priority_counts.items() if score >= 7)
            else:
                # Use _count_priority_range for EnhancedSentimentReporter
                high_priority = reporter._count_priority_range(view_tickets, 7, 10)
            report += f"High Priority Tickets (7-10): {high_priority}\n"
            
            # Get business impact for this view
            business_impact_count = reporter._count_business_impact(view_tickets)
            report += f"Business Impact Tickets: {business_impact_count}\n"
            
            # Calculate averages for this view
            avg_urgency = reporter._calculate_average_urgency(view_tickets)
            avg_frustration = reporter._calculate_average_frustration(view_tickets)
            avg_priority = reporter._calculate_average_priority(view_tickets)
            
            report += f"Average Urgency: {avg_urgency:.2f}/5\n"
            report += f"Average Frustration: {avg_frustration:.2f}/5\n"
            report += f"Average Priority: {avg_priority:.2f}/10\n"
        
        return report
    
    def _handle_webhook_mode(self, args, zendesk_client, ai_analyzer, db_repository):
        """Handle 'webhook' mode: start a webhook server."""
        from modules.webhook_server import WebhookServer
        
        webhook_server = WebhookServer(
            zendesk_client=zendesk_client,
            ai_analyzer=ai_analyzer,
            db_repository=db_repository
        )
        
        # Set comment preference based on command-line argument
        webhook_server.set_comment_preference(args.add_comments)
        
        # Run the webhook server
        webhook_server.run(host=args.host, port=args.port)
        return True
    
    def _handle_schedule_mode(self, args, zendesk_client, ai_analyzer, db_repository):
        """Handle 'schedule' mode: run scheduled tasks."""
        from modules.scheduler import TaskScheduler
        
        scheduler = TaskScheduler(
            zendesk_client=zendesk_client,
            ai_analyzer=ai_analyzer,
            db_repository=db_repository
        )
        
        scheduler.setup_schedules()
        scheduler.run()
        return True
    
    def _handle_summary_mode(self, args, zendesk_client, db_repository):
        """Handle 'summary' mode: generate summary reports."""
        # Check if multi-view support is requested
        if args.views:
            view_ids = [int(view_id.strip()) for view_id in args.views.split(",") if view_id.strip()]
            logger.info(f"Generating summary of tickets from {len(view_ids)} views...")
            
            # This functionality should be implemented in separate summary modules
            # For now, just show a message that it will be implemented
            logger.info("Multi-view summary generation will be implemented in a future update.")
            print("Multi-view summary functionality will be implemented in a future update.")
            return True
            
        # Default single-view summary
        logger.info(f"Generating summary of {args.status} tickets...")
        
        # This functionality should be implemented in separate summary modules
        # For now, just show a message that it will be implemented
        logger.info("Summary generation will be implemented in a future update.")
        print("Summary functionality will be implemented in a future update.")
        return True
    
    def _handle_report_mode(self, args, zendesk_client, report_modules):
        """Handle 'report' mode: generate hardware component reports."""
        # Check if multi-view support is requested
        if args.views:
            view_ids = [int(view_id.strip()) for view_id in args.views.split(",") if view_id.strip()]
            logger.info(f"Generating hardware component report for {len(view_ids)} views...")
            
            # Get view names for better reporting
            view_map = zendesk_client.get_view_names_by_ids(view_ids)
            
            # Fetch tickets from all views
            tickets = zendesk_client.fetch_tickets_from_multiple_views(view_ids, args.limit)
            
            if tickets:
                hardware_reporter = report_modules.get("hardware")
                if hardware_reporter:
                    report = hardware_reporter.generate_multi_view_report(tickets, view_map)
                    print(report)
                    
                    # Optionally save to file
                    report_filename = args.output
                    if not report_filename:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                        report_filename = f"multi_view_hardware_report_{timestamp}.txt"
                    
                    with open(report_filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    logger.info(f"Multi-view hardware component report generated with {len(tickets)} tickets and saved to {report_filename}")
                else:
                    logger.error("Hardware reporter module not available.")
            else:
                logger.error("No tickets found in the specified views")
            
            return True
        
        # Default single-view report
        if args.view:
            logger.info(f"Generating hardware component report for view {args.view}...")
            tickets = zendesk_client.fetch_tickets_from_view(args.view, args.limit)
            
            hardware_reporter = report_modules.get("hardware")
            if hardware_reporter:
                report = hardware_reporter.generate_report(tickets)
                print(report)
                
                # Optionally save to file
                report_filename = args.output
                if not report_filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    report_filename = f"hardware_report_{timestamp}.txt"
                
                with open(report_filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Hardware component report generated with {len(tickets)} tickets and saved to {report_filename}")
            else:
                logger.error("Hardware reporter module not available.")
        else:
            logger.error("View ID is required for report mode. Use --view or --views parameter.")
        
        return True
    
    def _handle_pending_mode(self, args, zendesk_client, report_modules, db_repository):
        """Handle 'pending' mode: generate pending support reports."""
        # Check if multi-view support is requested
        if args.view_names:
            view_names = [name.strip() for name in args.view_names.split(",") if name.strip()]
            logger.info(f"Generating pending report for {len(view_names)} views...")
            
            tickets_by_view = {}
            
            # Fetch tickets from each view
            for view_name in view_names:
                tickets = zendesk_client.fetch_tickets_by_view_name(view_name, args.limit)
                if tickets:
                    tickets_by_view[view_name] = tickets
                    logger.info(f"Fetched {len(tickets)} tickets from '{view_name}'")
                else:
                    logger.warning(f"No tickets found in '{view_name}' view or view not found.")
            
            if not tickets_by_view:
                logger.error("No tickets found in any of the specified views")
                return False
            
            # Generate a combined report
            pending_reporter = report_modules.get("pending")
            if pending_reporter:
                report = pending_reporter.generate_multi_view_report(tickets_by_view, db_repository=db_repository)
                print(report)
                
                # Optionally save to file
                report_filename = args.output
                if not report_filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    report_filename = f"multi_view_pending_report_{timestamp}.txt"
                
                with open(report_filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Multi-view pending report generated and saved to {report_filename}")
            else:
                logger.error("Pending reporter module not available.")
            
            return True
        
        # Default single-view mode
        view_name = args.pending_view
        if not view_name:
            logger.error("Pending view name is required. Use --pending-view parameter.")
            return False
        
        logger.info(f"Generating report for {view_name} view...")
        tickets = zendesk_client.fetch_tickets_by_view_name(view_name, args.limit)
        
        if tickets:
            pending_reporter = report_modules.get("pending")
            if pending_reporter:
                report = pending_reporter.generate_report(zendesk_client, db_repository, pending_view=view_name)
                print(report)
                
                # Optionally save to file
                report_filename = args.output
                if not report_filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    report_filename = f"pending_support_report_{timestamp}.txt"
                
                with open(report_filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Pending Support report generated with {len(tickets)} tickets and saved to {report_filename}")
            else:
                logger.error("Pending reporter module not available.")
        else:
            logger.error(f"No tickets found in '{view_name}' view or view not found.")
        
        return True
    
    def _handle_list_views_mode(self, args, zendesk_client):
        """Handle 'list-views' mode: list all available Zendesk views."""
        logger.info("Listing all available Zendesk views...")
        views_list = zendesk_client.list_all_views()
        print(views_list)
        
        # Optionally save to file
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(views_list)
            logger.info(f"Views list saved to {args.output}")
        
        return True
        
    def _handle_reanalysis_mode(self, args, zendesk_client, ai_analyzer, db_repository, use_enhanced, use_claude):
        """Handle the reanalysis of existing tickets in the database."""
        # Set up time range for reanalysis
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        
        if args.days:
            start_date = end_date - timedelta(days=args.days)
            logger.info(f"Reanalyzing tickets from the last {args.days} days")
        else:
            # Default to 30 days if not specified
            start_date = end_date - timedelta(days=30)
            logger.info("Reanalyzing tickets from the last 30 days")
        
        # Get existing analyses from database
        analyses = db_repository.find_analyses_between(start_date, end_date)
        
        if not analyses:
            logger.warning(f"No existing analyses found in the specified time period")
            return False
        
        logger.info(f"Found {len(analyses)} existing analyses to reanalyze")
        
        # Limit the number of analyses if specified
        if args.limit and len(analyses) > args.limit:
            analyses = analyses[:args.limit]
            logger.info(f"Limiting reanalysis to {args.limit} tickets")
        
        successful_updates = 0
        failed_updates = 0
        
        # Reanalyze each ticket
        for old_analysis in analyses:
            ticket_id = old_analysis.get("ticket_id")
            subject = old_analysis.get("subject", "")
            
            # Try to fetch the full ticket for description
            logger.info(f"Fetching ticket {ticket_id} for reanalysis")
            tickets = zendesk_client.fetch_tickets(filter_by={"id": ticket_id})
            
            if not tickets:
                # If ticket can't be fetched (e.g., deleted), continue
                logger.warning(f"Ticket {ticket_id} not found in Zendesk, skipping reanalysis")
                failed_updates += 1
                continue
            
            ticket = tickets[0]
            description = ticket.description or ""
            
            # Perform AI analysis
            logger.info(f"Reanalyzing ticket {ticket_id} with {'enhanced' if use_enhanced else 'basic'} sentiment analysis using {'Claude' if use_claude else 'OpenAI'}")
            new_analysis = ai_analyzer.analyze_ticket(
                ticket_id=ticket_id,
                subject=subject,
                description=description,
                use_enhanced=use_enhanced,
                use_claude=use_claude
            )
            
            # Update in database
            result = db_repository.update_analysis(new_analysis)
            
            if result:
                successful_updates += 1
            else:
                failed_updates += 1
        
        logger.info(f"Reanalysis complete: {successful_updates} successful, {failed_updates} failed")
        return successful_updates > 0
    
    def _handle_sentiment_mode(self, args, zendesk_client, ai_analyzer, db_repository, report_modules, use_enhanced=True, use_claude=True):
        """Handle 'sentiment' mode: generate sentiment analysis reports."""
        # Initialize the unified sentiment reporter with appropriate format
        from modules.reporters import SentimentReporter
        reporter = SentimentReporter(db_repository=db_repository, enhanced_mode=(args.format == "enhanced"))
        """Handle 'sentiment' mode: generate sentiment analysis reports."""
        # Check if multi-view support is requested
        if args.views or args.view_names:
            return self._handle_multi_view_mode(args, zendesk_client, ai_analyzer, db_repository, 
                                              report_modules, use_enhanced, use_claude)
        
        # Reporter has already been initialized based on format
        
        # Determine the time period (default to week if not specified)
        time_period = "week"
        if args.days == 1:
            time_period = "day"
        elif args.days == 7:
            time_period = "week"
        elif args.days == 30:
            time_period = "month"
        elif args.days == 365:
            time_period = "year"
        else:
            # Custom day range
            time_period = f"{args.days} days"
        
        logger.info(f"Generating sentiment analysis report for the last {args.days} days")
        
        # If view is specified, analyze tickets from that view
        if args.view:
            logger.info(f"Analyzing tickets from view {args.view}...")
            # Try to parse as integer (view ID)
            try:
                view_id = int(args.view)
                tickets = zendesk_client.fetch_tickets_from_view(view_id, args.limit)
                view_desc = f"View ID: {args.view}"
            except ValueError:
                # Not an integer, treat as view name
                tickets = zendesk_client.fetch_tickets_by_view_name(args.view, args.limit)
                view_desc = f"View: {args.view}"
            
            # If tickets found, analyze them
            if tickets:
                logger.info(f"Analyzing {len(tickets)} tickets from {view_desc}...")
                # Use batch processing to analyze tickets
                analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=use_claude)
                
                # Save all analyses to database
                for analysis in analyses:
                    db_repository.save_analysis(analysis)
                
                # Generate report
                title = f"Sentiment Analysis Report - {view_desc}"
                report = reporter.generate_report(analyses, title=title)
            else:
                logger.error(f"No tickets found in {view_desc}")
                return False
        elif args.view_name:
            logger.info(f"Analyzing tickets from view {args.view_name}...")
            tickets = zendesk_client.fetch_tickets_by_view_name(args.view_name, args.limit)
            
            # If tickets found, analyze them
            if tickets:
                logger.info(f"Analyzing {len(tickets)} tickets from view '{args.view_name}'...")
                analyses = []
                for ticket in tickets:
                    analysis = ai_analyzer.analyze_ticket(
                        ticket_id=ticket.id,
                        subject=ticket.subject or "",
                        description=ticket.description or "",
                        use_enhanced=use_enhanced,
                        use_claude=use_claude
                    )
                    analyses.append(analysis)
                    db_repository.save_analysis(analysis)
                
                # Generate report
                title = f"Sentiment Analysis Report - View: {args.view_name}"
                report = reporter.generate_report(analyses, title=title)
            else:
                logger.error(f"No tickets found in view '{args.view_name}'")
                return False
        else:
            # Use existing data from the database
            logger.info(f"Generating report from existing analysis data for the last {args.days} days...")
            
            # Calculate date range
            from datetime import datetime, timedelta
            end_date = datetime.utcnow()
            
            # Use a default of 7 days if days parameter is None
            days_value = args.days if args.days is not None else 7
            start_date = end_date - timedelta(days=days_value)
            
            # Find analyses in date range
            analyses = db_repository.find_analyses_between(start_date, end_date)
            
            if analyses:
                logger.info(f"Found {len(analyses)} analyses in the database for the specified period")
                # Generate report
                title = f"Sentiment Analysis Report - Last {days_value} days"
                report = reporter.generate_report(analyses, title=title)
            else:
                logger.error(f"No analyses found in the database for the last {days_value} days")
                return False
        
        # Output the report
        print(report)
        
        # Optionally save to file
        if args.output:
            reporter.save_report(report, args.output)
            logger.info(f"Sentiment analysis report saved to {args.output}")
        else:
            # Save with auto-generated filename
            filename = reporter.save_report(report)
            if filename:
                logger.info(f"Sentiment analysis report saved to {filename}")
        
        return True
