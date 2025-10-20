"""
Unit Tests for Enhanced Claude Sentiment Analysis Module

Tests the functionality of the claude_enhanced_sentiment.py module.
"""

# SKIPPED: This test file tests modules that were removed during clean architecture refactoring.
# Reason: Old claude_enhanced_sentiment module removed - replaced with ClaudeService
# To enable this test, the test would need to be rewritten to test the new architecture.

import pytest
pytestmark = pytest.mark.skip(reason="Old claude_enhanced_sentiment module removed - replaced with ClaudeService")


import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Import module to test
# from src.claude_enhanced_sentiment import (
##     enhanced_analyze_ticket_content,
#     calculate_priority_score,
#     create_default_sentiment_response,
#     ClaudeServiceError
# )


class TestClaudeEnhancedSentiment:
    """Test suite for Enhanced Claude Sentiment Analysis functionality."""
    
    def test_enhanced_analyze_ticket_content_success(self, mock_enhanced_claude_service):
        """Test successful enhanced ticket content analysis."""
        content = "Our production server is down, and we're losing $10,000 per hour! I've contacted support twice already about this. Please help ASAP!"
        
        # Configure the mock to return a successful response with correct format
        mock_response = {
            "sentiment": {
                "polarity": "negative",
                "urgency_level": 5,
                "frustration_level": 4,
                "technical_expertise": 2,
                "business_impact": {
                    "detected": True,
                    "description": "Production system down causing financial loss"
                },
                "key_phrases": ["production server down", "losing money", "contacted twice"],
                "emotions": ["frustrated", "urgent"]
            },
            "category": "hardware_issue",
            "component": "server",
            "confidence": 0.9
        }
        mock_enhanced_claude_service.return_value = mock_response
        
        # Call the function being tested
        result = enhanced_analyze_ticket_content(content)
        
        # Assertions
        assert result["sentiment"]["polarity"] == "negative"
        assert result["sentiment"]["urgency_level"] == 5
        assert result["sentiment"]["frustration_level"] == 4
        assert result["sentiment"]["business_impact"]["detected"] is True
        assert "production" in result["sentiment"]["business_impact"]["description"].lower()
        assert "key_phrases" in result["sentiment"]
        assert "emotions" in result["sentiment"]
        assert result["category"] == "hardware_issue"
        assert result["component"] == "server"
        assert result["confidence"] == 0.9
        assert "priority_score" in result
        assert 8 <= result["priority_score"] <= 10  # High priority due to high urgency and business impact
        
        # Verify that the Claude API was called with appropriate parameters
        mock_enhanced_claude_service.assert_called_once()
        
        # Get the call arguments - handle both positional and keyword arguments
        prompt_arg = None
        if mock_enhanced_claude_service.call_args and mock_enhanced_claude_service.call_args[0]:
            # Called with positional args
            prompt_arg = mock_enhanced_claude_service.call_args[0][0]
        elif mock_enhanced_claude_service.call_args.kwargs.get('prompt'):
            # Called with keyword args
            prompt_arg = mock_enhanced_claude_service.call_args.kwargs.get('prompt')
            
        assert prompt_arg is not None, "Claude service was not called with a prompt"
        assert "TICKET CONTENT" in prompt_arg
        assert content in prompt_arg
    
    def test_enhanced_analyze_ticket_content_empty(self):
        """Test enhanced analysis with empty content."""
        # Call with empty content
        result = enhanced_analyze_ticket_content("")
        
        # Assertions
        assert result["sentiment"]["polarity"] == "unknown"
        assert result["sentiment"]["urgency_level"] == 1
        assert result["sentiment"]["frustration_level"] == 1
        assert result["sentiment"]["business_impact"]["detected"] is False
        assert result["sentiment"]["key_phrases"] == []
        assert result["sentiment"]["emotions"] == []
        assert result["category"] == "uncategorized"
        assert result["component"] == "none"
        assert result["priority_score"] == 1
        assert result["confidence"] == 0.0
        assert "error" in result
        assert "Empty content" in result["error"]
    
    def test_enhanced_analyze_ticket_content_service_error(self, mock_enhanced_claude_service):
        """Test handling of Claude service errors."""
        content = "Test content"
        
        # Configure mock to raise a service error
        mock_enhanced_claude_service.side_effect = ClaudeServiceError("Service unavailable")
        
        # Call the function being tested
        result = enhanced_analyze_ticket_content(content)
        
        # Assertions
        assert result["sentiment"]["polarity"] == "unknown"
        assert result["sentiment"]["urgency_level"] == 1
        assert result["sentiment"]["business_impact"]["detected"] is False
        assert result["category"] == "uncategorized"
        assert result["component"] == "none"
        assert result["priority_score"] == 1
        assert "error" in result
        assert "Service unavailable" in result["error"]
        assert result["error_type"] == "ClaudeServiceError"
    
    def test_normalize_sentiment_data(self, mock_enhanced_claude_service):
        """Test normalization of sentiment data with unusual formats."""
        content = "Test content"
        
        # Configure mock with unusual response format
        mock_enhanced_claude_service.return_value = {
            "sentiment": {
                "polarity": "NEGATIVE",  # Uppercase
                "urgency_level": "4",     # String instead of int
                "frustration_level": 3.5, # Float instead of int
                "technical_expertise": 2,
                "business_impact": True,  # Boolean instead of object
                "key_phrases": "system down, urgent",  # String instead of list
                "emotions": ["ANGRY", "Worried"]  # Mixed case
            },
            "category": "Hardware Issue",  # Space instead of underscore
            "component": ["server"],       # List instead of string
            "confidence": "high"           # Text instead of number
        }
        
        # Call the function being tested
        result = enhanced_analyze_ticket_content(content)
        
        # Assertions
        assert result["sentiment"]["polarity"] == "negative"  # Should be normalized to lowercase
        assert result["sentiment"]["urgency_level"] == 4  # Should be converted to int
        assert result["sentiment"]["frustration_level"] == 3 or result["sentiment"]["frustration_level"] == 4  # Should be rounded to int
        assert isinstance(result["sentiment"]["business_impact"], dict)  # Should be converted to dict
        assert isinstance(result["sentiment"]["key_phrases"], list)  # Should be converted to list
        assert result["category"] == "hardware_issue"  # Should be normalized
        assert result["component"] == "server"  # Should be extracted from list
        assert isinstance(result["confidence"], float)  # Should be converted to float
    
    def test_calculate_priority_score(self):
        """Test priority score calculation with different inputs."""
        # Test case 1: High urgency, high frustration, business impact
        sentiment_data1 = {
            "urgency_level": 5,
            "frustration_level": 5,
            "business_impact": {"detected": True},
            "technical_expertise": 3
        }
        score1 = calculate_priority_score(sentiment_data1)
        assert 9 <= score1 <= 10  # Should be very high priority
        
        # Test case 2: Medium urgency, low frustration, no business impact
        sentiment_data2 = {
            "urgency_level": 3,
            "frustration_level": 2,
            "business_impact": {"detected": False},
            "technical_expertise": 3
        }
        score2 = calculate_priority_score(sentiment_data2)
        assert 3 <= score2 <= 6  # Should be medium priority
        
        # Test case 3: Low urgency, low frustration, no business impact, high expertise
        sentiment_data3 = {
            "urgency_level": 1,
            "frustration_level": 1,
            "business_impact": {"detected": False},
            "technical_expertise": 5
        }
        score3 = calculate_priority_score(sentiment_data3)
        assert 1 <= score3 <= 3  # Should be low priority
        
        # Test case 4: Low urgency, low frustration, business impact
        sentiment_data4 = {
            "urgency_level": 1,
            "frustration_level": 1,
            "business_impact": {"detected": True},
            "technical_expertise": 3
        }
        score4 = calculate_priority_score(sentiment_data4)
        assert score4 > score3  # Business impact should increase priority
        
        # Test case 5: Missing fields
        sentiment_data5 = {
            "urgency_level": 3
            # Missing other fields
        }
        score5 = calculate_priority_score(sentiment_data5)
        assert 1 <= score5 <= 10  # Should handle missing fields gracefully
    
    def test_create_default_sentiment_response(self):
        """Test creation of default sentiment response."""
        # Test with no error message
        response1 = create_default_sentiment_response()
        assert response1["sentiment"]["polarity"] == "unknown"
        assert response1["sentiment"]["urgency_level"] == 1
        assert response1["sentiment"]["frustration_level"] == 1
        assert response1["sentiment"]["business_impact"]["detected"] is False
        assert response1["category"] == "uncategorized"
        assert response1["component"] == "none"
        assert response1["priority_score"] == 1
        assert "error" in response1
        assert response1["error_type"] == "EmptyContentError"
        
        # Test with custom error message
        response2 = create_default_sentiment_response("Custom error")
        assert "Custom error" in response2["error"]
        assert response2["error_type"] == "EnhancedSentimentError"
