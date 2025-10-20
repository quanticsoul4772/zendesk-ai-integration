"""
Pytest configuration for integration tests.

This file contains fixtures specifically for integration testing that properly
mock external APIs like OpenAI to avoid authentication issues and provide consistent results.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
import json
import sys

logger = logging.getLogger(__name__)

# Define responses for different urgency levels
mock_responses = {
    "low": {
        "sentiment": {
            "polarity": "positive",
            "urgency_level": 1,
            "frustration_level": 1,
            "technical_expertise": 3,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": ["wondering about order status", "estimated delivery date", "thank you"],
            "emotions": ["curious", "patient"]
        },
        "category": "general_inquiry",
        "component": "none",
        "confidence": 0.95
    },
    "medium": {
        "sentiment": {
            "polarity": "neutral",
            "urgency_level": 3,
            "frustration_level": 2,
            "technical_expertise": 4,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": ["system keeps freezing", "slowing down our development", "need it resolved in a few days"],
            "emotions": ["concerned", "professional"]
        },
        "category": "hardware_issue",
        "component": "system",
        "confidence": 0.9
    },
    "high": {
        "sentiment": {
            "polarity": "negative",
            "urgency_level": 5,
            "frustration_level": 4,
            "technical_expertise": 4,
            "business_impact": {
                "detected": True,
                "description": "Production system down with financial impact and urgent client deliverable"
            },
            "key_phrases": ["URGENT HELP NEEDED", "severely impacting our business", "losing thousands of dollars per hour"],
            "emotions": ["frustrated", "urgent", "worried"]
        },
        "category": "hardware_issue",
        "component": "system",
        "confidence": 0.98
    },
    "default": {
        "sentiment": {
            "polarity": "neutral",
            "urgency_level": 2,
            "frustration_level": 1,
            "technical_expertise": 3,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": [],
            "emotions": []
        },
        "category": "general_inquiry",
        "component": "none",
        "confidence": 0.8
    }
}

# Create mock implementations
def mock_call_openai_with_retries(prompt, **kwargs):
    """Mock implementation of call_openai_with_retries"""
    logger.info("Using mocked OpenAI API call")
    
    # Determine the response based on content in the prompt
    if "URGENT" in prompt or "emergency" in prompt.lower() or "losing thousands" in prompt:
        return mock_responses["high"]
    elif "slowing down our development" in prompt or "freezing" in prompt:
        return mock_responses["medium"]
    elif "wondering if you could provide" in prompt or "order status" in prompt.lower():
        return mock_responses["low"]
    else:
        return mock_responses["default"]

def mock_get_completion_from_openai(prompt, **kwargs):
    """Mock implementation of get_completion_from_openai"""
    logger.info("Using mocked OpenAI get_completion")
    result = mock_call_openai_with_retries(prompt)
    return json.dumps(result, indent=2)

# Note: Monkey patching removed as src.ai_service has been refactored to class-based services
# The old function-based API (call_openai_with_retries, get_completion_from_openai) no longer exists.
# Tests should mock the new service classes (OpenAIService, ClaudeService) as needed.
# See src/infrastructure/external_services/ for the new implementations.

@pytest.fixture
def zendesk_client():
    """Provide a mock ZendeskClient for integration tests."""
    from unittest.mock import MagicMock
    from datetime import datetime, timedelta
    
    mock_client = MagicMock()
    
    # Configure fetch_tickets to return mock tickets
    mock_tickets = []
    for i in range(5):
        ticket = MagicMock()
        ticket.id = f"{10000 + i}"
        ticket.subject = f"Test Subject {i}"
        ticket.description = f"Test Description {i}" + (" GPU issue" if i % 2 == 0 else "")
        ticket.status = "open" if i < 3 else "pending"
        ticket.created_at = datetime.utcnow() - timedelta(days=i)
        ticket.updated_at = datetime.utcnow() - timedelta(hours=i)
        ticket.tags = [f"tag_{i}"]
        mock_tickets.append(ticket)
    
    # Configure methods
    mock_client.fetch_tickets.return_value = mock_tickets
    mock_client.fetch_tickets_from_view.return_value = mock_tickets
    mock_client.fetch_tickets_from_multiple_views.return_value = mock_tickets
    mock_client.fetch_tickets_by_view_name.return_value = mock_tickets
    mock_client.list_all_views.return_value = [MagicMock(id=1001, title="Test View")]
    
    # Add a get_ticket method for tests that expect it
    mock_client.get_ticket = MagicMock(return_value=mock_tickets[0])
    
    # Add cache mock with stats
    mock_cache = MagicMock()
    mock_cache.get_stats.return_value = {"hits": 1, "misses": 1, "size": 5}
    mock_client.cache = mock_cache
    
    return mock_client

@pytest.fixture
def ai_analyzer():
    """Provide a mock AIAnalyzer for integration tests."""
    from unittest.mock import MagicMock
    from datetime import datetime
    
    mock_analyzer = MagicMock()
    
    # Configure analyze_ticket to return mock analysis
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
        "confidence": 0.9,
        "timestamp": datetime.utcnow()
    }
    
    mock_analyzer.analyze_ticket.return_value = mock_analysis
    
    # Configure batch analysis
    batch_results = {}
    for i in range(5):
        ticket_id = f"{10000 + i}"
        analysis = mock_analysis.copy()
        analysis["ticket_id"] = ticket_id
        analysis["subject"] = f"Test Subject {i}"
        batch_results[ticket_id] = analysis
    
    mock_analyzer.analyze_tickets_batch.return_value = batch_results
    
    return mock_analyzer

@pytest.fixture(scope="module", autouse=False)
def patch_openai():
    """
    This fixture has been disabled (autouse=False) as the old src.ai_service module no longer exists.
    The codebase has been refactored to use class-based services (OpenAIService, ClaudeService).

    Individual tests that need to mock AI services should:
    1. Import the service class: from src.infrastructure.external_services.openai_service import OpenAIService
    2. Mock the class or its methods as needed
    3. Use the mock_responses data structure above for consistent test data

    Example:
        @patch('src.infrastructure.external_services.openai_service.OpenAIService')
        def test_something(mock_service):
            mock_instance = mock_service.return_value
            mock_instance.analyze_content.return_value = mock_responses["high"]
            ...
    """
    # This fixture is now a no-op placeholder for backward compatibility
    yield
