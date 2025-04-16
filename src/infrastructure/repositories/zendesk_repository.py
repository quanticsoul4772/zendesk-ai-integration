"""
Zendesk Repository Implementation

This module provides an implementation of the TicketRepository and ViewRepository interfaces
using the Zendesk API.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, cast
from datetime import datetime, timedelta

from src.domain.entities.ticket import Ticket
from src.domain.value_objects.ticket_status import TicketStatus
from src.domain.interfaces.repository_interfaces import TicketRepository, ViewRepository
from src.domain.exceptions import EntityNotFoundError, ConnectionError, QueryError

from src.infrastructure.utils.retry import with_retry
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCacheManager

# Set up logging
logger = logging.getLogger(__name__)


class ZendeskRepository(TicketRepository, ViewRepository):
    """
    Implementation of the TicketRepository and ViewRepository interfaces using the Zendesk API.
    
    This repository uses the Zenpy library to interact with the Zendesk API and provides
    caching to reduce API calls.
    """
    
    def __init__(self, zenpy_client=None, cache_manager=None):
        """
        Initialize the Zendesk repository.
        
        Args:
            zenpy_client: Optional pre-configured Zenpy client
            cache_manager: Optional cache manager
        """
        self.client = zenpy_client or self._create_zenpy_client()
        self.cache = cache_manager or ZendeskCacheManager()
        
        # Check if we have a valid client
        self._check_client_connection()
    
    def _create_zenpy_client(self):
        """
        Create a new Zenpy client using environment variables.
        
        Returns:
            Zenpy client instance
            
        Raises:
            ConnectionError: If credentials are missing or invalid
        """
        try:
            from zenpy import Zenpy
            
            # Get Zendesk credentials from environment
            email = os.getenv("ZENDESK_EMAIL")
            api_token = os.getenv("ZENDESK_API_TOKEN")
            subdomain = os.getenv("ZENDESK_SUBDOMAIN")
            
            if not all([email, api_token, subdomain]):
                raise ConnectionError("Zendesk credentials not found in environment variables")
            
            # Create Zenpy client
            credentials = {
                'email': email,
                'token': api_token,
                'subdomain': subdomain
            }
            
            return Zenpy(**credentials)
        except ImportError:
            logger.error("Zenpy package not installed. Install with: pip install zenpy>=2.0.24")
            raise ConnectionError("Zenpy package not installed")
        except Exception as e:
            logger.error(f"Failed to create Zenpy client: {str(e)}")
            raise ConnectionError(f"Failed to create Zenpy client: {str(e)}")
    
    def _check_client_connection(self):
        """
        Check if the client connection works by making a simple API call.
        
        Raises:
            ConnectionError: If the connection fails
        """
        try:
            # Try a simple API call to check if the connection works
            _ = self.client.users.me()
            logger.info("Successfully connected to Zendesk API")
        except Exception as e:
            logger.error(f"Zendesk API connection test failed: {str(e)}")
            raise ConnectionError(f"Failed to connect to Zendesk API: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: ID of the ticket to fetch
            
        Returns:
            Ticket entity or None if not found
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        cache_key = f"ticket_{ticket_id}"
        
        # Try to get from cache first
        cached_ticket = self.cache.get_ticket(cache_key)
        if cached_ticket is not None:
            logger.debug(f"Cache hit for ticket {ticket_id}")
            return cached_ticket
        
        logger.info(f"Fetching ticket with ID: {ticket_id}")
        
        try:
            zendesk_ticket = self.client.tickets(id=ticket_id)
            
            if not zendesk_ticket:
                logger.warning(f"Ticket with ID {ticket_id} not found")
                return None
            
            # Convert to domain entity
            ticket = Ticket.from_zendesk_ticket(zendesk_ticket)
            
            # Cache the result
            self.cache.set_ticket(cache_key, ticket)
            
            return ticket
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error fetching ticket {ticket_id}: {error_str}")
            
            if "RecordNotFound" in error_str:
                # Handle non-existent ticket with a more specific error
                error_message = f"Ticket {ticket_id} does not exist or is not accessible. Please verify the ticket ID."
                logger.error(error_message)
                raise EntityNotFoundError(error_message)
            elif "connection" in error_str.lower() or "timeout" in error_str.lower():
                raise ConnectionError(f"Connection error while fetching ticket {ticket_id}: {error_str}")
            else:
                raise QueryError(f"Error fetching ticket {ticket_id}: {error_str}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_tickets(self, status: str = "open", limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets with the specified status.
        
        Args:
            status: Ticket status (open, new, pending, solved, closed, all)
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of ticket entities
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        # Normalize status
        normalized_status = status.lower()
        cache_key = f"tickets_{normalized_status}_{limit}"
        
        # Try to get from cache first
        cached_tickets = self.cache.get_tickets(cache_key)
        if cached_tickets is not None:
            logger.debug(f"Cache hit for tickets with status: {normalized_status}")
            return cached_tickets
        
        logger.info(f"Fetching tickets with status: {normalized_status}")
        
        try:
            if normalized_status == "all":
                if limit:
                    zendesk_tickets = list(self.client.tickets())[:limit]
                else:
                    zendesk_tickets = list(self.client.tickets())
            else:
                if limit:
                    zendesk_tickets = list(self.client.tickets(status=normalized_status))[:limit]
                else:
                    zendesk_tickets = list(self.client.tickets(status=normalized_status))
            
            # Convert to domain entities
            tickets = [Ticket.from_zendesk_ticket(t) for t in zendesk_tickets]
            
            # Cache the result
            self.cache.set_tickets(cache_key, tickets)
            
            logger.info(f"Fetched {len(tickets)} tickets with status: {normalized_status}")
            return tickets
        except Exception as e:
            logger.error(f"Error fetching tickets: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching tickets: {str(e)}")
            else:
                raise QueryError(f"Error fetching tickets: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_tickets_from_view(self, view_id: int, limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from a specific view.
        
        Args:
            view_id: ID of the view to fetch tickets from
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of ticket entities
            
        Raises:
            ConnectionError: If the API connection fails
            EntityNotFoundError: If the view does not exist
            QueryError: If the query fails for another reason
        """
        cache_key = f"view_tickets_{view_id}_{limit}"
        
        # Try to get from cache first
        cached_tickets = self.cache.get_tickets(cache_key)
        if cached_tickets is not None:
            logger.debug(f"Cache hit for view ID: {view_id}")
            return cached_tickets
        
        logger.info(f"Fetching tickets from view ID: {view_id}")
        
        try:
            # Validate if the view exists
            valid_views = self._validate_view_ids([view_id])
            if view_id not in valid_views:
                logger.warning(f"View ID {view_id} does not exist or is not accessible")
                raise EntityNotFoundError(f"View ID {view_id} does not exist or is not accessible")
            
            # Fetch tickets from the view
            if limit:
                zendesk_tickets = list(self.client.views.tickets(view_id))[:limit]
            else:
                zendesk_tickets = list(self.client.views.tickets(view_id))
            
            # Filter out closed tickets to prevent update errors
            zendesk_tickets = [t for t in zendesk_tickets if hasattr(t, 'status') and t.status != 'closed']
            
            # Convert to domain entities
            tickets = []
            for zendesk_ticket in zendesk_tickets:
                # Set source view info
                zendesk_ticket.source_view_id = view_id
                
                # Get view name if available
                view_map = self.get_view_names_by_ids([view_id])
                if view_id in view_map:
                    zendesk_ticket.source_view_name = view_map[view_id]
                
                ticket = Ticket.from_zendesk_ticket(zendesk_ticket)
                tickets.append(ticket)
            
            # Cache the result
            self.cache.set_tickets(cache_key, tickets)
            
            logger.info(f"Fetched {len(tickets)} tickets from view ID: {view_id}")
            return tickets
        except Exception as e:
            logger.error(f"Error fetching tickets from view: {str(e)}")
            
            if "RecordNotFound" in str(e):
                raise EntityNotFoundError(f"View ID {view_id} not found: {str(e)}")
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching tickets from view: {str(e)}")
            else:
                raise QueryError(f"Error fetching tickets from view: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_tickets_from_view_name(self, view_name: str, limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from a view by name.
        
        Args:
            view_name: Name of the view to fetch tickets from
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of ticket entities
            
        Raises:
            ConnectionError: If the API connection fails
            EntityNotFoundError: If the view does not exist
            QueryError: If the query fails for another reason
        """
        logger.info(f"Fetching tickets from view: {view_name}")
        
        try:
            # First, find the view by name
            view = self.get_view_by_name(view_name)
            
            if not view:
                logger.error(f"View not found: {view_name}")
                raise EntityNotFoundError(f"View not found: {view_name}")
            
            # Then fetch tickets from the view
            return self.get_tickets_from_view(view['id'], limit)
        except EntityNotFoundError:
            # Re-raise EntityNotFoundError
            raise
        except Exception as e:
            logger.error(f"Error fetching tickets by view name: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching tickets by view name: {str(e)}")
            else:
                raise QueryError(f"Error fetching tickets by view name: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_tickets_from_multiple_views(self, view_ids: List[int], limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from multiple views.
        
        Args:
            view_ids: List of view IDs to fetch tickets from
            limit: Maximum number of tickets per view
            
        Returns:
            List of ticket entities
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        all_tickets = []
        ticket_ids_seen = set()  # To prevent duplicates
        
        # Create a cache key for views
        cache_key = f"tickets_from_views_{'_'.join(str(id) for id in view_ids)}_{limit}"
        
        # Try to get from cache first
        cached_tickets = self.cache.get_tickets(cache_key)
        if cached_tickets is not None:
            logger.debug(f"Cache hit for multiple views: {view_ids}")
            return cached_tickets
        
        logger.info(f"Fetching tickets from {len(view_ids)} views")
        
        try:
            # Force refresh the views cache to ensure we have fresh data
            self.cache.force_refresh_views()
            
            # Get view names for better reporting
            view_map = self.get_view_names_by_ids(view_ids)
            
            # Validate view IDs
            valid_view_ids = self._validate_view_ids(view_ids)
            if not valid_view_ids:
                logger.warning("None of the specified views exist or are accessible")
                return []
            
            logger.info(f"Processing {len(valid_view_ids)} valid views out of {len(view_ids)} requested")
            
            for view_id in valid_view_ids:
                logger.info(f"Fetching tickets from view ID: {view_id}")
                view_tickets = []
                
                try:
                    if limit:
                        zendesk_tickets = list(self.client.views.tickets(view_id))[:limit]
                    else:
                        zendesk_tickets = list(self.client.views.tickets(view_id))
                    
                    # Add source view info to each ticket
                    for zendesk_ticket in zendesk_tickets:
                        if zendesk_ticket.id not in ticket_ids_seen:
                            ticket_ids_seen.add(zendesk_ticket.id)
                            
                            # Set source view info
                            zendesk_ticket.source_view_id = view_id
                            if view_id in view_map:
                                zendesk_ticket.source_view_name = view_map[view_id]
                            
                            # Convert to domain entity
                            ticket = Ticket.from_zendesk_ticket(zendesk_ticket)
                            view_tickets.append(ticket)
                    
                    logger.info(f"Fetched {len(view_tickets)} unique tickets from view ID: {view_id}")
                    all_tickets.extend(view_tickets)
                except Exception as e:
                    # Log the error but don't raise to continue with other views
                    logger.error(f"Error fetching tickets from view {view_id}: {str(e)}")
            
            # Cache the combined results
            if all_tickets:
                self.cache.set_tickets(cache_key, all_tickets)
            
            logger.info(f"Total unique tickets from all views: {len(all_tickets)}")
            return all_tickets
        except Exception as e:
            logger.error(f"Error fetching tickets from multiple views: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching tickets from multiple views: {str(e)}")
            else:
                raise QueryError(f"Error fetching tickets from multiple views: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def add_ticket_tags(self, ticket_id: int, tags: List[str]) -> bool:
        """
        Add tags to a ticket.
        
        Args:
            ticket_id: ID of the ticket to update
            tags: List of tags to add
            
        Returns:
            Success indicator
            
        Raises:
            ConnectionError: If the API connection fails
            EntityNotFoundError: If the ticket does not exist
            QueryError: If the query fails for another reason
        """
        if not tags:
            logger.info(f"No tags to add to ticket {ticket_id}")
            return True
        
        # Check if tag updates are disabled globally
        if os.getenv("DISABLE_TAG_UPDATES", "").lower() == "true":
            logger.info(f"Tag updates disabled by configuration. Would have added tags to ticket {ticket_id}: {tags}")
            return True
        
        logger.info(f"Adding tags to ticket {ticket_id}: {tags}")
        
        try:
            # Get the ticket
            zendesk_ticket = self.client.tickets(id=ticket_id)
            
            if not zendesk_ticket:
                logger.warning(f"Ticket with ID {ticket_id} not found")
                raise EntityNotFoundError(f"Ticket with ID {ticket_id} not found")
            
            # Skip closed tickets as they cannot be updated in Zendesk
            if hasattr(zendesk_ticket, 'status') and zendesk_ticket.status == 'closed':
                logger.warning(f"Skipping tag update for ticket {ticket_id} because it is closed")
                return False
            
            # Add new tags to existing tags
            current_tags = zendesk_ticket.tags or []
            new_tags = list(set(current_tags + tags))
            
            # Only update if tags have changed
            if set(new_tags) != set(current_tags):
                zendesk_ticket.tags = new_tags
                self.client.tickets.update(zendesk_ticket)
                logger.info(f"Updated tags for ticket {ticket_id}: {new_tags}")
                
                # Invalidate cache for this ticket
                self.cache.invalidate_ticket(str(ticket_id))
                
                return True
            
            logger.info(f"No new tags to add to ticket {ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding tags to ticket {ticket_id}: {str(e)}")
            
            if "RecordNotFound" in str(e):
                raise EntityNotFoundError(f"Ticket with ID {ticket_id} not found: {str(e)}")
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while adding tags to ticket: {str(e)}")
            else:
                raise QueryError(f"Error adding tags to ticket: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def add_ticket_comment(self, ticket_id: int, comment: str, public: bool = False) -> bool:
        """
        Add a comment to a ticket.
        
        Args:
            ticket_id: ID of the ticket to update
            comment: Comment text
            public: Whether the comment should be public
            
        Returns:
            Success indicator
            
        Raises:
            ConnectionError: If the API connection fails
            EntityNotFoundError: If the ticket does not exist
            QueryError: If the query fails for another reason
        """
        if not comment:
            logger.info(f"No comment to add to ticket {ticket_id}")
            return True
        
        logger.info(f"Adding {'public' if public else 'private'} comment to ticket {ticket_id}")
        
        try:
            # Get the ticket
            zendesk_ticket = self.client.tickets(id=ticket_id)
            
            if not zendesk_ticket:
                logger.warning(f"Ticket with ID {ticket_id} not found")
                raise EntityNotFoundError(f"Ticket with ID {ticket_id} not found")
            
            # Skip closed tickets as they cannot be updated in Zendesk
            if hasattr(zendesk_ticket, 'status') and zendesk_ticket.status == 'closed':
                logger.warning(f"Skipping comment for ticket {ticket_id} because it is closed")
                return False
            
            # Import Comment class dynamically to avoid circular imports
            from zenpy.lib.api_objects import Comment
            
            # Add the comment
            zendesk_ticket.comment = Comment(body=comment, public=public)
            self.client.tickets.update(zendesk_ticket)
            
            logger.info(f"Added {'public' if public else 'private'} comment to ticket {ticket_id}")
            
            # Invalidate cache for this ticket
            self.cache.invalidate_ticket(str(ticket_id))
            
            return True
        except Exception as e:
            logger.error(f"Error adding comment to ticket {ticket_id}: {str(e)}")
            
            if "RecordNotFound" in str(e):
                raise EntityNotFoundError(f"Ticket with ID {ticket_id} not found: {str(e)}")
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while adding comment to ticket: {str(e)}")
            else:
                raise QueryError(f"Error adding comment to ticket: {str(e)}")
    
    # ViewRepository interface implementation
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_all_views(self) -> List[Dict[str, Any]]:
        """
        Get all available views.
        
        Returns:
            List of view objects
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        cache_key = "all_views"
        
        # Try to get from cache first
        cached_views = self.cache.get_views(cache_key)
        if cached_views is not None:
            logger.debug("Cache hit for all views")
            return cached_views
        
        logger.info("Fetching all views")
        
        try:
            zendesk_views = list(self.client.views())
            
            # Convert to dictionaries
            views = [self._convert_view_to_dict(view) for view in zendesk_views]
            
            # Cache the result
            self.cache.set_views(cache_key, views)
            
            logger.info(f"Fetched {len(views)} views")
            return views
        except Exception as e:
            logger.error(f"Error fetching views: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching views: {str(e)}")
            else:
                raise QueryError(f"Error fetching views: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_view_by_id(self, view_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a view by ID.
        
        Args:
            view_id: ID of the view to fetch
            
        Returns:
            View object or None if not found
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        cache_key = f"view_{view_id}"
        
        # Try to get from cache first
        cached_view = self.cache.get_views(cache_key)
        if cached_view is not None:
            logger.debug(f"Cache hit for view ID: {view_id}")
            return cached_view
        
        logger.info(f"Fetching view with ID: {view_id}")
        
        try:
            view = self.client.views(id=view_id)
            
            if not view:
                logger.warning(f"View with ID {view_id} not found")
                return None
            
            # Convert to dictionary
            view_dict = self._convert_view_to_dict(view)
            
            # Cache the result
            self.cache.set_views(cache_key, view_dict)
            
            return view_dict
        except Exception as e:
            logger.error(f"Error fetching view by ID {view_id}: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching view: {str(e)}")
            else:
                raise QueryError(f"Error fetching view: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_view_by_name(self, view_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a view by name.
        
        Args:
            view_name: Name of the view to fetch
            
        Returns:
            View object or None if not found
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        logger.info(f"Fetching view with name: {view_name}")
        
        try:
            # Get all views
            views = self.get_all_views()
            
            # Step 1: Try exact match (case-insensitive)
            for view in views:
                if view.get('title', '').lower() == view_name.lower():
                    logger.info(f"Found exact match for view name: {view_name}")
                    return view
            
            # Step 2: Try partial match with path components
            # For example, "Support :: Pending Support" should match both the full string
            # and the rightmost component "Pending Support"
            view_name_parts = [part.strip() for part in view_name.split('::')] 
            if len(view_name_parts) > 1:
                # Try to match the rightmost component
                rightmost_part = view_name_parts[-1].lower()
                for view in views:
                    view_title = view.get('title', '')
                    if '::' in view_title:
                        view_parts = [part.strip() for part in view_title.split('::')] 
                        if len(view_parts) > 0 and view_parts[-1].lower() == rightmost_part:
                            logger.info(f"Found match on rightmost component for view name: {view_name} -> {view_title}")
                            return view
            
            # Step 3: Try partial match with view name as substring
            best_match = None
            best_match_score = 0
            
            for view in views:
                view_title = view.get('title', '').lower()
                
                # Exact title contains
                if view_name.lower() in view_title:
                    match_score = len(view_name) / len(view_title) if len(view_title) > 0 else 0
                    if match_score > best_match_score:
                        best_match = view
                        best_match_score = match_score
                # Or vice versa
                elif view_title in view_name.lower():
                    match_score = len(view_title) / len(view_name) if len(view_name) > 0 else 0
                    if match_score > best_match_score:
                        best_match = view
                        best_match_score = match_score
            
            if best_match:
                logger.info(f"Found partial match: {best_match.get('title')} (score: {best_match_score:.2f})")
                return best_match
            
            logger.warning(f"View with name {view_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching view by name {view_name}: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while fetching view by name: {str(e)}")
            else:
                raise QueryError(f"Error fetching view by name: {str(e)}")
    
    @with_retry(max_retries=3, retry_on=Exception)
    def get_view_names_by_ids(self, view_ids: List[int]) -> Dict[int, str]:
        """
        Get a mapping of view IDs to their names.
        
        Args:
            view_ids: List of view IDs
            
        Returns:
            Dictionary mapping view IDs to view names
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        if not view_ids:
            return {}
        
        cache_key = f"view_names_{','.join(str(id) for id in view_ids)}"
        
        # Try to get from cache first
        cached_map = self.cache.get_views(cache_key)
        if cached_map is not None:
            logger.debug(f"Cache hit for view names mapping: {view_ids}")
            return cached_map
        
        logger.info(f"Fetching names for {len(view_ids)} views")
        
        try:
            # Get all views
            all_views = self.get_all_views()
            
            # Create mapping of IDs to names
            view_map = {}
            for view in all_views:
                view_id = view.get('id')
                if view_id in view_ids:
                    view_map[view_id] = view.get('title', f"View {view_id}")
            
            # Cache the mapping
            self.cache.set_views(cache_key, view_map)
            
            return view_map
        except Exception as e:
            logger.error(f"Error getting view names by IDs: {str(e)}")
            
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise ConnectionError(f"Connection error while getting view names: {str(e)}")
            else:
                raise QueryError(f"Error getting view names: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def get_view_ids_by_names(self, view_names: List[str]) -> Dict[str, int]:
        """
        Get view IDs by their names.
        
        Args:
            view_names: List of view names to convert to IDs
            
        Returns:
            Dictionary mapping view names to their IDs
            
        Raises:
            ConnectionError: If the API connection fails
            QueryError: If the query fails for another reason
        """
        if not view_names:
            return {}
            
        logger.info(f"Converting {len(view_names)} view names to IDs")
        
        result = {}
        for view_name in view_names:
            try:
                view = self.get_view_by_name(view_name)
                if view:
                    result[view_name] = view['id']
                    logger.info(f"Converted view name '{view_name}' to ID {view['id']}")
                else:
                    logger.warning(f"Could not find view with name '{view_name}'")
            except Exception as e:
                logger.error(f"Error finding view ID for name '{view_name}': {str(e)}")
                # Continue with other view names
        
        logger.info(f"Successfully converted {len(result)} out of {len(view_names)} view names to IDs")
        return result
    
    # Helper methods
    
    def _validate_view_ids(self, view_ids: List[int]) -> List[int]:
        """
        Validates which view IDs exist and are accessible.
        
        Args:
            view_ids: List of view IDs to validate
            
        Returns:
            List of valid view IDs that exist
        """
        valid_views = []
        
        try:
            # Get all views
            all_views = self.get_all_views()
            all_view_ids = [view.get('id') for view in all_views]
            
            # Check which of the provided view IDs exist
            for view_id in view_ids:
                if view_id in all_view_ids:
                    valid_views.append(view_id)
                else:
                    logger.warning(f"View ID {view_id} does not exist or is not accessible")
            
            return valid_views
        except Exception as e:
            logger.error(f"Error validating view IDs: {str(e)}")
            return []
    
    def _convert_view_to_dict(self, view) -> Dict[str, Any]:
        """
        Convert a Zendesk view object to a dictionary.
        
        Args:
            view: Zendesk view object
            
        Returns:
            Dictionary representation of the view
        """
        # Basic properties
        view_dict = {
            'id': view.id,
            'title': view.title,
            'created_at': view.created_at,
            'updated_at': view.updated_at
        }
        
        # Add additional properties if available
        for attr in ['description', 'position', 'active', 'default', 'execution', 'restriction']:
            if hasattr(view, attr):
                view_dict[attr] = getattr(view, attr)
        
        # Convert conditions if available
        if hasattr(view, 'conditions'):
            view_dict['conditions'] = view.conditions
        
        return view_dict
