"""
View Hierarchy Module

This module provides backward compatibility for the view hierarchy module.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)


class ViewHierarchyParser:
    """
    Legacy view hierarchy parser class.
    
    This is a compatibility stub that delegates to the new implementation.
    """
    
    def __init__(self):
        """Initialize the parser."""
        logger.debug("ViewHierarchyParser initialized (compatibility mode)")
    
    def parse_view_hierarchy(self, views_data):
        """
        Parse view hierarchy from views data.
        
        Args:
            views_data: Views data to parse
            
        Returns:
            Parsed view hierarchy
        """
        logger.debug("Parsing view hierarchy (compatibility mode)")
        
        # Import here to avoid circular imports
        from src.presentation.cli.commands.list_views_command import ViewHierarchyFormatter
        
        formatter = ViewHierarchyFormatter()
        return formatter.format_hierarchy(views_data)
