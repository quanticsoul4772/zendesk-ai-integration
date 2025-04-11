"""
View Hierarchy Parser Module

This module provides functionality to parse Zendesk views into a hierarchical structure
based on the naming convention using :: as a delimiter.
"""

import logging
from typing import Dict, List, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class ViewHierarchyParser:
    """
    Parses Zendesk views into a hierarchical structure based on the naming convention.
    
    This class analyzes view names that use a delimiter (::) to create a hierarchical
    structure that can be navigated through different levels.
    
    Example:
        "Support :: Pending Tickets" would be organized as:
        {
            "Support": {
                "_views": {
                    "Pending Tickets": 123456  # view ID
                }
            }
        }
    """
    
    def __init__(self, views: List, delimiter: str = "::"):
        """
        Initialize the ViewHierarchyParser with a list of Zendesk views.
        
        Args:
            views: List of Zendesk view objects
            delimiter: The delimiter used in view names (default: "::")
        """
        self.views = views
        self.delimiter = delimiter
        self.hierarchy = {}
        self._build_hierarchy()
        
    def _build_hierarchy(self) -> None:
        """
        Builds the view hierarchy by parsing view names.
        
        Analyzes each view's title to extract the hierarchical structure
        based on the delimiter.
        """
        if not self.views:
            logger.warning("No views provided to build hierarchy")
            return
            
        logger.info(f"Building view hierarchy from {len(self.views)} views")
        
        for view in self.views:
            # Skip views without titles
            if not hasattr(view, 'title') or not view.title:
                logger.warning(f"View {getattr(view, 'id', 'unknown')} has no title, skipping")
                continue
                
            # Split view name by delimiter
            parts = [p.strip() for p in view.title.split(self.delimiter)]
            
            # Navigate/build the hierarchy
            current = self.hierarchy
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # Add the leaf (actual view)
            leaf_name = parts[-1].strip()
            if "_views" not in current:
                current["_views"] = {}
            current["_views"][leaf_name] = view.id
            
        logger.info(f"Built hierarchy with {len(self.hierarchy)} top-level categories")
                
    def get_categories(self) -> List[str]:
        """
        Get top-level categories from the hierarchy.
        
        Returns:
            List of category names
        """
        # Get all keys except special _views key
        return [k for k in self.hierarchy.keys() if k != "_views"]
    
    def get_subcategories(self, path: List[str]) -> List[str]:
        """
        Get subcategories for a given path in the hierarchy.
        
        Args:
            path: List of category names forming a path in the hierarchy
            
        Returns:
            List of subcategory names
        """
        if not path:
            return self.get_categories()
            
        # Navigate to the specified path
        current = self.hierarchy
        for part in path:
            if part in current:
                current = current[part]
            else:
                logger.warning(f"Path part '{part}' not found in hierarchy")
                return []
                
        # Return all keys except special _views key
        return [k for k in current.keys() if k != "_views"]
    
    def get_views(self, path: List[str]) -> Dict[str, int]:
        """
        Get views for a given path in the hierarchy.
        
        Args:
            path: List of category names forming a path in the hierarchy
            
        Returns:
            Dictionary mapping view names to view IDs
        """
        # Navigate to the specified path
        current = self.hierarchy
        for part in path:
            if part in current:
                current = current[part]
            else:
                logger.warning(f"Path part '{part}' not found in hierarchy")
                return {}
                
        # Return views at this level
        return current.get("_views", {})
    
    def find_view_path(self, view_id: int) -> List[str]:
        """
        Find the path to a specific view by ID.
        
        Args:
            view_id: The ID of the view to find
            
        Returns:
            List of category names forming the path to the view
        """
        result = []
        
        def search_recursive(node, current_path):
            # Check if this node has views
            if "_views" in node:
                # Check each view at this level
                for name, vid in node["_views"].items():
                    if vid == view_id:
                        return current_path + [name]
            
            # Check subcategories
            for key, value in node.items():
                if key != "_views" and isinstance(value, dict):
                    path = search_recursive(value, current_path + [key])
                    if path:
                        return path
            
            return None
        
        result = search_recursive(self.hierarchy, [])
        return result or []
    
    def get_recently_used_views(self, recents: List[int], limit: int = 5) -> Dict[str, int]:
        """
        Get recently used views with their full names.
        
        Args:
            recents: List of recent view IDs
            limit: Maximum number of recent views to return
            
        Returns:
            Dictionary mapping full view names to view IDs
        """
        result = {}
        counter = 0
        
        for view in self.views:
            if hasattr(view, 'id') and view.id in recents:
                result[view.title] = view.id
                counter += 1
                if counter >= limit:
                    break
                    
        return result
