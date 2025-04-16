"""
Base Reporter Module

This module provides base functionality for all report generators.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class BaseReporter:
    """Base class for all reporter modules."""
    
    def __init__(self):
        """Initialize the base reporter."""
        self.report_name = "Base Report"
    
    def generate_report(self, *args, **kwargs):
        """Generate a report. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate_report")
    
    def output(self, content: str, file_path: Optional[str] = None) -> None:
        """
        Output report content to console or file.
        
        Args:
            content: The content to output
            file_path: Optional file path to write content to
        """
        # Print to console
        print(content)
        
        # Write to file if specified
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Report written to {file_path}")
            except Exception as e:
                logger.error(f"Error writing report to file: {e}")
    
    def _calculate_time_period(self, days: int = 30, view: Optional[str] = None, 
                              views: Optional[List[str]] = None, 
                              zendesk_client = None) -> Tuple[datetime, str]:
        """
        Calculate the time period for the report.
        
        Args:
            days: Number of days to look back
            view: Optional view ID to include in the description
            views: Optional list of view IDs to include in the description
            zendesk_client: Zendesk client for looking up view names
            
        Returns:
            Tuple of (start_date, time_period_description)
        """
        # Calculate start date
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Generate description
        if view and zendesk_client:
            # Get view information
            view_obj = self._get_view_by_id_or_name(view, zendesk_client)
            if view_obj:
                return start_date, f"the last {days} days in view '{view_obj.title}'"
        
        elif views and zendesk_client:
            # Get view names
            view_names = []
            for view_id in views:
                view_obj = self._get_view_by_id_or_name(view_id, zendesk_client)
                if view_obj:
                    view_names.append(view_obj.title)
            
            if view_names:
                view_list = "', '".join(view_names)
                return start_date, f"the last {days} days in views: '{view_list}'"
        
        # Default description
        return start_date, f"the last {days} days"
    
    def _get_view_by_id_or_name(self, id_or_name: str, zendesk_client) -> Optional[Any]:
        """
        Get a view by ID or name.
        
        Args:
            id_or_name: The view ID or name
            zendesk_client: Zendesk client to use for lookup
            
        Returns:
            The view object or None if not found
        """
        # Try getting by ID first
        view = zendesk_client.get_view_by_id(id_or_name)
        
        # If not found and has get_view_by_name method, try by name
        if view is None and hasattr(zendesk_client, 'get_view_by_name'):
            view = zendesk_client.get_view_by_name(id_or_name)
            
        # If still not found and numeric ID, try one more time with integer ID
        if view is None and id_or_name.isdigit():
            try:
                view = zendesk_client.get_view_by_id(int(id_or_name))
            except (ValueError, TypeError):
                pass
                
        return view
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format a timestamp for output.
        
        Args:
            timestamp: The timestamp to format
            
        Returns:
            Formatted timestamp string
        """
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_percentage(self, value: float) -> str:
        """
        Format a value as a percentage.
        
        Args:
            value: The value to format (0.0 to 1.0)
            
        Returns:
            Formatted percentage string
        """
        return f"{value * 100:.1f}%"
    
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
    
    def _create_report_header(self) -> str:
        """
        Create a standard report header.
        
        Returns:
            Report header string
        """
        now = datetime.utcnow()
        header = [
            f"=== {self.report_name} ===",
            f"Generated: {self._format_timestamp(now)}",
            "=" * (len(self.report_name) + 8),
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
