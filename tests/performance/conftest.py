"""
Performance test fixtures for the Zendesk AI Integration project.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from src.application.services.ticket_analysis_service import TicketAnalysisService
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository

# Ensure the project root is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

@pytest.fixture
def zendesk_client():
    """
    Fixture that provides a ZendeskRepository instance for performance testing.

    NOTE: Old ZendeskClient module was removed during clean architecture refactoring.
    This fixture now returns a mock ZendeskRepository.
    """
    # Create a mock repository
    mock_repo = MagicMock(spec=ZendeskRepository)

    # Configure basic mock behavior
    mock_repo.get_tickets.return_value = []
    mock_repo.get_all_views.return_value = []

    yield mock_repo

@pytest.fixture
def ai_analyzer():
    """
    Fixture that provides a TicketAnalysisService instance for performance testing.

    NOTE: Old AIAnalyzer and BatchProcessor modules were removed during clean architecture refactoring.
    This fixture now returns a mock TicketAnalysisService.
    """
    # Create a mock service
    mock_service = MagicMock(spec=TicketAnalysisService)

    # Mock the analysis functions to return predictable results without making API calls
    def mock_analyze_ticket(ticket_id, subject="", description=""):
        import time
        import random
        from datetime import datetime

        # Simulate processing time
        time.sleep(0.1)  # Fast enough for tests but simulates real processing

        # Return a realistic analysis result
        return {
            "ticket_id": ticket_id,
            "subject": subject,
            "timestamp": datetime.utcnow(),
            "sentiment": {
                "polarity": random.choice(["positive", "negative", "neutral"]),
                "urgency_level": random.randint(1, 5),
                "frustration_level": random.randint(1, 5),
                "technical_expertise": random.randint(1, 5),
                "business_impact": {
                    "detected": random.choice([True, False]),
                    "description": "Test business impact"
                },
                "key_phrases": ["test phrase 1", "test phrase 2"],
                "emotions": ["test emotion"]
            },
            "category": random.choice(["hardware_issue", "software_issue", "technical_support"]),
            "component": random.choice(["gpu", "cpu", "memory", "none"]),
            "priority_score": random.randint(1, 10),
            "confidence": random.uniform(0.7, 1.0)
        }

    # Apply the mock
    mock_service.analyze_ticket.side_effect = mock_analyze_ticket

    yield mock_service
