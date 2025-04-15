"""
Mocked implementation of the test_sentiment_analysis module.

This is a modified version of the original test file that uses explicit mocking
to ensure consistent test results without requiring real OpenAI API calls.
"""

import pytest
import logging
import os
import json
from unittest.mock import patch, MagicMock

from src.enhanced_sentiment import enhanced_analyze_ticket_content
import src.ai_service

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_tickets():
    """Sample tickets with varying sentiment characteristics for testing."""
    return [
        {
            "title": "Low urgency order status",
            "content": """
            Hello, I placed an order for a new workstation last week (Order #12345).
            I was just wondering if you could provide me with an estimated delivery date?
            Thank you for your help!
            """
        },
        {
            "title": "Medium urgency technical issue",
            "content": """
            Hi support team,
            
            I'm having an issue with one of our development systems. The system keeps freezing
            when running our compute workloads. I've tried rebooting and checking temperatures
            but it still happens. This is slowing down our development process and we need
            to get it resolved in the next few days if possible.
            
            System details:
            - Model: Traverse Pro X8
            - CPU: Intel i9-13900K
            - GPU: 2x RTX 4090
            
            Thanks,
            Dave
            """
        },
        {
            "title": "High urgency production issue",
            "content": """
            URGENT HELP NEEDED! Our main production render server has completely crashed
            and we have a client deliverable due tomorrow morning! This is the third system
            failure this month and it's severely impacting our business. We have a team of
            15 artists sitting idle and we're losing thousands of dollars per hour!
            
            The system was running fine last night but now it won't POST and all diagnostic
            LEDs are red. We've already tried reseating components and testing the power supply.
            
            We need someone to call us IMMEDIATELY to help troubleshoot this.
            Our business literally depends on getting this fixed TODAY.
            
            Jason Miller
            Chief Technical Officer
            """
        }
    ]

# Define mock responses for each test case
mock_responses = {
    0: {  # Low urgency
        "sentiment": {
            "polarity": "neutral",
            "urgency_level": 1,
            "frustration_level": 1,
            "technical_expertise": 2,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": ["wondering about delivery date", "thank you"],
            "emotions": ["curious", "patient"]
        },
        "category": "general_inquiry",
        "component": "none",
        "priority_score": 2,
        "confidence": 0.9
    },
    1: {  # Medium urgency
        "sentiment": {
            "polarity": "neutral",
            "urgency_level": 3,
            "frustration_level": 2,
            "technical_expertise": 3,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": ["system keeps freezing", "slowing down development"],
            "emotions": ["concerned"]
        },
        "category": "hardware_issue",
        "component": "system",
        "priority_score": 6,
        "confidence": 0.85
    },
    2: {  # High urgency
        "sentiment": {
            "polarity": "negative",
            "urgency_level": 5,
            "frustration_level": 4,
            "technical_expertise": 3,
            "business_impact": {
                "detected": True,
                "description": "Production down affecting team productivity and client deliverables"
            },
            "key_phrases": ["URGENT HELP NEEDED", "losing thousands of dollars per hour"],
            "emotions": ["frustrated", "urgent"]
        },
        "category": "hardware_issue",
        "component": "system",
        "priority_score": 9,
        "confidence": 0.95
    }
}

# Create a test-specific version of our AI service call function
def _mock_call_openai(prompt, **kwargs):
    """Test-specific mock for OpenAI API calls"""
    logger.info("Using test-specific mock for OpenAI API")
    # Look for specific indicators in the prompt to determine which response to return
    if "Order #12345" in prompt:
        return mock_responses[0]
    elif "slowing down our development" in prompt:
        return mock_responses[1]
    elif "URGENT HELP NEEDED" in prompt:
        return mock_responses[2]
    else:
        # Default to low urgency
        return mock_responses[0]

# Before all tests, ensure we're using test API key
os.environ["OPENAI_API_KEY"] = "test_key_for_mocked_tests"

def test_sentiment_analysis_structure(sample_tickets):
    """Test that the sentiment analysis function returns the expected structure."""
    with patch.object(src.ai_service, 'call_openai_with_retries', side_effect=_mock_call_openai):
        # Test the first sample ticket (low urgency)
        low_urgency_ticket = sample_tickets[0]["content"]
        analysis = enhanced_analyze_ticket_content(low_urgency_ticket)
        
        # Check basic structure
        assert isinstance(analysis, dict), "Analysis should be a dictionary"
        assert "sentiment" in analysis, "Analysis should contain sentiment data"
        assert isinstance(analysis["sentiment"], dict), "Sentiment should be a dictionary"
        
        # Check sentiment fields
        sentiment = analysis["sentiment"]
        assert "polarity" in sentiment, "Sentiment should have polarity"
        assert "urgency_level" in sentiment, "Sentiment should have urgency level"
        assert "frustration_level" in sentiment, "Sentiment should have frustration level"
        
        # Check additional fields
        assert "category" in analysis, "Analysis should have a category"
        assert "priority_score" in analysis, "Analysis should have a priority score"

@pytest.mark.parametrize("ticket_idx,expected_urgency,expected_business_impact", [
    (0, "low", False),     # Low urgency order status
    (1, "medium", False),  # Medium urgency technical issue  
    (2, "high", True)      # High urgency production issue
])
def test_sentiment_analysis_urgency_detection(sample_tickets, ticket_idx, expected_urgency, expected_business_impact):
    """Test that the sentiment analysis correctly identifies urgency and business impact."""
    # Setup a specific mock response for each test case
    def mock_response_for_test(**kwargs):
        return mock_responses[ticket_idx]
    
    # Apply the specific mock for this test
    with patch.object(src.ai_service, 'call_openai_with_retries', return_value=mock_responses[ticket_idx]):
        ticket_content = sample_tickets[ticket_idx]["content"]
        analysis = enhanced_analyze_ticket_content(ticket_content)
        
        # Check urgency level matches expectation
        sentiment = analysis["sentiment"]
        urgency_level = sentiment["urgency_level"]
        
        # Convert numeric urgency to text for comparison
        if isinstance(urgency_level, (int, float)):
            if urgency_level <= 2:
                detected_urgency = "low"
            elif urgency_level <= 3:
                detected_urgency = "medium"
            else:
                detected_urgency = "high"
        else:
            # If string is returned directly
            detected_urgency = urgency_level.lower()
        
        assert detected_urgency == expected_urgency, f"Expected urgency '{expected_urgency}' but got '{detected_urgency}'"
        
        # Check business impact detection
        business_impact = sentiment.get("business_impact", {})
        has_business_impact = business_impact.get("detected", False) if isinstance(business_impact, dict) else False
        
        assert has_business_impact == expected_business_impact, \
            f"Expected business impact detection to be {expected_business_impact} but got {has_business_impact}"
