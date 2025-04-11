"""
Breadcrumb Navigation Module

This module provides functionality to maintain and display navigation breadcrumbs
for the interactive menu system.
"""

import logging
from typing import List, Optional

# Set up logging
logger = logging.getLogger(__name__)

class BreadcrumbTrail:
    """
    Maintains and displays navigation breadcrumbs.
    
    This class keeps track of the user's navigation path through the menu system
    and provides a formatted string representation for display.
    """
    
    def __init__(self, home_label: str = "Home"):
        """
        Initialize the BreadcrumbTrail.
        
        Args:
            home_label: Label for the home/root level (default: "Home")
        """
        self.trail = []
        self.home_label = home_label
        logger.debug("Initialized breadcrumb trail")
        
    def add(self, item: str) -> None:
        """
        Add an item to the breadcrumb trail.
        
        Args:
            item: The menu item/label to add to the trail
        """
        if item:
            self.trail.append(item)
            logger.debug(f"Added '{item}' to breadcrumb trail")
        
    def pop(self) -> Optional[str]:
        """
        Remove and return the last item from the breadcrumb trail.
        
        Returns:
            The last item in the trail or None if the trail is empty
        """
        if self.trail:
            item = self.trail.pop()
            logger.debug(f"Removed '{item}' from breadcrumb trail")
            return item
        logger.debug("Attempted to pop from empty breadcrumb trail")
        return None
        
    def clear(self) -> None:
        """
        Clear the entire breadcrumb trail.
        """
        self.trail = []
        logger.debug("Cleared breadcrumb trail")
        
    def get_path(self) -> List[str]:
        """
        Get the current path as a list of strings.
        
        Returns:
            List of items in the breadcrumb trail
        """
        return self.trail.copy()
        
    def get_formatted(self, separator: str = " > ") -> str:
        """
        Get a formatted string representation of the breadcrumb trail.
        
        Args:
            separator: The separator to use between breadcrumb items (default: " > ")
            
        Returns:
            Formatted breadcrumb string
        """
        if not self.trail:
            return self.home_label
        return separator.join([self.home_label] + self.trail)
        
    def __str__(self) -> str:
        """
        String representation of the breadcrumb trail.
        
        Returns:
            Formatted breadcrumb string
        """
        return self.get_formatted()
        
    def __len__(self) -> int:
        """
        Get the length of the breadcrumb trail.
        
        Returns:
            Number of items in the trail
        """
        return len(self.trail)
