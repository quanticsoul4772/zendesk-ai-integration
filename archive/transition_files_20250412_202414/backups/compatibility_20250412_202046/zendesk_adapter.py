"""
Zendesk Client Adapter

This module provides an adapter that presents a ZendeskClient interface
but uses the ZendeskRepository implementation internally.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from src.domain.interfaces.repository_interfaces import TicketRepository, ViewRepository
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository

# Set up logging
logger = logging.getLogger(__name__)


class ZendeskClientAdapter:
    """
    Adapter that presents a ZendeskClient interface but uses ZendeskRepository internally.
    
    This adapter helps with the transition from the legacy ZendeskClient to the
    new ZendeskRepository implementation.
    """
    
    def __init__(self, repository=None):
        """
        Initialize the adapter.
        
        Args:
            repository: Optional ZendeskRepository instance (will create one if not provided)
        """
        self._repository = repository or ZendeskRepository()
        
        # For backward compatibility, expose the client directly
        self.client = self._repository.client
        
        # For backward compatibility, expose the cache
        self.cache = self._repository.cache
        
        logger.debug("ZendeskClientAdapter initialized - using ZendeskRepository internally")
    
    def fetch_tickets(self, status="open", limit=None, filter_by=None):
        """
        Fetch tickets from Zendesk.
        
        Args:
            status: Ticket status (open, new, pending, solved, closed, all)
            limit: Maximum number of tickets to fetch
            filter_by: Optional filter criteria
            
        Returns:
            List of tickets
        """
        logger.debug(f"ZendeskClientAdapter.fetch_tickets called with status={status}, limit={limit}")
        
        if filter_by and isinstance(filter_by, dict) and "id" in filter_by:
            # If filtering by ID, use get_ticket
            ticket = self._repository.get_ticket(filter_by["id"])
            return [ticket] if ticket else []
        
        return self._repository.get_tickets(status, limit)
    
    def fetch_tickets_from_view(self, view_id, limit=None):
        """
        Fetch tickets from a specific view.
        
        Args:
            view_id: ID of the view to fetch tickets from
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of tickets
        """
        logger.debug(f"ZendeskClientAdapter.fetch_tickets_from_view called with view_id={view_id}, limit={limit}")
        
        return self._repository.get_tickets_from_view(view_id, limit)
    
    def fetch_tickets_by_view_name(self, view_name, limit=None):
        """
        Fetch tickets from a view by name.
        
        Args:
            view_name: Name of the view to fetch tickets from
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of tickets
        """
        logger.debug(f"ZendeskClientAdapter.fetch_tickets_by_view_name called with view_name={view_name}, limit={limit}")
        
        return self._repository.get_tickets_from_view_name(view_name, limit)
    
    def fetch_tickets_from_multiple_views(self, view_ids, limit=None, status=None):
        """
        Fetch tickets from multiple views.
        
        Args:
            view_ids: List of view IDs to fetch tickets from
            limit: Maximum number of tickets per view
            status: Optional status filter
            
        Returns:
            List of tickets
        """
        logger.debug(f"ZendeskClientAdapter.fetch_tickets_from_multiple_views called with {len(view_ids)} views, limit={limit}")
        
        return self._repository.get_tickets_from_multiple_views(view_ids, limit)
    
    def fetch_tickets_from_multiple_view_names(self, view_names, limit=None, status=None):
        """
        Fetch tickets from multiple views by name.
        
        Args:
            view_names: List of view names to fetch tickets from
            limit: Maximum number of tickets per view
            status: Optional status filter
            
        Returns:
            List of tickets
        """
        logger.debug(f"ZendeskClientAdapter.fetch_tickets_from_multiple_view_names called with {len(view_names)} views, limit={limit}")
        
        all_tickets = []
        for view_name in view_names:
            tickets = self.fetch_tickets_by_view_name(view_name, limit)
            all_tickets.extend(tickets)
        
        return all_tickets
    
    def add_ticket_tags(self, ticket_id, tags):
        """
        Add tags to a ticket.
        
        Args:
            ticket_id: ID of the ticket to update
            tags: List of tags to add
            
        Returns:
            Success indicator
        """
        logger.debug(f"ZendeskClientAdapter.add_ticket_tags called for ticket {ticket_id} with {len(tags)} tags")
        
        return self._repository.add_ticket_tags(ticket_id, tags)
    
    def add_ticket_comment(self, ticket_id, comment, public=False):
        """
        Add a comment to a ticket.
        
        Args:
            ticket_id: ID of the ticket to update
            comment: Comment text
            public: Whether the comment should be public
            
        Returns:
            Success indicator
        """
        logger.debug(f"ZendeskClientAdapter.add_ticket_comment called for ticket {ticket_id}, public={public}")
        
        return self._repository.add_ticket_comment(ticket_id, comment, public)
    
    def list_all_views(self):
        """
        Get a formatted string of all available views.
        
        Returns:
            Formatted string of views
        """
        logger.debug("ZendeskClientAdapter.list_all_views called")
        
        views = self._repository.get_all_views()
        
        # Format the views in a way that matches the legacy format
        result = "Available Zendesk Views:\n"
        result += "=====================\n\n"
        
        for idx, view in enumerate(views, 1):
            result += f"{idx}. {view['title']} (ID: {view['id']})\n"
        
        return result
    
    def get_view_names_by_ids(self, view_ids):
        """
        Get a mapping of view IDs to their names.
        
        Args:
            view_ids: List of view IDs
            
        Returns:
            Dictionary mapping view IDs to view names
        """
        logger.debug(f"ZendeskClientAdapter.get_view_names_by_ids called with {len(view_ids)} IDs")
        
        return self._repository.get_view_names_by_ids(view_ids)
    
    def get_view_by_name(self, view_name):
        """
        Get a view by name.
        
        Args:
            view_name: Name of the view to fetch
            
        Returns:
            View object or None if not found
        """
        logger.debug(f"ZendeskClientAdapter.get_view_by_name called with name={view_name}")
        
        return self._repository.get_view_by_name(view_name)
