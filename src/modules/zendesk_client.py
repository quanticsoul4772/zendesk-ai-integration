"""
Zendesk Client Module

This module handles all interactions with the Zendesk API.
It's responsible for fetching tickets, views, and updating tickets.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv

# Import the cache manager
from modules.cache_manager import ZendeskCache

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables if not already loaded
load_dotenv()

class ZendeskClient:
    """Handles all interactions with the Zendesk API."""
    
    def __init__(self):
        """Initialize the Zendesk client using credentials from environment variables."""
        # Initialize cache system
        self.cache = ZendeskCache()
        
        # Initialize Zendesk client
        try:
            from zenpy import Zenpy
            from zenpy.lib.api_objects import Ticket, Comment, User, View
            
            # Get Zendesk credentials from environment
            email = os.getenv("ZENDESK_EMAIL")
            api_token = os.getenv("ZENDESK_API_TOKEN")
            subdomain = os.getenv("ZENDESK_SUBDOMAIN")
            
            if not all([email, api_token, subdomain]):
                logger.error("Zendesk credentials not found in environment variables.")
                raise ValueError("Zendesk credentials not configured.")
            
            # Create Zenpy client
            credentials = {
                'email': email,
                'token': api_token,
                'subdomain': subdomain
            }
            
            self.client = Zenpy(**credentials)
            logger.info("Zendesk client initialized successfully")
        except ImportError:
            logger.error("Zenpy package not installed. Install with: pip install zenpy>=2.0.24")
            raise

    def fetch_tickets(self, status="open", limit=None, filter_by=None):
        """
        Fetch tickets from Zendesk with the specified status.
        
        Args:
            status: Ticket status (open, new, pending, solved, closed, all)
            limit: Maximum number of tickets to fetch (None for all)
            filter_by: Dictionary of additional filters
            
        Returns:
            List of Zendesk tickets.
        """
        # Create a cache key based on the function parameters
        cache_key = f"tickets_{status}_{limit}_{str(filter_by)}"
        
        # Try to get from cache first
        cached_result = self.cache.get_tickets(cache_key)
        if cached_result is not None:
            logger.info(f"Using cached tickets with status: {status}")
            return cached_result
            
        logger.info(f"Fetching tickets with status: {status} (cache miss)")
        try:
            if filter_by and 'id' in filter_by:
                # Fetch a specific ticket by ID
                ticket = self.client.tickets(id=filter_by['id'])
                return [ticket] if ticket else []
            elif status.lower() == "all":
                # Fetch all tickets regardless of status
                tickets = list(self.client.tickets())
                logger.info(f"Fetched {len(tickets)} tickets with any status")
            elif limit:
                tickets = list(self.client.tickets(status=status))[:limit]
            else:
                tickets = list(self.client.tickets(status=status))
            
            # Filter out closed tickets if we're fetching open tickets
            # This is a safeguard in case Zendesk API returns closed tickets
            if status == "open":
                tickets = [t for t in tickets if hasattr(t, 'status') and t.status != 'closed']
                logger.info(f"Filtered out closed tickets, remaining: {len(tickets)}")
            
            logger.info(f"Fetched {len(tickets)} tickets with status: {status}")
            
            # Cache the results before returning
            self.cache.set_tickets(cache_key, tickets)
            return tickets
        except Exception as e:
            logger.exception(f"Error fetching tickets: {e}")
            return []

    def fetch_tickets_from_view(self, view_id, limit=None):
        """
        Fetch tickets from a specific Zendesk view.
        
        Args:
            view_id: ID of the Zendesk view
            limit: Maximum number of tickets to fetch (None for all)
        
        Returns:
            List of Zendesk tickets.
        """
        # Create a cache key
        cache_key = f"view_tickets_{view_id}_{limit}"
        
        # Try to get from cache first
        cached_result = self.cache.get_tickets(cache_key)
        if cached_result is not None:
            logger.info(f"Using cached tickets for view ID: {view_id}")
            return cached_result
            
        logger.info(f"Fetching tickets from view ID: {view_id} (cache miss)")
        
        # First check if the view exists
        try:
            # Validate if the view exists
            valid_views = self._validate_view_ids([view_id])
            if view_id not in valid_views:
                logger.warning(f"View ID {view_id} does not exist or is not accessible")
                return []
                
            # Fetch tickets from the view
            if limit:
                tickets = list(self.client.views.tickets(view_id))[:limit]
            else:
                tickets = list(self.client.views.tickets(view_id))
            
            # Filter out closed tickets to prevent update errors
            original_count = len(tickets)
            tickets = [t for t in tickets if hasattr(t, 'status') and t.status != 'closed']
            
            if original_count != len(tickets):
                logger.info(f"Filtered out {original_count - len(tickets)} closed tickets from view")
            
            logger.info(f"Fetched {len(tickets)} tickets from view ID: {view_id}")
            
            # Cache the results before returning
            self.cache.set_tickets(cache_key, tickets)
            return tickets
        except Exception as e:
            # Handle RecordNotFoundException specifically
            if "RecordNotFound" in str(e):
                logger.error(f"View ID {view_id} not found: {e}")
            else:
                logger.exception(f"Error fetching tickets from view: {e}")
            return []

    def fetch_tickets_from_multiple_views(self, view_ids, limit=None, status=None):
        """
        Fetch tickets from multiple Zendesk views.
        
        Args:
            view_ids: List of view IDs to fetch tickets from
            limit: Optional limit per view (None for all)
            status: Optional status filter
            
        Returns:
            Combined list of Zendesk tickets with view_id added to each ticket.
        """
        all_tickets = []
        ticket_ids_seen = set()  # To prevent duplicates
        
        # Create a cache key for views
        cache_key = "all_views"
        
        # Try to get views from cache first
        cached_views = self.cache.get_views(cache_key)
        if cached_views is not None:
            views = cached_views
            valid_view_ids = {view.id for view in views}
            logger.info(f"Using cached views, found {len(valid_view_ids)} available views")
        else:
            # Get all available views for validation if not in cache
            try:
                views = self.client.views()
                # Create a set of valid view IDs for fast lookup
                valid_view_ids = {view.id for view in views}
                logger.info(f"Found {len(valid_view_ids)} available views in Zendesk")
                
                # Cache the views
                self.cache.set_views(cache_key, views)
            
        except Exception as e:
            logger.error(f"Error fetching available views: {e}")
            # If we can't fetch views, return empty list
            return []
            
        # Check for invalid view IDs
        invalid_views = [view_id for view_id in view_ids if view_id not in valid_view_ids]
        if invalid_views:
            for view_id in invalid_views:
                logger.warning(f"View ID {view_id} does not exist or is not accessible")
        
        # Process only valid views
        valid_views = [view_id for view_id in view_ids if view_id in valid_view_ids]
        if not valid_views:
            logger.warning("None of the specified views exist or are accessible")
            return []
            
        logger.info(f"Processing {len(valid_views)} valid views out of {len(view_ids)} requested")
        
        for view_id in valid_views:
            logger.info(f"Fetching tickets from view ID: {view_id}")
            view_tickets = []
            
            try:
                if limit:
                    tickets = list(self.client.views.tickets(view_id))[:limit]
                else:
                    tickets = list(self.client.views.tickets(view_id))
                
                # Filter by status if specified
                if status and status.lower() != "all":
                    tickets = [t for t in tickets if hasattr(t, 'status') and t.status == status]
                    logger.info(f"Filtered by status '{status}', remaining: {len(tickets)} tickets")
                
                # Add view_id attribute to each ticket for tracking source
                for ticket in tickets:
                    if ticket.id not in ticket_ids_seen:
                        ticket_ids_seen.add(ticket.id)
                        # Store the view_id in a custom attribute
                        setattr(ticket, 'source_view_id', view_id)
                        view_tickets.append(ticket)
                
                logger.info(f"Fetched {len(view_tickets)} unique tickets from view ID: {view_id}")
                all_tickets.extend(view_tickets)
            except Exception as e:
                # Log the error but don't raise the exception to continue with other views
                logger.error(f"Error fetching tickets from view {view_id}: {e}")
        
        logger.info(f"Total unique tickets from all views: {len(all_tickets)}")
        return all_tickets

    def fetch_tickets_by_view_name(self, view_name, limit=None):
        """
        Fetch tickets from a specific Zendesk view by name.
        
        Args:
            view_name: Name of the Zendesk view
            limit: Maximum number of tickets to fetch (None for all)
        
        Returns:
            List of Zendesk tickets.
        """
        logger.info(f"Fetching tickets from view: {view_name}")
        try:
            # First, find the view by name
            views = self.client.views()
            view_id = None
            
            for view in views:
                if view.title.lower() == view_name.lower():
                    view_id = view.id
                    break
            
            if not view_id:
                # Try partial matching
                for view in views:
                    if view_name.lower() in view.title.lower():
                        view_id = view.id
                        logger.info(f"Found partial match: {view.title}")
                        break
            
            if view_id:
                logger.info(f"Found view ID {view_id} for {view_name}")
                return self.fetch_tickets_from_view(view_id, limit)
            else:
                logger.error(f"View not found: {view_name}")
                return []
        except Exception as e:
            logger.exception(f"Error fetching tickets by view name: {e}")
            return []

    def fetch_tickets_from_multiple_view_names(self, view_names, limit=None, status=None):
        """
        Fetch tickets from multiple Zendesk views using view names.
        
        Args:
            view_names: List of view names to fetch tickets from
            limit: Optional limit per view (None for all)
            status: Optional status filter
            
        Returns:
            Combined list of Zendesk tickets with view_id and view_name added to each ticket.
        """
        # First, resolve all view names to view IDs
        view_ids = []
        view_map = {}  # Map IDs to names for reference
        
        try:
            views = self.client.views()
            
            for view_name in view_names:
                found = False
                
                # Try exact match first
                for view in views:
                    if view.title.lower() == view_name.lower():
                        view_ids.append(view.id)
                        view_map[view.id] = view.title
                        logger.info(f"Found exact match for '{view_name}': ID {view.id}")
                        found = True
                        break
                
                # If no exact match, try partial match
                if not found:
                    for view in views:
                        if view_name.lower() in view.title.lower():
                            view_ids.append(view.id)
                            view_map[view.id] = view.title
                            logger.info(f"Found partial match for '{view_name}': '{view.title}' (ID {view.id})")
                            found = True
                            break
                
                if not found:
                    logger.warning(f"View '{view_name}' not found")
            
            # Now fetch tickets from all resolved view IDs
            tickets = self.fetch_tickets_from_multiple_views(view_ids, limit, status)
            
            # Add view_name attribute for each ticket based on the view_id
            for ticket in tickets:
                if hasattr(ticket, 'source_view_id'):
                    view_id = getattr(ticket, 'source_view_id')
                    setattr(ticket, 'source_view_name', view_map.get(view_id, "Unknown View"))
            
            return tickets
            
        except Exception as e:
            logger.exception(f"Error fetching tickets from multiple view names: {e}")
            return []

    def get_view_names_by_ids(self, view_ids):
        """
        Get a mapping of view IDs to their names.
        
        Args:
            view_ids: List of view IDs
            
        Returns:
            Dictionary mapping view IDs to view names
        """
        # Create a cache key
        cache_key = f"view_names_{','.join(str(id) for id in view_ids)}"
        
        # Try to get from cache first
        cached_map = self.cache.get_views(cache_key)
        if cached_map is not None:
            return cached_map
            
        view_map = {}
        
        try:
            # Try to get all views from cache first
            cached_views = self.cache.get_views("all_views")
            if cached_views is not None:
                views = cached_views
            else:
                views = self.client.views()
                # Cache all views for future use
                self.cache.set_views("all_views", views)
            
            for view in views:
                if view.id in view_ids:
                    view_map[view.id] = view.title
            
            # Cache the mapping
            self.cache.set_views(cache_key, view_map)
            return view_map
        except Exception as e:
            logger.exception(f"Error getting view names by IDs: {e}")
            return {}

    def _validate_view_ids(self, view_ids):
        """
        Validates which view IDs exist and are accessible.
        
        Args:
            view_ids: List of view IDs to validate
            
        Returns:
            Set of valid view IDs that exist
        """
        valid_views = set()
        
        try:
            # Try to get from cache first
            cached_views = self.cache.get_views("all_views")
            if cached_views is not None:
                all_views = cached_views
            else:
                # Get all available views if not in cache
                all_views = self.client.views()
                # Cache the views
                self.cache.set_views("all_views", all_views)
                
            all_view_ids = {view.id for view in all_views}
            
            # Check which of the provided view IDs exist
            for view_id in view_ids:
                if view_id in all_view_ids:
                    valid_views.add(view_id)
                else:
                    logger.warning(f"View ID {view_id} does not exist or is not accessible")
            
            return valid_views
        except Exception as e:
            logger.error(f"Error validating view IDs: {e}")
            return set()
            
    def list_all_views(self):
        """
        List all available Zendesk views with their IDs and titles.
        
        Returns:
            Formatted string with view IDs and names.
        """
        # Create a cache key for the formatted view list
        cache_key = "formatted_view_list"
        
        # Try to get from cache first
        cached_list = self.cache.get_views(cache_key)
        if cached_list is not None:
            return cached_list
            
        try:
            # Try to get views from cache
            cached_views = self.cache.get_views("all_views")
            if cached_views is not None:
                views = cached_views
            else:
                views = self.client.views()
                # Cache the views
                self.cache.set_views("all_views", views)
                
            view_list = "\nZENDESK VIEWS\n============\n\nID\t\tName\n--\t\t----\n"
            
            for view in sorted(views, key=lambda v: v.title):
                view_list += f"{view.id}\t\t{view.title}\n"
                
            # Cache the formatted list
            self.cache.set_views(cache_key, view_list)
            return view_list
        except Exception as e:
            logger.exception(f"Error fetching views: {e}")
            return f"Error fetching views: {str(e)}"
    
    def add_ticket_tags(self, ticket, tags):
        """
        Add tags to a Zendesk ticket.
        
        Args:
            ticket: Zendesk ticket object
            tags: List of tags to add
        
        Returns:
            Boolean indicating success
        """
        if not tags:
            return False
        
        # Check if tag updates are disabled globally
        if os.getenv("DISABLE_TAG_UPDATES", "").lower() == "true":
            logger.info(f"Tag updates disabled by configuration. Would have added tags to ticket {ticket.id}: {tags}")
            return True
        
        # Skip closed tickets as they cannot be updated in Zendesk
        if hasattr(ticket, 'status') and ticket.status == 'closed':
            logger.warning(f"Skipping tag update for ticket {ticket.id} because it is closed")
            return False
        
        try:
            # Add new tags to existing tags
            current_tags = ticket.tags or []
            new_tags = list(set(current_tags + tags))
            
            # Only update if tags have changed
            if set(new_tags) != set(current_tags):
                ticket.tags = new_tags
                self.client.tickets.update(ticket)
                logger.info(f"Updated tags for ticket {ticket.id}: {new_tags}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding tags to ticket {ticket.id}: {e}")
            return False

    def add_private_comment(self, ticket, comment_text):
        """
        Add a private comment to a Zendesk ticket.
        
        Args:
            ticket: Zendesk ticket object
            comment_text: Text for the comment
        
        Returns:
            Boolean indicating success
        """
        # Skip closed tickets as they cannot be updated in Zendesk
        if hasattr(ticket, 'status') and ticket.status == 'closed':
            logger.warning(f"Skipping comment update for ticket {ticket.id} because it is closed")
            return False
            
        try:
            from zenpy.lib.api_objects import Comment
            ticket.comment = Comment(body=comment_text, public=False)
            self.client.tickets.update(ticket)
            logger.info(f"Added private comment to ticket {ticket.id}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment to ticket {ticket.id}: {e}")
            return False
