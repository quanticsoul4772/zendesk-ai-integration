"""
Breadcrumb Module

This module provides backward compatibility for the breadcrumb module.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)


class BreadcrumbTrail:
    """
    Legacy breadcrumb trail class.
    
    This is a compatibility stub that delegates to the new implementation.
    """
    
    def __init__(self):
        """Initialize the breadcrumb trail."""
        logger.debug("BreadcrumbTrail initialized (compatibility mode)")
        self.trail = []
    
    def add(self, name, data=None):
        """
        Add a breadcrumb to the trail.
        
        Args:
            name: Breadcrumb name
            data: Optional breadcrumb data
        """
        logger.debug(f"Adding breadcrumb {name} (compatibility mode)")
        self.trail.append((name, data))
    
    def pop(self):
        """
        Remove the last breadcrumb from the trail.
        
        Returns:
            The removed breadcrumb
        """
        if self.trail:
            breadcrumb = self.trail.pop()
            logger.debug(f"Popped breadcrumb {breadcrumb[0]} (compatibility mode)")
            return breadcrumb
        return None
    
    def get_trail(self):
        """
        Get the breadcrumb trail.
        
        Returns:
            List of breadcrumbs
        """
        return self.trail
    
    def clear(self):
        """Clear the breadcrumb trail."""
        logger.debug("Clearing breadcrumb trail (compatibility mode)")
        self.trail = []
