"""
Reporter Base Module

Provides common reporter functionality shared by all reporter types.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)

class ReporterBase:
    """
    Base class for all reporters providing common functionality.
    """
    
    def __init__(self):
        """Initialize the reporter base class."""
        self.output_file = None
    
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
            
        return None
    
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
