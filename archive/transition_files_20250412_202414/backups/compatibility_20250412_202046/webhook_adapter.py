"""
Webhook Server Adapter

This module provides an adapter that presents a WebhookServer interface
but uses the new WebhookHandler and WebhookService implementations internally.
"""

import logging
import threading
from typing import Dict, List, Any, Optional, Union, Callable

from src.domain.interfaces.service_interfaces import WebhookService as WebhookServiceInterface
from src.presentation.webhook.webhook_handler import WebhookHandler
from src.application.services.webhook_service import WebhookService

# Set up logging
logger = logging.getLogger(__name__)


class WebhookServerAdapter:
    """
    Adapter that presents a WebhookServer interface but uses WebhookHandler and WebhookService internally.
    
    This adapter helps with the transition from the legacy WebhookServer to the
    new webhook implementation.
    """
    
    def __init__(self, webhook_service=None, webhook_handler=None):
        """
        Initialize the adapter.
        
        Args:
            webhook_service: Optional WebhookService instance
            webhook_handler: Optional WebhookHandler instance
        """
        self._webhook_service = webhook_service or WebhookService()
        self._webhook_handler = webhook_handler or WebhookHandler(self._webhook_service)
        
        self._server_thread = None
        self._running = False
        
        # Legacy compatibility: Store references to services that may be used by legacy code
        self.zendesk_client = None
        self.ai_analyzer = None
        self.db_repository = None
        
        logger.debug("WebhookServerAdapter initialized - using WebhookHandler internally")
    
    def set_services(self, zendesk_client, ai_analyzer, db_repository):
        """
        Set the services used by the webhook server (for legacy compatibility).
        
        Args:
            zendesk_client: Zendesk client instance
            ai_analyzer: AI analyzer instance
            db_repository: DB repository instance
        """
        logger.debug("WebhookServerAdapter.set_services called")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Update the webhook service with adapters if necessary
        if hasattr(self._webhook_service, 'set_repositories'):
            self._webhook_service.set_repositories(
                ticket_repository=zendesk_client,
                analysis_repository=db_repository
            )
        
        if hasattr(self._webhook_service, 'set_ticket_analysis_service'):
            self._webhook_service.set_ticket_analysis_service(ai_analyzer)
    
    def start(self, host='0.0.0.0', port=5000, endpoint='/webhook', debug=False):
        """
        Start the webhook server.
        
        Args:
            host: Host to listen on
            port: Port to listen on
            endpoint: Webhook endpoint
            debug: Whether to enable debug mode
            
        Returns:
            Success indicator
        """
        logger.debug(f"WebhookServerAdapter.start called on {host}:{port}{endpoint}")
        
        if self._running:
            logger.warning("WebhookServerAdapter is already running")
            return False
        
        def _run_server():
            self._webhook_handler.start(host, port, endpoint, debug)
        
        self._server_thread = threading.Thread(target=_run_server)
        self._server_thread.daemon = True
        self._server_thread.start()
        
        self._running = True
        logger.info(f"WebhookServerAdapter started on {host}:{port}{endpoint}")
        
        return True
    
    def stop(self):
        """
        Stop the webhook server.
        
        Returns:
            Success indicator
        """
        logger.debug("WebhookServerAdapter.stop called")
        
        if not self._running:
            logger.warning("WebhookServerAdapter is not running")
            return False
        
        self._webhook_handler.stop()
        
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=5)
        
        self._running = False
        logger.info("WebhookServerAdapter stopped")
        
        return True
    
    def is_running(self):
        """
        Check if the webhook server is running.
        
        Returns:
            True if running, False otherwise
        """
        return self._running
    
    def register_callback(self, callback, event_type='ticket.updated'):
        """
        Register a callback for a specific event type.
        
        Args:
            callback: Callback function
            event_type: Event type to trigger the callback
            
        Returns:
            Success indicator
        """
        logger.debug(f"WebhookServerAdapter.register_callback called for event {event_type}")
        
        # Delegate to the webhook service if it supports registering callbacks
        if hasattr(self._webhook_service, 'register_callback'):
            return self._webhook_service.register_callback(callback, event_type)
        
        # Legacy fallback
        logger.warning("WebhookService does not support registering callbacks")
        return False
