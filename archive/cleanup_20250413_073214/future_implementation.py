"""
Sample improved implementation for ZendeskClient.fetch_tickets to support the days parameter

This is a suggestion for how to update the ZendeskClient.fetch_tickets method to
support the days parameter, which will make it match the test expectations.
"""

def fetch_tickets(self, status="open", limit=None, days=None, filter_by=None, view_id=None):
    """
    Fetch tickets from Zendesk with the specified parameters.
    
    Args:
        status: Ticket status (open, new, pending, solved, closed, all)
        limit: Maximum number of tickets to fetch (None for all)
        days: Number of days to look back for tickets
        filter_by: Dictionary of additional filters
        view_id: Optional ID of a Zendesk view to fetch tickets from
        
    Returns:
        List of Zendesk tickets.
    """
    # If view_id is provided, use fetch_tickets_from_view method
    if view_id is not None:
        return self.fetch_tickets_from_view(view_id, limit)
        
    # Create a cache key based on the function parameters
    cache_key = f"tickets_{status}_{limit}_{days}_{str(filter_by)}"
    
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
            
        # Prepare search query if days parameter is present
        if days is not None:
            from datetime import datetime, timedelta
            past_date = datetime.utcnow() - timedelta(days=days)
            date_str = past_date.strftime("%Y-%m-%d")
            if status.lower() == "all":
                search_query = f"created>{date_str}"
            else:
                search_query = f"status:{status} created>{date_str}"
            
            tickets = list(self.client.search(search_query))
        elif status.lower() == "all":
            # Fetch all tickets regardless of status
            try:
                tickets = list(self.client.tickets())
            except Exception as e:
                logger.warning(f"Error using tickets() method, falling back to search: {e}")
                tickets = list(self.client.search("type:ticket"))
            logger.info(f"Fetched {len(tickets)} tickets with any status")
        elif limit:
            try:
                tickets = list(self.client.tickets(status=status))[:limit]
            except Exception as e:
                logger.warning(f"Error using tickets() method, falling back to search: {e}")
                search_query = f"type:ticket status:{status}"
                tickets = list(self.client.search(search_query))[:limit]
        else:
            try:
                tickets = list(self.client.tickets(status=status))
            except Exception as e:
                logger.warning(f"Error using tickets() method, falling back to search: {e}")
                search_query = f"type:ticket status:{status}"
                tickets = list(self.client.search(search_query))
        
        # Apply limit if specified
        if limit and len(tickets) > limit:
            tickets = tickets[:limit]
            
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
        # Check for rate limiting error (status code 429)
        if hasattr(e, 'response') and getattr(e.response, 'status_code', 0) == 429:
            # Wait for a bit and retry once
            logger.warning(f"Rate limit hit when fetching tickets. Retrying after a short delay.")
            import time
            time.sleep(2)  # 2 second delay
            
            # Try the request again
            try:
                if days is not None:
                    from datetime import datetime, timedelta
                    past_date = datetime.utcnow() - timedelta(days=days)
                    date_str = past_date.strftime("%Y-%m-%d")
                    search_query = f"status:{status} created>{date_str}"
                    tickets = list(self.client.search(search_query))
                else:
                    tickets = list(self.client.search(f"status:{status}"))
                
                # Apply limit if specified
                if limit:
                    tickets = tickets[:limit]
                
                return tickets
            except Exception as retry_error:
                logger.exception(f"Error after rate limit retry: {retry_error}")
                return []
        else:
            logger.exception(f"Error fetching tickets: {e}")
            return []
