"""
Unit Tests for Enhanced OpenAI Sentiment Analysis Module

Tests the functionality of the enhanced_sentiment.py module which uses OpenAI.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Import module to test
from src.enhanced_sentiment import (
    enhanced_analyze_ticket_content,
    calculate_priority_score,
    create_default_sentiment_response
)


class TestEnhancedSentiment:
    """Test suite for Enhanced OpenAI Sentiment Analysis functionality."""
    
    @patch('src.enhanced_sentiment.call_openai_with_retries')
    def test_enhanced_analyze_ticket_content_success(self, mock_call_function):
        """Test successful enhanced ticket content analysis with OpenAI."""
        content = "Our production server is down, and we're losing $10,000 per hour! I've contacted support twice already about this. Please help ASAP!"
        
        # Configure the mock response
        mock_call_function.return_value = {
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
        
        # Verify that API was called with appropriate parameters
        mock_call_function.assert_called_once()
        
        # Check if the content was included in the prompt
        assert mock_call_function.call_args is not None
        call_args = mock_call_function.call_args[1]
        assert 'prompt' in call_args
        assert content in call_args['prompt']
    
    def test_enhanced_analyze_ticket_content_empty(self):
        """Test enhanced analysis with empty content."""
        # Call with empty content
        result = enhanced_analyze_ticket_content("")
        
        # Create expected response
        expected = create_default_sentiment_response("Empty content provided")
        
        # Assertions
        assert result["sentiment"]["polarity"] == expected["sentiment"]["polarity"]
        assert result["sentiment"]["urgency_level"] == expected["sentiment"]["urgency_level"]
        assert result["sentiment"]["frustration_level"] == expected["sentiment"]["frustration_level"]
        assert result["sentiment"]["business_impact"]["detected"] == expected["sentiment"]["business_impact"]["detected"]
        assert result["sentiment"]["key_phrases"] == expected["sentiment"]["key_phrases"]
        assert result["sentiment"]["emotions"] == expected["sentiment"]["emotions"]
        assert result["category"] == expected["category"]
        assert result["component"] == expected["component"]
        assert result["priority_score"] == expected["priority_score"]
        assert result["confidence"] == expected["confidence"]
        assert "error" in result
        assert "Empty content provided" in result["error"]
    
    @patch('src.enhanced_sentiment.call_openai_with_retries')
    def test_enhanced_analyze_ticket_content_api_error(self, mock_call_function):
        """Test handling of OpenAI API errors."""
        content = "Test content"
        
        # Configure mock to raise an API error
        mock_call_function.side_effect = Exception("API error")
        
        # Call the function being tested
        result = enhanced_analyze_ticket_content(content)
        
        # Create expected response
        expected = create_default_sentiment_response("API error")
        
        # Assertions
        assert result["sentiment"]["polarity"] == expected["sentiment"]["polarity"]
        assert result["sentiment"]["urgency_level"] == expected["sentiment"]["urgency_level"]
        assert result["sentiment"]["business_impact"]["detected"] == expected["sentiment"]["business_impact"]["detected"]
        assert result["category"] == expected["category"]
        assert result["component"] == expected["component"]
        assert result["priority_score"] == expected["priority_score"]
        assert "error" in result
        assert "API error" in result["error"]
    
    @patch('src.enhanced_sentiment.call_openai_with_retries')
    def test_non_json_response_handling(self, mock_call_function):
        """Test handling of non-JSON responses from OpenAI."""
        content = "Test content"
        
        # Configure mock to return non-JSON response
        mock_call_function.return_value = {"raw_text": "This is not a valid JSON response"}
        
        # Call the function being tested with the non-JSON response
        result = enhanced_analyze_ticket_content(content)
        
        # Assertions - just verify basic structure and error
        assert "sentiment" in result
        assert "category" in result
        assert "component" in result
        assert "error" in result
    
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
