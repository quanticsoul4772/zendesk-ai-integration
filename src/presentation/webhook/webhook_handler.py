"""
Webhook Handler

This module defines the WebhookHandler class that processes webhook requests from Zendesk.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable

# Set up logging
logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles webhooks from Zendesk.

    This class processes webhook requests from Zendesk and dispatches them to
    the appropriate handler methods.
    """

    def __init__(self, service_provider: Any):
        """
        Initialize the webhook handler.

        Args:
            service_provider: Provider for application services
        """
        self.service_provider = service_provider
        self.webhook_service = service_provider.get_webhook_service()
        self.handlers: Dict[str, Callable] = {
            "ticket.created": self._handle_ticket_created,
            "ticket.updated": self._handle_ticket_updated,
            "comment.created": self._handle_comment_created
        }

    def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a webhook request.

        Args:
            event_type: Type of webhook event
            payload: Webhook payload

        Returns:
            Response with success/error information
        """
        logger.info(f"Handling webhook event: {event_type}")

        # Check if we have a handler for this event type
        handler = self.handlers.get(event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return {
                "success": False,
                "error": f"Unknown event type: {event_type}"
            }

        try:
            # Call the handler
            result = handler(payload)

            # Return the result
            return {
                "success": result,
                "event_type": event_type
            }
        except Exception as e:
            logger.exception(f"Error handling webhook: {e}")

            return {
                "success": False,
                "error": str(e),
                "event_type": event_type
            }

    def _handle_ticket_created(self, payload: Dict[str, Any]) -> bool:
        """
        Handle a ticket.created webhook event.

        Args:
            payload: Webhook payload

        Returns:
            Success indicator
        """
        # Extract ticket data
        ticket_data = payload.get("ticket", {})

        # Process the event
        return self.webhook_service.handle_ticket_created(ticket_data)

    def _handle_ticket_updated(self, payload: Dict[str, Any]) -> bool:
        """
        Handle a ticket.updated webhook event.

        Args:
            payload: Webhook payload

        Returns:
            Success indicator
        """
        # Extract ticket data
        ticket_data = payload.get("ticket", {})

        # Process the event
        return self.webhook_service.handle_ticket_updated(ticket_data)

    def _handle_comment_created(self, payload: Dict[str, Any]) -> bool:
        """
        Handle a comment.created webhook event.

        Args:
            payload: Webhook payload

        Returns:
            Success indicator
        """
        # Extract comment data
        comment_data = payload.get("comment", {})

        # Process the event
        return self.webhook_service.handle_comment_created(comment_data)
