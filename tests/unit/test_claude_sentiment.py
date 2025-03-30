"""
Unit tests for the Claude-enhanced sentiment analysis.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock

from src.claude_enhanced_sentiment import analyze_with_claude

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_ticket():
    """Sample ticket for testing."""
    return """
    Hello support team,
    
    Our server is completely down and our production pipeline is at a standstill.
    We need urgent help as we have a delivery deadline this afternoon.
    This is costing us thousands of dollars per hour in lost productivity.
    
    Please help us resolve this ASAP!
    
    Thanks,
    John
    """

def test_claude_sentiment_structure():
    """Test that the claude sentiment analysis has the correct structure."""
    with patch("src.claude_enhanced_sentiment.get_completion_from_claude") as mock_get_completion:
        # Set up mock response
        mock_response = MagicMock()
        mock_response.content = """
        {
          "sentiment": {
            "polarity": "negative",
            "urgency_level": 5,
            "frustration_level": 4,
            "technical_expertise": 3,
            "emotions": ["anxiety", "frustration", "urgency"],
            "key_phrases": ["server is completely down", "production pipeline", "urgent help", "delivery deadline", "thousands of dollars"],
            "business_impact": {
              "detected": true,
              "description": "Production pipeline standstill causing financial loss"
            }
          },
          "category": "server outage",
          "component": "server",
          "priority_score": 9,
          "confidence": 0.92
        }
        """
        mock_get_completion.return_value = mock_response
        
        # Call the function with any sample text
        result = analyze_with_claude("Sample text")
        
        # Check structure
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "category" in result
        assert "priority_score" in result
        
        # Check sentiment structure
        sentiment = result["sentiment"]
        assert "polarity" in sentiment
        assert "urgency_level" in sentiment
        assert "emotions" in sentiment
        assert "business_impact" in sentiment
        
        # Check business impact structure
        business_impact = sentiment["business_impact"]
        assert "detected" in business_impact
        assert "description" in business_impact

def test_claude_sentiment_error_handling():
    """Test error handling in the claude sentiment analysis."""
    with patch("src.claude_enhanced_sentiment.get_completion_from_claude") as mock_get_completion:
        # Set up mock to raise an exception
        mock_get_completion.side_effect = Exception("API error")
        
        # Call the function
        result = analyze_with_claude("Sample text")
        
        # Check error handling structure
        assert isinstance(result, dict)
        assert "error" in result
        assert "sentiment" in result
        assert result["sentiment"].get("polarity") == "unknown"
