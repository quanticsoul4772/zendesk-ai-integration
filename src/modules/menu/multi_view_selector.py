"""
Multi-View Selector Module

This module provides an enhanced menu system that allows selecting multiple views
for batch operations and offers detailed status information about ticket content.
"""

import os
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class MultiViewSelector:
    """
    Enhanced view selection system that allows selecting multiple views
    and provides detailed status information about view contents.
    """
    
    def __init__(self, zendesk_client, db_repository=None):
        """
        Initialize the MultiViewSelector.
        
        Args:
            zendesk_client: Instance of ZendeskClient for API interactions
            db_repository: Optional database repository for analysis data
        """
        self.zendesk_client = zendesk_client
        self.db_repository = db_repository
        
        # Initialize ticket status cache with more detailed information
        # Format: {view_id: {'total': count, 'pending': count, 'open': count, etc.}}
        self._view_status_cache = {}
        
        # List of currently selected views
        self.selected_views = set()
        
        logger.info("Initializing MultiViewSelector")
        
    def _get_views(self):
        """Get all views from Zendesk."""
        try:
            views = list(self.zendesk_client.fetch_views())
            logger.info(f"Fetched {len(views)} views from Zendesk")
            return views
        except Exception as e:
            logger.error(f"Error fetching views: {e}")
            return []
        
    def _check_view_content(self, view_id: int, check_detailed: bool = False) -> Dict[str, int]:
        """
        Check ticket counts and statuses for a view.
        
        Args:
            view_id: ID of the view to check
            check_detailed: Whether to check detailed status counts
            
        Returns:
            Dict with ticket counts by status
        """
        # Initialize result with zeros
        result = {
            'total': 0,
            'open': 0,
            'pending': 0,
            'solved': 0,
            'closed': 0,
            'new': 0
        }
        
        try:
            # First get total ticket count
            tickets = self.zendesk_client.fetch_tickets_from_view(view_id, limit=100)
            result['total'] = len(tickets)
            
            # If detailed check requested and there are tickets, count by status
            if check_detailed and result['total'] > 0:
                for ticket in tickets:
                    status = getattr(ticket, 'status', 'unknown')
                    if status in result:
                        result[status] += 1
                    
            # Cache the result
            self._view_status_cache[view_id] = result
            logger.debug(f"View {view_id} has {result['total']} tickets, {result.get('pending', 0)} pending")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking view {view_id} content: {e}")
            return result
            
    def display_view_selector(self, message: str = "Select views:") -> Tuple[List[int], List[str]]:
        """
        Display an interactive view selector with multiple selection support.
        
        Args:
            message: Message to display above the selector
            
        Returns:
            Tuple of (list of selected view IDs, list of selected view names)
        """
        # Get views from Zendesk
        views = self._get_views()
        
        # Create mapping of view names to IDs
        view_map = {view.title: view.id for view in views if hasattr(view, 'title') and hasattr(view, 'id')}
        
        # Check for content if not already cached
        for view_id in view_map.values():
            if view_id not in self._view_status_cache:
                self._check_view_content(view_id)
        
        # Create menu options
        menu_options = []
        
        # Sort views into categories
        categorized_views = self._categorize_views(views)
        
        print("\n" + "=" * 50)
        print(f"{message}")
        print("=" * 50)
        print("Select multiple views using numbers (e.g. 1,3,5-7)")
        print("Enter 'all' to select all views")
        print("Enter 'clear' to clear selection")
        print("Enter 'done' when finished selecting")
        print("-" * 50)
        
        # Display categories and views
        option_num = 1
        option_map = {}
        
        for category, category_views in categorized_views.items():
            print(f"\n{category}:")
            
            for view_name, view_id in category_views:
                # Get status indicators
                status_info = self._view_status_cache.get(view_id, {'total': 0})
                
                # Format status information
                if status_info['total'] == 0:
                    status_str = "[Empty]"
                else:
                    ticket_count = status_info['total']
                    pending_count = status_info.get('pending', 0)
                    
                    if pending_count > 0:
                        status_str = f"[{ticket_count} total, {pending_count} pending]"
                    else:
                        status_str = f"[{ticket_count} tickets]"
                
                # Show selected status
                selected = "*" if view_id in self.selected_views else " "
                
                # Display option
                print(f"  {selected} {option_num}. {view_name} {status_str}")
                
                # Map option number to view
                option_map[option_num] = (view_id, view_name)
                option_num += 1
        
        print("\nCurrent selection: ", end="")
        if self.selected_views:
            selected_view_names = [name for (id, name) in option_map.values() if id in self.selected_views]
            print(", ".join(selected_view_names))
        else:
            print("None")
        
        # Loop until selection is complete
        while True:
            choice = input("\nSelect views (or 'done'): ").strip().lower()
            
            if choice == 'done':
                break
                
            elif choice == 'all':
                self.selected_views = set(view_id for view_id, _ in option_map.values())
                print(f"Selected all {len(self.selected_views)} views")
                
            elif choice == 'clear':
                self.selected_views.clear()
                print("Cleared all selections")
                
            else:
                try:
                    # Parse comma-separated selection with ranges
                    parts = choice.split(',')
                    for part in parts:
                        part = part.strip()
                        
                        if '-' in part:
                            # Handle range (e.g., "5-8")
                            start, end = part.split('-')
                            start, end = int(start), int(end)
                            
                            for num in range(start, end + 1):
                                if num in option_map:
                                    view_id, _ = option_map[num]
                                    self.selected_views.add(view_id)
                        else:
                            # Handle single number
                            num = int(part)
                            if num in option_map:
                                view_id, _ = option_map[num]
                                self.selected_views.add(view_id)
                    
                    # Show current selection
                    selected_view_names = [name for (id, name) in option_map.values() if id in self.selected_views]
                    print(f"Current selection: {', '.join(selected_view_names)}")
                    
                except ValueError:
                    print("Invalid selection. Use numbers, ranges (e.g., 1-3), or commands (all, clear, done)")
        
        # Return selected views
        selected_view_ids = list(self.selected_views)
        selected_view_names = [name for (_id, name) in option_map.values() if _id in self.selected_views]
        
        return selected_view_ids, selected_view_names
        
    def _categorize_views(self, views) -> Dict[str, List[Tuple[str, int]]]:
        """
        Organize views into categories based on their names.
        
        Args:
            views: List of view objects
            
        Returns:
            Dict mapping categories to lists of (view_name, view_id) tuples
        """
        # Initialize result with "Uncategorized" category
        result = {"Uncategorized": []}
        
        for view in views:
            if hasattr(view, 'title') and hasattr(view, 'id'):
                name = view.title
                view_id = view.id
                
                # Parse category from name (e.g., "Support :: Pending" -> "Support")
                if " :: " in name:
                    category, _ = name.split(" :: ", 1)
                else:
                    category = "Uncategorized"
                
                # Add category if it doesn't exist
                if category not in result:
                    result[category] = []
                
                # Add view to category
                result[category].append((name, view_id))
        
        # Sort views within each category
        for category in result:
            result[category].sort(key=lambda x: x[0])
            
        return result
    
    def refresh_view_status(self, view_ids: List[int] = None, check_detailed: bool = True):
        """
        Refresh status information for specified views.
        
        Args:
            view_ids: List of view IDs to refresh. If None, refresh all cached views.
            check_detailed: Whether to check detailed status counts
        """
        if view_ids is None:
            view_ids = list(self._view_status_cache.keys())
        
        print(f"\nRefreshing status for {len(view_ids)} views...")
        
        for i, view_id in enumerate(view_ids):
            progress = (i + 1) / len(view_ids) * 100
            print(f"\rProgress: {progress:.1f}% ({i+1}/{len(view_ids)})", end="")
            
            self._check_view_content(view_id, check_detailed)
        
        print(f"\nRefreshed status for {len(view_ids)} views")
    
    def generate_multi_view_report(self, selected_view_ids: List[int], report_type: str, 
                                 ai_analyzer=None, report_modules=None):
        """
        Generate a report for multiple selected views.
        
        Args:
            selected_view_ids: List of view IDs to include in the report
            report_type: Type of report to generate ('sentiment', 'pending', 'enhanced')
            ai_analyzer: AI analyzer for sentiment analysis if needed
            report_modules: Dict of report modules for report generation
        """
        # Ensure we have necessary components
        if report_type in ('sentiment', 'enhanced') and ai_analyzer is None:
            print("\nAI Analyzer not available. Cannot generate sentiment reports.")
            return
            
        if report_modules is None or not report_modules:
            print("\nReport modules not available. Cannot generate reports.")
            return
            
        # Map selected views to names
        views = self._get_views()
        view_map = {view.id: view.title for view in views if hasattr(view, 'id') and hasattr(view, 'title')}
        
        # Get list of view names for display
        selected_view_names = [view_map.get(view_id, f"View {view_id}") for view_id in selected_view_ids]
        
        print(f"\nGenerating {report_type} report for {len(selected_view_ids)} views:")
        print("- " + "\n- ".join(selected_view_names))
        
        # Different report types have different workflows
        if report_type == 'pending':
            # For pending report, prepare view name to ID mapping
            view_name_map = {view_map[view_id]: view_id for view_id in selected_view_ids if view_id in view_map}
            
            # Check if we have the pending reporter module
            if 'pending' not in report_modules:
                print("\nPending reporter module not available.")
                return
                
            reporter = report_modules['pending']
            
            print("\nFetching tickets for multiple views... This may take a while.")
            
            # Format current time for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"multi_view_pending_report_{timestamp}.txt"
            
            # Generate multi-view report
            report = reporter.generate_multi_view_report(
                {name: self.zendesk_client.fetch_tickets_by_view_name(name) for name in view_name_map.keys()},
                db_repository=self.db_repository
            )
            
            # Save report
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            
            # Display report
            print("\n" + report)
            print(f"\nReport saved to: {filename}")
            
        elif report_type in ('sentiment', 'enhanced'):
            # For sentiment/enhanced reports, we need to analyze tickets
            # For first implementation, we'll use the batch processing approach
            
            # Determine which AI model to use (default to Claude)
            use_claude = True
            use_enhanced = (report_type == 'enhanced')
            
            # Get the appropriate reporter
            if use_enhanced:
                if 'sentiment_enhanced' not in report_modules:
                    print("\nEnhanced sentiment reporter module not available.")
                    return
                reporter = report_modules['sentiment_enhanced']
            else:
                if 'sentiment' not in report_modules:
                    print("\nSentiment reporter module not available.")
                    return
                reporter = report_modules['sentiment']
            
            print("\nFetching and analyzing tickets from multiple views... This may take a while.")
            
            # Fetch tickets from multiple views
            all_tickets = []
            for view_id in selected_view_ids:
                view_name = view_map.get(view_id, f"View {view_id}")
                print(f"\nFetching tickets from {view_name}...")
                
                tickets = self.zendesk_client.fetch_tickets_from_view(view_id)
                for ticket in tickets:
                    # Add view info to ticket for tracking
                    setattr(ticket, 'source_view_id', view_id)
                    setattr(ticket, 'source_view_name', view_name)
                
                all_tickets.extend(tickets)
                
                # Update status cache with actual ticket count
                if view_id in self._view_status_cache:
                    self._view_status_cache[view_id]['total'] = len(tickets)
                
            if not all_tickets:
                print("\nNo tickets found in selected views.")
                return
                
            print(f"\nAnalyzing {len(all_tickets)} tickets from {len(selected_view_ids)} views...")
            
            # Batch analyze tickets
            analyses = ai_analyzer.analyze_tickets_batch(all_tickets, use_claude=use_claude)
            
            # Add view information to each analysis and save to database
            for analysis in analyses:
                # Find matching ticket
                for ticket in all_tickets:
                    if ticket.id == analysis['ticket_id']:
                        # Add view information
                        analysis['source_view_id'] = getattr(ticket, 'source_view_id', None)
                        analysis['source_view_name'] = getattr(ticket, 'source_view_name', "Unknown")
                        break
                
                # Save to database if available
                if self.db_repository:
                    self.db_repository.save_analysis(analysis)
            
            # Generate the combined report
            print("\nGenerating combined report...")
            
            # Format for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"multi_view_{report_type}_report_{timestamp}.txt"
            
            # Create a view mapping for the report
            view_name_map = {view_id: view_map.get(view_id, f"View {view_id}") for view_id in selected_view_ids}
            
            # Generate the report
            title = f"Multi-View {report_type.capitalize()} Analysis Report"
            report = self._generate_multi_view_report(analyses, view_name_map, title, reporter)
            
            # Save report
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            
            # Display report
            print("\n" + report)
            print(f"\nReport saved to: {filename}")
    
    def _generate_multi_view_report(self, analyses, view_map, title, reporter):
        """
        Generate a multi-view report using the appropriate reporter.
        
        Args:
            analyses: List of analysis results
            view_map: Mapping of view IDs to names
            title: Report title
            reporter: Reporter module to use
            
        Returns:
            Generated report as string
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
        report += f"MULTI-VIEW ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
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
        report += "COMBINED ANALYSIS\n----------------\n"
        try:
            # Use reporter's generate_report method if available
            if hasattr(reporter, 'generate_report'):
                view_report = reporter.generate_report(analyses)
                
                # Skip the header part if it exists (usually first 60 chars)
                if len(view_report) > 61:
                    report += view_report[61:]
                else:
                    report += view_report
            else:
                report += "Report generation not supported by the selected reporter.\n"
        except Exception as e:
            report += f"Error generating combined report: {str(e)}\n"
        
        # Per-view analysis
        report += "\nPER-VIEW ANALYSIS\n-----------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}")
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            
            # Get ticket details per view
            if hasattr(reporter, '_count_sentiment_polarities'):
                # Get sentiment distribution
                polarity_counts = reporter._count_sentiment_polarities(view_tickets)
                report += "Sentiment Distribution:\n"
                for polarity, count in sorted(polarity_counts.items()):
                    report += f"  {polarity}: {count}\n"
            
            # Get priority distribution if available
            if hasattr(reporter, '_count_priority_range'):
                high_priority = reporter._count_priority_range(view_tickets, 7, 10)
                report += f"High Priority Tickets (7-10): {high_priority}\n"
            elif hasattr(reporter, '_count_priority_scores'):
                priority_counts = reporter._count_priority_scores(view_tickets)
                high_priority = sum(count for score, count in priority_counts.items() if score >= 7)
                report += f"High Priority Tickets (7-10): {high_priority}\n"
            
            # Get business impact if available
            if hasattr(reporter, '_count_business_impact'):
                business_impact_count = reporter._count_business_impact(view_tickets)
                report += f"Business Impact Tickets: {business_impact_count}\n"
            
            # Calculate averages if available
            if hasattr(reporter, '_calculate_average_urgency'):
                avg_urgency = reporter._calculate_average_urgency(view_tickets)
                report += f"Average Urgency: {avg_urgency:.2f}/5\n"
                
            if hasattr(reporter, '_calculate_average_frustration'):
                avg_frustration = reporter._calculate_average_frustration(view_tickets)
                report += f"Average Frustration: {avg_frustration:.2f}/5\n"
                
            if hasattr(reporter, '_calculate_average_priority'):
                avg_priority = reporter._calculate_average_priority(view_tickets)
                report += f"Average Priority: {avg_priority:.2f}/10\n"
        
        return report
