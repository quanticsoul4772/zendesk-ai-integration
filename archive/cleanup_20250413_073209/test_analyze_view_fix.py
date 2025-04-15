#!/usr/bin/env python3
"""
Test script for analyzing tickets from a view, specifically checking custom fields handling
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """Test directly accessing tickets from a view and create Ticket entities"""
    try:
        # Import necessary modules
        from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
        from src.domain.entities.ticket import Ticket
        
        # Create repository
        logger.info("Creating Zendesk repository...")
        zendesk_repo = ZendeskRepository()
        
        # Get tickets from the view
        view_id = 29753646016023  # "Production :: Test Engineering :: Test Tickets (RMA)"
        limit = 3
        
        logger.info(f"Fetching up to {limit} tickets from view {view_id}...")
        
        try:
            # Try to get tickets directly using the repository function
            tickets = zendesk_repo.get_tickets_from_view(view_id, limit)
            
            # Display results
            logger.info(f"Successfully retrieved {len(tickets)} tickets from view {view_id}")
            
            for i, ticket in enumerate(tickets, 1):
                logger.info(f"Ticket {i}: ID={ticket.id}, Subject='{ticket.subject}'")
                logger.info(f"  Custom Fields: {ticket.custom_fields}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting tickets from view: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to manual retrieval and conversion
            logger.info("Falling back to manual ticket conversion...")
            
            # Get raw tickets from the Zendesk API
            raw_tickets = list(zendesk_repo.client.views.tickets(view_id))[:limit]
            logger.info(f"Raw tickets count: {len(raw_tickets)}")
            
            for i, raw_ticket in enumerate(raw_tickets, 1):
                logger.info(f"Raw Ticket {i}: ID={raw_ticket.id}, Subject='{raw_ticket.subject}'")
                
                # Debug custom fields
                if hasattr(raw_ticket, 'custom_fields'):
                    cf = raw_ticket.custom_fields
                    logger.info(f"  Custom Fields Type: {type(cf)}")
                    logger.info(f"  Custom Fields Dir: {dir(cf)}")
                    
                    if hasattr(cf, 'items') and callable(getattr(cf, 'items')):
                        logger.info("  Custom Fields Items:")
                        for k, v in cf.items():
                            logger.info(f"    {k}: {v} (type: {type(v)})")
                
                # Try to convert manually
                try:
                    ticket = Ticket.from_zendesk_ticket(raw_ticket)
                    logger.info(f"  Successfully converted ticket {raw_ticket.id}")
                    logger.info(f"  Custom Fields after conversion: {ticket.custom_fields}")
                except Exception as e:
                    logger.error(f"  Error converting ticket {raw_ticket.id}: {e}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
