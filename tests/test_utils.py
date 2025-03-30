"""
Test Utilities

Common utility functions to support testing.
"""

from unittest.mock import MagicMock
from datetime import datetime, timedelta
import json
import random


def create_mock_ticket(ticket_id="12345", subject="Test Subject", description="Test Description", status="open", created_at=None):
    """
    Create a mock Zendesk ticket object for testing.
    
    Args:
        ticket_id: ID for the ticket
        subject: Subject line
        description: Ticket description/content
        status: Ticket status
        created_at: Creation timestamp (defaults to now)
        
    Returns:
        Mock ticket object
    """
    if created_at is None:
        created_at = datetime.utcnow()
        
    # Create a mock ticket object
    ticket = MagicMock()
    ticket.id = ticket_id
    ticket.subject = subject
    ticket.description = description
    ticket.status = status
    ticket.created_at = created_at
    ticket.tags = []
    ticket.requester_id = "user_123"
    ticket.assignee_id = "agent_456"
    ticket.priority = "normal"
    ticket.updated_at = created_at
    
    # Add custom methods
    def add_tag(tag):
        if tag not in ticket.tags:
            ticket.tags.append(tag)
    
    ticket.add_tag = add_tag
    
    return ticket


def create_mock_tickets(count=5, with_random_data=True):
    """
    Create a list of mock tickets for testing.
    
    Args:
        count: Number of tickets to create
        with_random_data: Whether to use random varied data
        
    Returns:
        List of mock ticket objects
    """
    tickets = []
    
    # Sample data for random generation
    subjects = [
        "GPU rendering issue",
        "System crashes during startup",
        "RAM compatibility question",
        "Fan making noise",
        "Power supply problem",
        "Display flickering",
        "Need assistance with order",
        "RMA request",
        "BIOS update inquiry"
    ]
    
    descriptions = [
        "My system keeps crashing when I try to render large projects.",
        "I installed your GPU but my system won't boot anymore.",
        "Is the RAM I purchased compatible with my motherboard?",
        "The cooling fan is making a grinding noise, what should I do?",
        "My power supply shuts down under heavy load, is it defective?",
        "The display flickers when running games, is this a GPU issue?",
        "I'd like to check the status of my recent order #87652.",
        "I need to return a defective component, please advise.",
        "How do I update the BIOS on my system safely?"
    ]
    
    statuses = ["open", "pending", "solved", "new", "closed"]
    components = ["gpu", "cpu", "memory", "power_supply", "motherboard", "none"]
    
    # Create tickets
    for i in range(count):
        if with_random_data:
            subject = random.choice(subjects)
            description = random.choice(descriptions)
            status = random.choice(statuses)
            created_days_ago = random.randint(1, 30)
            created_at = datetime.utcnow() - timedelta(days=created_days_ago)
        else:
            # Use deterministic data
            subject = f"Test Subject {i+1}"
            description = f"Test Description {i+1}"
            status = "open"
            created_at = datetime.utcnow() - timedelta(days=i)
        
        ticket = create_mock_ticket(
            ticket_id=str(10000 + i),
            subject=subject,
            description=description,
            status=status,
            created_at=created_at
        )
        
        tickets.append(ticket)
    
    return tickets


def create_mock_ai_response(sentiment="neutral", category="general_inquiry", component="none", 
                          confidence=0.7, ticket_id="12345", subject="Test Subject", enhanced=False):
    """
    Create a mock AI analysis response for testing.
    
    Args:
        sentiment: Sentiment value or dict for enhanced sentiment
        category: Category label
        component: Hardware component
        confidence: Confidence score
        ticket_id: Associated ticket ID
        subject: Associated ticket subject
        enhanced: Whether to use enhanced sentiment format
        
    Returns:
        Dict with mock analysis response
    """
    timestamp = datetime.utcnow()
    
    if enhanced:
        # Create enhanced sentiment format
        if isinstance(sentiment, str):
            # Convert simple sentiment to enhanced format
            sentiment_data = {
                "polarity": sentiment,
                "urgency_level": 3,
                "frustration_level": 2,
                "technical_expertise": 3,
                "business_impact": {
                    "detected": False,
                    "description": ""
                },
                "key_phrases": ["test phrase", "another phrase"],
                "emotions": ["neutral"]
            }
        else:
            # Use provided sentiment dict
            sentiment_data = sentiment
            
        # Format a response with enhanced sentiment
        response = {
            "ticket_id": ticket_id,
            "subject": subject,
            "sentiment": sentiment_data,
            "category": category,
            "component": component,
            "confidence": confidence,
            "timestamp": timestamp,
            "priority_score": 5  # Default mid-range priority
        }
        
    else:
        # Format a simple sentiment response
        response = {
            "ticket_id": ticket_id,
            "subject": subject,
            "sentiment": sentiment,
            "category": category,
            "component": component,
            "confidence": confidence,
            "timestamp": timestamp
        }
    
    return response


def setup_mock_flask_context(monkeypatch):
    """
    Set up mocking for Flask request context.
    
    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    # Create a mock Flask request
    mock_request = MagicMock()
    mock_request.remote_addr = "127.0.0.1"
    mock_request.headers = {"X-API-Key": "valid_api_key"}
    
    # Patch the Flask request object
    monkeypatch.setattr("flask.request", mock_request)
    
    return mock_request
