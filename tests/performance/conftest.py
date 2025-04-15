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
    Fixture that provides a ZendeskClient instance for performance testing.
    Uses the actual implementation rather than a mock for performance tests.
    """
#     from src.infrastructure.compatibility import ZendeskClient
    
    # Create the client
    with patch("modules.zendesk_client.ZendeskClient._validate_view_ids", return_value=set([123, 456])):
        client = ZendeskClient()
        
        # Mock the Zenpy client to avoid actual API calls
        mock_client = MagicMock()
        client.client = mock_client
        
        # Set up the cache properly for testing
        client.cache.clear_all()
        
        yield client
        
        # Clean up after the test
        client.cache.clear_all()

@pytest.fixture
def ai_analyzer():
    """
    Fixture that provides an AIAnalyzer instance for performance testing.
    Uses a mock for AI services to avoid actual API calls while maintaining real processing logic.
    """
#     from src.infrastructure.compatibility import AIAnalyzer
    from src.modules.batch_processor import BatchProcessor
    
    # Create the analyzer
    analyzer = AIAnalyzer()
    
    # Mock the AI analysis functions to return predictable results without making API calls
    def mock_analyze_ticket(ticket_id, subject, description, use_enhanced=True, use_claude=True):
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
    
    # Apply the mock to the analyze_ticket method
    analyzer.analyze_ticket = mock_analyze_ticket
    
    # Set up a fresh batch processor
    analyzer.batch_processor = BatchProcessor(
        max_workers=5,
        batch_size=10,
        show_progress=True
    )
    
    yield analyzer
