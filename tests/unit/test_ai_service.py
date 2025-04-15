"""
Unit tests for the AI service module.
"""
import pytest
import logging
from unittest.mock import patch

from src.ai_service import analyze_ticket_content

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_ticket():
    """Sample ticket for testing."""
    return """
    Hello support team,
    
    I've been trying to use your product for the past week and I'm really impressed with the features.
    However, I'm having trouble with the export functionality. When I try to export my data to CSV,
    the application crashes. Could you please help me resolve this issue?
    
    Thanks,
    John
    """

def test_analyze_ticket_content_structure(sample_ticket):
    """Test that the analyze_ticket_content function returns the expected structure."""
    with patch("src.ai_service.get_completion_from_openai") as mock_get_completion:
        # Set up the mock to return a valid JSON response
        mock_get_completion.return_value = '''
        {
            "category": "software issue",
            "component": "export functionality",
            "priority": "medium",
            "sentiment": {
                "polarity": "neutral",
                "urgency_level": 2,
                "frustration_level": 1,
                "emotions": ["impressed", "confused"]
            }
        }
        '''
        
        # Call the function
        result = analyze_ticket_content(sample_ticket)
        
        # Check that the result has the expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "category" in result, "Result should have a 'category' field"
        assert "component" in result, "Result should have a 'component' field"
        assert "priority" in result, "Result should have a 'priority' field"
        assert "sentiment" in result and isinstance(result["sentiment"], dict), "Result should have a 'sentiment' field that is a dictionary"

def test_analyze_ticket_content_error_handling(sample_ticket):
    """Test that the analyze_ticket_content function handles errors properly."""
    with patch("src.ai_service.get_completion_from_openai") as mock_get_completion:
        # Set up the mock to return an invalid JSON response
        mock_get_completion.return_value = "This is not valid JSON"
        
        # Call the function
        result = analyze_ticket_content(sample_ticket)
        
        # Check that error handling works (should return a default response)
        assert isinstance(result, dict), "Result should be a dictionary even with an error"
        assert "error" in result, "Result should have an 'error' field when JSON parsing fails"
