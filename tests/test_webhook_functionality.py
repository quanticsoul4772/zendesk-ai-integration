"""
Test script to verify webhook functionality.

This script simulates a webhook request to verify that the webhook server
is processing requests correctly and maintaining its read-only approach.
"""

import os
import sys
import json
import hmac
import hashlib
import pytest
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime
from flask import Flask, request, jsonify
from src.application.services.ticket_analysis_service import TicketAnalysisService
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
from src.presentation.webhook.webhook_handler import WebhookHandler

# Add the src directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Import the webhook server
# from src.infrastructure.compatibility import WebhookServer
# from src.infrastructure.compatibility import ZendeskClient
# from src.infrastructure.compatibility import AIAnalyzer
# from src.infrastructure.compatibility import DBRepository

# Mark all tests in this module as serial
pytestmark = pytest.mark.serial

def test_webhook_endpoint():
    """Test the webhook endpoint with a simulated request."""
    # Create a test version of WebhookServer without authentication
    class TestWebhookServer(WebhookServer):
        """Test version of WebhookServer that skips authentication."""
        
        def _register_routes(self):
            """Register routes without security decorators."""
            @self.app.route("/webhook", methods=["POST"])
            def webhook_handler():
                """Handle incoming webhook requests from Zendesk without auth."""
                return self._webhook_endpoint()
            
            @self.app.route("/health", methods=["GET"])
            def health_check():
                """Simple health check endpoint."""
                return jsonify({"status": "ok"}), 200

    # Set up mock components
    mock_zendesk = MagicMock(spec=ZendeskClient)
    mock_ai = MagicMock(spec=AIAnalyzer)
    mock_db = MagicMock(spec=DBRepository)
    
    # Configure mock tickets
    mock_ticket = MagicMock()
    mock_ticket.id = "12345"
    mock_ticket.subject = "Test Subject"
    mock_ticket.description = "Test Description with GPU issue"
    mock_ticket.status = "open"
    
    # Configure Zendesk client
    mock_zendesk.get_ticket.return_value = mock_ticket
    mock_zendesk.fetch_tickets.return_value = [mock_ticket]
    
    # Configure AI analyzer
    mock_analysis = {
        "ticket_id": "12345",
        "subject": "Test Subject",
        "sentiment": {
            "polarity": "negative",
            "urgency_level": 4,
            "frustration_level": 3,
            "business_impact": {"detected": True, "description": "Production impact"}
        },
        "category": "hardware_issue",
        "component": "gpu",
        "priority_score": 8,
        "timestamp": datetime.utcnow()
    }
    
    mock_ai.analyze_ticket.return_value = mock_analysis
    
    # Initialize the webhook server with our test class that skips authentication
    server = TestWebhookServer(
        zendesk_client=mock_zendesk,
        ai_analyzer=mock_ai,
        db_repository=mock_db
    )
    
    # Create test app client
    test_client = server.app.test_client()
    
    # Create test webhook data
    webhook_data = {
        "ticket": {
            "id": "12345",
            "subject": "Test Subject",
            "description": "Test Description"
        },
        "event": "ticket_created",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Set up webhook test
    webhook_secret = "test_webhook_secret"
    
    # Mock the environment variable and test
    with patch.dict(os.environ, {"WEBHOOK_SECRET_KEY": webhook_secret}):
        # Prepare payload and send request
        payload = json.dumps(webhook_data).encode('utf-8')
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        response = test_client.post(
            '/webhook',
            data=payload,
            content_type='application/json',
            headers={'X-Zendesk-Webhook-Signature': signature}
        )
        
        # Check response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["status"] == "success"
        assert response_data["ticket_id"] == "12345"
        
        # Verify ticket was analyzed
        mock_ai.analyze_ticket.assert_called_once()
        
        # Verify analysis was saved
        mock_db.save_analysis.assert_called_once()
        
        # Verify ticket was not modified (read-only)
        if hasattr(mock_zendesk, "add_comment"):
            mock_zendesk.add_comment.assert_not_called()
        
        if hasattr(mock_zendesk, "add_ticket_tags"):
            mock_zendesk.add_ticket_tags.assert_not_called()
        
        print("Webhook test passed!")

if __name__ == "__main__":
    test_webhook_endpoint()
