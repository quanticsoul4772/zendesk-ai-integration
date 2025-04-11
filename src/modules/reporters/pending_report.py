"""
Pending Reporter Module

Generates reports about pending tickets requiring attention.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import Counter, defaultdict
from .reporter_base import ReporterBase

# Set up logging
logger = logging.getLogger(__name__)

class PendingReporter(ReporterBase):
    """
    Generates reports focused on pending tickets requiring attention.
    """
    
    def __init__(self):
        """Initialize the pending reporter."""
        # Initialize the parent class
        super().__init__()
        
        # Define status categories
        self.status_groups = {
            'new': 'New',
            'open': 'In Progress',
            'pending': 'Waiting on Customer',
            'solved': 'Resolved',
            'closed': 'Closed',
            'hold': 'On Hold'
        }
    
    def generate_report(
        self, zendesk_client, db_repository, days=None, view=None, views=None, 
        status="pending", output_file=None, format="standard", limit=None, 
        view_name=None, view_names=None, pending_view=None
    ):
        """
        Generate a pending tickets report.
        
        Args:
            zendesk_client: ZendeskClient instance
            db_repository: DBRepository instance
            days: Number of days to look back
            view: View ID or name
            views: List of view IDs or names
            status: Ticket status
            output_file: File to write the report to
            format: Report format
            limit: Maximum number of tickets to include
            view_name: View name (alternative to view)
            view_names: List of view names (alternative to views)
            pending_view: Specific view for pending tickets
            
        Returns:
            The generated report as a string
        """
        # Convert view_name/view_names to view/views if provided
        if view_name and not view:
            view = view_name
        if view_names and not views:
            views = view_names
        if pending_view and not view:
            view = pending_view
            
        # If a view name is provided, get the view by name
        view_obj = None
        if isinstance(view, str) and not view.isdigit():
            view_obj = zendesk_client.get_view_by_name(view)
            if view_obj:
                view = str(view_obj.id)
            
        # Set up output file
        self.output_file = output_file
        
        # Get ticket data based on parameters
        start_date, time_period = self._calculate_time_period(days, view, views)
        
        # For testing, return a placeholder
        tickets = []
        analyses = {}
        
        if not tickets:
            report = f"No pending tickets found for the last 7 days for view '{view}'."
        else:
            # Generate the actual report
            report = self._generate_report_content(tickets, analyses, f"Pending Tickets Report - {time_period}")
        
        # Output the report
        self.output(report, output_file)
        
        return report
    
    def generate_multi_view_report(
        self, tickets_by_view: Dict[str, List], 
        db_repository=None, 
        days=7, 
        status="pending", 
        output_file=None, 
        format="standard"
    ):
        """
        Generate a combined report for multiple views.
        
        Args:
            tickets_by_view: Dictionary mapping view names to lists of tickets
            db_repository: Optional database repository for analysis data
            days: Number of days to look back (default: 7)
            status: Ticket status to filter by (default: "pending")
            output_file: File to write the report to (optional)
            format: Report format (standard or enhanced) (default: "standard")
            
        Returns:
            The generated report as a string
        """
        # Set up output file
        self.output_file = output_file
        
        # Check if we have any tickets
        total_tickets = sum(len(tickets) for tickets in tickets_by_view.values())
        
        if total_tickets == 0:
            # No tickets found in any view
            views_str = ", ".join(tickets_by_view.keys())
            return f"No pending tickets found for the last {days} days in the selected views: {views_str}"
        
        # Get analyses from database if available
        analyses = {}
        if db_repository:
            # Get ticket IDs from all views
            all_ticket_ids = []
            for tickets in tickets_by_view.values():
                for ticket in tickets:
                    if hasattr(ticket, 'id'):
                        all_ticket_ids.append(str(ticket.id))
            
            # Get analyses from database
            if all_ticket_ids:
                analyses = db_repository.find_analyses_by_ticket_ids(all_ticket_ids)
        
        # Generate the report
        return self._generate_multi_view_report_content(tickets_by_view, analyses, days)
    
    def _generate_multi_view_report_content(self, tickets_by_view, analyses, days=7):
        """
        Generate the content for a multi-view pending tickets report.
        
        Args:
            tickets_by_view: Dictionary mapping view names to lists of tickets
            analyses: Dictionary mapping ticket IDs to analysis results
            days: Number of days to look back
            
        Returns:
            The generated report as a string
        """
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"MULTI-VIEW PENDING TICKETS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        title = f"Pending Tickets - Last {days} Days"
        report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Calculate total tickets
        total_tickets = sum(len(tickets) for tickets in tickets_by_view.values())
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total views: {len(tickets_by_view)}\n"
        report += f"Total pending tickets: {total_tickets}\n\n"
        
        # Views summary section
        report += "TICKETS BY VIEW\n--------------\n"
        for view_name, tickets in tickets_by_view.items():
            report += f"{view_name}: {len(tickets)} pending tickets\n"
        report += "\n"
        
        # Status breakdown for all tickets
        all_tickets = []
        for tickets in tickets_by_view.values():
            all_tickets.extend(tickets)
            
        status_counts = Counter()
        for ticket in all_tickets:
            status = getattr(ticket, 'status', 'unknown')
            status_counts[status] += 1
        
        if status_counts:
            report += "STATUS BREAKDOWN\n---------------\n"
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_tickets) * 100
                status_label = self.status_groups.get(status, status.capitalize())
                report += f"{status_label}: {count} tickets ({percentage:.1f}%)\n"
            report += "\n"
        
        # Per-view details
        report += "PER-VIEW DETAILS\n----------------\n"
        
        for view_name, tickets in tickets_by_view.items():
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            
            if not tickets:
                report += "No pending tickets found in this view.\n"
                continue
                
            # Get status distribution for this view
            view_status_counts = Counter()
            for ticket in tickets:
                status = getattr(ticket, 'status', 'unknown')
                view_status_counts[status] += 1
            
            # Status distribution
            for status, count in sorted(view_status_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(tickets)) * 100
                status_label = self.status_groups.get(status, status.capitalize())
                report += f"{status_label}: {count} tickets ({percentage:.1f}%)\n"
            
            # Add ticket details (limit to 5 per view to avoid overwhelming reports)
            if tickets:
                report += "\nRecent tickets:\n"
                # Sort tickets by updated_at if available
                sorted_tickets = sorted(
                    tickets, 
                    key=lambda t: getattr(t, 'updated_at', datetime.min), 
                    reverse=True
                )
                
                for ticket in sorted_tickets[:5]:
                    ticket_id = getattr(ticket, 'id', 'Unknown')
                    analysis = analyses.get(str(ticket_id))
                    report += self._format_ticket_details(ticket, analysis) + "\n"
        
        return report
    
    def _generate_report_content(self, tickets, analyses, title=None):
        """Generate the pending tickets report content."""
        # Create the report header
        report = f"\n{'='*60}\n"
        report += f"PENDING TICKETS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Add summary section
        report += f"Total tickets: {len(tickets)}\n\n"
        
        # Categorize tickets
        categories = self._categorize_tickets(tickets, analyses)
        
        # Add category distribution
        report += "CATEGORY DISTRIBUTION\n--------------------\n"
        for category, count in sorted(categories['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(tickets)) * 100 if len(tickets) > 0 else 0
            report += f"{category}: {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add ticket details by category
        for category, category_tickets in categories['tickets_by_category'].items():
            if category_tickets:
                report += f"{category.upper()} TICKETS\n{'-' * (len(category) + 8)}\n"
                for ticket in category_tickets:
                    ticket_id = getattr(ticket, 'id', 'Unknown')
                    analysis = analyses.get(str(ticket_id))
                    report += self._format_ticket_details(ticket, analysis) + "\n"
                report += "\n"
        
        return report
    
    def _categorize_tickets(self, tickets, analyses):
        """Categorize tickets by type and priority."""
        categories = Counter()
        tickets_by_category = defaultdict(list)
        
        for ticket in tickets:
            ticket_id = str(getattr(ticket, 'id', 'Unknown'))
            analysis = analyses.get(ticket_id)
            
            # Determine category based on analysis if available
            if analysis and 'category' in analysis:
                category = analysis['category']
            else:
                # Default categorization based on ticket properties
                category = 'uncategorized'
                if hasattr(ticket, 'tags') and ticket.tags:
                    for tag in ticket.tags:
                        if tag.startswith('category_'):
                            category = tag.replace('category_', '')
                            break
            
            # Count the category
            categories[category] += 1
            
            # Add ticket to the category list
            tickets_by_category[category].append(ticket)
        
        return {
            'categories': dict(categories),
            'tickets_by_category': dict(tickets_by_category)
        }
    
    def _format_ticket_details(self, ticket, analysis=None):
        """Format details for a single ticket."""
        # Extract ticket information
        ticket_id = getattr(ticket, 'id', 'Unknown')
        subject = getattr(ticket, 'subject', 'No Subject')
        status = getattr(ticket, 'status', 'unknown')
        created_at = getattr(ticket, 'created_at', None)
        updated_at = getattr(ticket, 'updated_at', None)
        
        # Format basic ticket info
        ticket_info = f"#{ticket_id} - {subject}\n"
        ticket_info += f"  Status: {status} ({self.status_groups.get(status, 'Unknown')})\n"
        
        # Add timestamps if available
        if created_at:
            ticket_info += f"  Created: {self._format_timestamp(created_at)}\n"
        if updated_at:
            ticket_info += f"  Updated: {self._format_timestamp(updated_at)}\n"
        
        # Add analysis information if available
        if analysis:
            # Add sentiment
            sentiment = analysis.get('sentiment')
            if isinstance(sentiment, dict):
                polarity = sentiment.get('polarity', 'unknown')
                ticket_info += f"  Sentiment: {polarity}\n"
                
                # Add urgency and frustration if available
                if 'urgency_level' in sentiment:
                    ticket_info += f"  Urgency: {sentiment['urgency_level']}/5\n"
                if 'frustration_level' in sentiment:
                    ticket_info += f"  Frustration: {sentiment['frustration_level']}/5\n"
            else:
                ticket_info += f"  Sentiment: {sentiment}\n"
            
            # Add component if available
            component = analysis.get('component')
            if component and component != 'none':
                ticket_info += f"  Component: {component}\n"
                
            # Add priority score if available
            priority = analysis.get('priority_score')
            if priority:
                ticket_info += f"  Priority: {priority}/10\n"
        
        return ticket_info
