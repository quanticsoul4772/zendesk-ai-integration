"""
Zendesk client module for ticket operations.

This module provides functions for fetching and updating Zendesk tickets.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Zendesk client
try:
    from zenpy import Zenpy
    from zenpy.lib.api_objects import Ticket, Comment, User, View
except ImportError:
    logger.error("Zenpy package not installed. Install with: pip install zenpy>=2.0.24")
    raise

# Initialize Zendesk client
def get_zendesk_client():
    """
    Get a configured Zendesk client.
    
    Returns:
        A Zenpy client instance.
    """
    # Zendesk credentials
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
    
    return Zenpy(**credentials)

# Initialize once on module import
zenpy_client = get_zendesk_client()

def fetch_tickets(status="open", limit=None):
    """
    Fetch tickets from Zendesk with the specified status.
    
    Args:
        status: Ticket status (open, new, pending, solved, closed)
        limit: Maximum number of tickets to fetch (None for all)
    
    Returns:
        List of Zendesk tickets.
    """
    logger.info(f"Fetching tickets with status: {status}")
    try:
        if limit:
            tickets = list(zenpy_client.tickets(status=status))[:limit]
        else:
            tickets = list(zenpy_client.tickets(status=status))
        
        logger.info(f"Fetched {len(tickets)} tickets with status: {status}")
        return tickets
    except Exception as e:
        logger.exception(f"Error fetching tickets: {e}")
        return []

def fetch_tickets_from_view(view_id, limit=None):
    """
    Fetch tickets from a specific Zendesk view.
    
    Args:
        view_id: ID of the Zendesk view
        limit: Maximum number of tickets to fetch (None for all)
    
    Returns:
        List of Zendesk tickets.
    """
    logger.info(f"Fetching tickets from view ID: {view_id}")
    try:
        if limit:
            tickets = list(zenpy_client.views.tickets(view_id))[:limit]
        else:
            tickets = list(zenpy_client.views.tickets(view_id))
        
        logger.info(f"Fetched {len(tickets)} tickets from view ID: {view_id}")
        return tickets
    except Exception as e:
        logger.exception(f"Error fetching tickets from view: {e}")
        return []

def fetch_tickets_by_view_name(view_name, limit=None):
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
        views = zenpy_client.views()
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
            return fetch_tickets_from_view(view_id, limit)
        else:
            logger.error(f"View not found: {view_name}")
            return []
    except Exception as e:
        logger.exception(f"Error fetching tickets by view name: {e}")
        return []

def add_ticket_tags(ticket, tags):
    """
    Add tags to a Zendesk ticket.
    
    Args:
        ticket: Zendesk ticket object
        tags: List of tags to add
    
    Returns:
        None
    """
    if not tags:
        return
    
    try:
        # Add new tags to existing tags
        current_tags = ticket.tags or []
        new_tags = list(set(current_tags + tags))
        
        # Only update if tags have changed
        if set(new_tags) != set(current_tags):
            ticket.tags = new_tags
            zenpy_client.tickets.update(ticket)
            logger.info(f"Updated tags for ticket {ticket.id}: {new_tags}")
    except Exception as e:
        logger.error(f"Error adding tags to ticket {ticket.id}: {e}")

def add_private_comment(ticket, comment_text):
    """
    Add a private comment to a Zendesk ticket.
    
    Args:
        ticket: Zendesk ticket object
        comment_text: Text for the comment
    
    Returns:
        None
    """
    try:
        ticket.comment = Comment(body=comment_text, public=False)
        zenpy_client.tickets.update(ticket)
        logger.info(f"Added private comment to ticket {ticket.id}")
    except Exception as e:
        logger.error(f"Error adding comment to ticket {ticket.id}: {e}")