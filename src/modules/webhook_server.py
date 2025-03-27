"""
Webhook Server Module

This module provides a Flask server for handling Zendesk webhooks.
It includes security features like IP whitelisting and signature verification.
"""

import os
import logging
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import security decorators with absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security import ip_whitelist, webhook_auth

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables if not already loaded
load_dotenv()

class WebhookServer:
    """
    Flask server for handling Zendesk webhooks with security features.
    """
    
    def __init__(self, zendesk_client, ai_analyzer, db_repository):
        """
        Initialize the webhook server.
        
        Args:
            zendesk_client: ZendeskClient instance for ticket operations
            ai_analyzer: AIAnalyzer instance for ticket analysis
            db_repository: DBRepository instance for storing analysis results
        """
        self.app = Flask(__name__)
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        self.add_comments = False  # Default to not adding comments
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register the webhook route with the Flask app."""
        @self.app.route("/webhook", methods=["POST"])
        @ip_whitelist
        @webhook_auth
        def webhook_handler():
            """Handle incoming webhook requests from Zendesk."""
            data = request.json
            if not data or "ticket" not in data:
                return jsonify({"error": "Invalid payload"}), 400
            
            ticket_id = data["ticket"]["id"]
            logger.info(f"Received webhook for ticket {ticket_id}")
            
            try:
                # Fetch the full ticket from Zendesk
                tickets = self.zendesk_client.fetch_tickets(filter_by={"id": ticket_id})
                if not tickets:
                    return jsonify({"error": "Ticket not found"}), 404
                
                ticket = tickets[0]
                
                # Analyze the ticket
                subject = ticket.subject or ""
                description = ticket.description or ""
                analysis = self.ai_analyzer.analyze_ticket(
                    ticket_id=ticket_id,
                    subject=subject,
                    description=description,
                    use_enhanced=True  # Always use enhanced for webhooks
                )
                
                # Save analysis to database
                self.db_repository.save_analysis(analysis)
                
                # No ticket modifications - this is a read-only system
                # Just analyze and store, don't modify the ticket
                
                return jsonify({
                    "status": "success", 
                    "ticket_id": ticket_id,
                    "sentiment": analysis.get("sentiment", {}),
                    "priority_score": analysis.get("priority_score", 0)
                }), 200
                
            except Exception as e:
                logger.exception(f"Error processing webhook for ticket {ticket_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        # Health check endpoint
        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Simple health check endpoint."""
            return jsonify({"status": "ok"}), 200
    
    def set_comment_preference(self, add_comments):
        """
        Set whether to add comments to tickets.
        
        Args:
            add_comments: Boolean indicating whether to add comments
                          (Note: Comments are now always disabled regardless of this setting)
        """
        # This method is maintained for backward compatibility but does nothing
        # The system never adds comments or tags to tickets
        pass
    
    def run(self, host='0.0.0.0', port=5000):
        """
        Run the webhook server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        # Log security settings
        logger.info("Starting webhook server...")
        logger.info("Security features enabled:")
        logger.info(f"- IP Whitelist: {'Enabled' if os.getenv('ALLOWED_IPS') else 'Disabled'}")
        logger.info(f"- Webhook Signature Verification: {'Enabled' if os.getenv('WEBHOOK_SECRET_KEY') else 'Disabled'}")
        logger.info("- Ticket modifications: Disabled (This is a read-only system)")
        
        # Run the Flask app
        self.app.run(host=host, port=port, debug=False)
