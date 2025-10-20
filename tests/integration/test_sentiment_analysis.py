"""
Integration tests for sentiment analysis functionality.

These tests verify that the enhanced sentiment analysis functions correctly
with various types of ticket content.
"""
# SKIPPED: Uses removed sentiment modules
import pytest
pytestmark = pytest.mark.skip(reason="Uses removed sentiment modules")
import pytest
import logging
# from src.enhanced_sentiment import enhanced_analyze_ticket_content

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

def test_sentiment_analysis_structure(sample_tickets):
    """Test that the sentiment analysis function returns the expected structure."""
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
