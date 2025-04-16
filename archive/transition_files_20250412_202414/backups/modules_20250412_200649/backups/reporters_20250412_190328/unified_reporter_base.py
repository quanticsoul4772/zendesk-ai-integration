"""
Unified Reporter Base Module

Provides common reporter functionality shared by all reporter types.
Consolidates functionality from BaseReporter and ReporterBase.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)

class UnifiedReporterBase:
    """
    Base class for all reporters providing common functionality.
    This class consolidates BaseReporter and ReporterBase.
    """
    
    def __init__(self):
        """Initialize the reporter base class."""
        self.report_name = "Base Report"
        self.output_file = None
    
    def generate_report(self, *args, **kwargs):
        """Generate a report. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate_report")
    
    def output(self, content: str, output_file: Optional[str] = None) -> None:
        """
        Output content to console and/or file.
        
        Args:
            content: String content to output
            output_file: Optional file path to write content to
        """
        # Print to console
        print(content)
        
        # Write to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Report written to {output_file}")
            except Exception as e:
                logger.error(f"Error writing report to file: {e}")
    
    def save_report(self, report, output_file=None):
        """
        Save a report to file.
        
        Args:
            report: Report content to save
            output_file: Output file path (optional, will generate if not specified)
            
        Returns:
            The path to the saved file
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_file = f"{self.report_name.lower().replace(' ', '_')}_{timestamp}.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"Report saved to {output_file}")
        return output_file
    
    def _calculate_time_period(self, days: Optional[int] = None, 
                              view: Optional[str] = None,
                              views: Optional[List[str]] = None,
                              zendesk_client: Any = None) -> Tuple[datetime, str]:
        """
        Calculate the start date and human-readable time period description.
        
        Args:
            days: Number of days to look back (optional)
            view: View ID or name to include in description (optional)
            views: List of view IDs to include in description (optional)
            zendesk_client: ZendeskClient to resolve view names (optional)
            
        Returns:
            Tuple of (start_date, time_period_description)
        """
        # Current time as the end point
        now = datetime.utcnow()
        
        # Start date based on days parameter or default to 7 days
        if days:
            start_date = now - timedelta(days=days)
            time_desc = f"the last {days} days"
        else:
            # Default to last 7 days
            start_date = now - timedelta(days=7)
            time_desc = "the last 7 days"
        
        # Add view information if provided
        if view and zendesk_client:
            # Try to get view object to show the title
            view_obj = self._get_view_by_id_or_name(view, zendesk_client)
            if view_obj and hasattr(view_obj, 'title'):
                time_desc += f" for view '{view_obj.title}'"
            else:
                time_desc += f" for view '{view}'"
        elif view:
            time_desc += f" for view '{view}'"
        elif views:
            # Get view names for multiple views
            view_names = []
            if zendesk_client:
                for view_id in views:
                    view_obj = self._get_view_by_id_or_name(view_id, zendesk_client)
                    if view_obj and hasattr(view_obj, 'title'):
                        view_names.append(view_obj.title)
            
            if view_names:
                if len(view_names) == 1:
                    time_desc += f" for view '{view_names[0]}'"
                else:
                    view_list = "', '".join(view_names)
                    time_desc += f" for views: '{view_list}'"
            else:
                if len(views) == 1:
                    time_desc += f" for view ID {views[0]}"
                else:
                    time_desc += f" for {len(views)} views"
                
        return start_date, time_desc
    
    def _get_view_by_id_or_name(self, view_id_or_name: str, zendesk_client: Any) -> Any:
        """
        Get a view by ID or name.
        
        Args:
            view_id_or_name: View ID or name
            zendesk_client: ZendeskClient instance
            
        Returns:
            Zendesk view object or None if not found
        """
        # Try as ID first
        try:
            view_id = view_id_or_name
            if hasattr(zendesk_client, 'get_view_by_id'):
                return zendesk_client.get_view_by_id(view_id)
            elif hasattr(zendesk_client, 'get_view'):
                return zendesk_client.get_view(view_id)
        except (ValueError, AttributeError):
            # Not a valid ID or method not found, try as name
            pass
            
        # Look up by name
        try:
            if hasattr(zendesk_client, 'get_view_by_name'):
                return zendesk_client.get_view_by_name(view_id_or_name)
        except AttributeError:
            # Fall back to fetch_tickets_by_view_name method
            pass
            
        # Try one more time with integer ID if needed
        if str(view_id_or_name).isdigit():
            try:
                view = zendesk_client.get_view_by_id(int(view_id_or_name))
                if view:
                    return view
            except (ValueError, TypeError, AttributeError):
                pass
                
        return None
    
    def _lookup_view_name(self, view_id: str, zendesk_client) -> str:
        """
        Look up a view name from its ID. Includes caching to prevent repeated lookups.
        
        Args:
            view_id: The view ID to look up
            zendesk_client: Zendesk client to use for lookup
            
        Returns:
            View name or the original ID if not found
        """
        # Check if the client has a cache
        if hasattr(zendesk_client, 'cache'):
            # Try to get from cache first
            cache_key = f"view-name-{view_id}"
            view_name = zendesk_client.cache.get_views(cache_key)
            if view_name:
                return view_name
        
        # If not in cache, look up the view
        view = self._get_view_by_id_or_name(view_id, zendesk_client)
        if view:
            view_name = view.title
            
            # Store in cache if available
            if hasattr(zendesk_client, 'cache'):
                zendesk_client.cache.set_views(f"view-name-{view_id}", view_name)
                
            return view_name
        
        # If all else fails, return the original ID
        return str(view_id)
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format a timestamp for display.
        
        Args:
            timestamp: Datetime object
            
        Returns:
            Formatted timestamp string
        """
        if not timestamp:
            return "Unknown time"
            
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_percentage(self, value: float, total: Optional[float] = None, 
                         decimal_places: int = 1) -> str:
        """
        Format a value as a percentage.
        
        Args:
            value: Numeric value
            total: Total value (if value is not already a percentage)
            decimal_places: Number of decimal places to show
            
        Returns:
            Formatted percentage string
        """
        if total is not None and total > 0:
            percentage = (value / total) * 100
        else:
            # If value is already a ratio between 0-1, convert to percentage
            if 0 <= value <= 1:
                percentage = value * 100
            else:
                # Assume it's already a percentage value
                percentage = value
            
        return f"{percentage:.{decimal_places}f}%"
    
    def _format_count(self, count: int) -> str:
        """
        Format a count for output.
        
        Args:
            count: The count to format
            
        Returns:
            Formatted count string
        """
        return f"{count:,}"
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format a duration in seconds.
        
        Args:
            seconds: The duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def _create_report_header(self, title: Optional[str] = None) -> str:
        """
        Create a standard report header.
        
        Args:
            title: Optional title to override report_name
            
        Returns:
            Report header string
        """
        now = datetime.utcnow()
        report_title = title or self.report_name
        header = [
            f"{'='*60}",
            f"{report_title.upper()} ({now.strftime('%Y-%m-%d %H:%M')})",
            f"{'='*60}",
            ""
        ]
        return "\n".join(header)
    
    def _create_report_footer(self) -> str:
        """
        Create a standard report footer.
        
        Returns:
            Report footer string
        """
        footer = [
            "",
            "=" * 50,
            "End of Report",
            "=" * 50
        ]
        return "\n".join(footer)
