"""
Tests for the unified AI service and sentiment analysis implementation.
"""

# SKIPPED: This test file tests modules that were removed during clean architecture refactoring.
# Reason: Tests old unified_ai_service module that was removed - replaced with class-based services

import pytest
pytestmark = pytest.mark.skip(reason="Tests old unified_ai_service module that was removed - replaced with class-based services")


import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from src.unified_ai_service import UnifiedAIService, AIServiceError, RateLimitError
# from src.unified_sentiment import analyze_sentiment, calculate_priority_score


class TestUnifiedAIService:
    """Tests for UnifiedAIService class."""
    
    def test_initialization(self):
        """Test initialization with different providers."""
        # Test with Claude (default)
        with patch('src.unified_ai_service.Anthropic') as mock_anthropic:
            service = UnifiedAIService()
            assert service.provider == "claude"
            assert service.ready is True
            mock_anthropic.assert_called_once()
        
        # Test with OpenAI
        with patch('src.unified_ai_service.OpenAI') as mock_openai:
            service = UnifiedAIService(provider="openai")
            assert service.provider == "openai"
            assert service.ready is True
            mock_openai.assert_called_once()
    
    def test_initialization_errors(self):
        """Test initialization error handling."""
        # Test with invalid provider
        with pytest.raises(ValueError) as excinfo:
            service = UnifiedAIService(provider="invalid")
        assert "Unsupported AI provider" in str(excinfo.value)
        
        # Test with missing dependencies
        with patch('src.unified_ai_service.Anthropic', side_effect=ImportError("No module named 'anthropic'")):
            service = UnifiedAIService(provider="claude")
            assert service.ready is False
            
        with patch('src.unified_ai_service.OpenAI', side_effect=ImportError("No module named 'openai'")):
            service = UnifiedAIService(provider="openai")
            assert service.ready is False
    
    def test_get_completion_with_claude(self):
        """Test get_completion with Claude."""
        with patch('src.unified_ai_service.Anthropic') as mock_anthropic:
            # Set up mock response
            mock_client = MagicMock()
            mock_client.messages.create.return_value.content = [
                MagicMock(text='{"result": "success", "sentiment": "positive"}')
            ]
            mock_anthropic.return_value = mock_client
            
            # Initialize service
            service = UnifiedAIService(provider="claude")
            
            # Test get_completion
            result = service.get_completion("Test prompt")
            assert result == {"result": "success", "sentiment": "positive"}
            
            # Verify correct parameters were used
            mock_client.messages.create.assert_called_once()
            args, kwargs = mock_client.messages.create.call_args
            assert kwargs["model"] == "claude-3-haiku-20240307"
            assert kwargs["temperature"] == 0.0
            assert kwargs["messages"][0]["content"] == "Test prompt"
    
    def test_get_completion_with_openai(self):
        """Test get_completion with OpenAI."""
        with patch('src.unified_ai_service.OpenAI') as mock_openai:
            # Set up mock response
            mock_choice = MagicMock()
            mock_choice.message.content = '{"result": "success", "sentiment": "positive"}'
            
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Initialize service
            service = UnifiedAIService(provider="openai")
            
            # Test get_completion
            result = service.get_completion("Test prompt")
            assert result == {"result": "success", "sentiment": "positive"}
            
            # Verify correct parameters were used
            mock_client.chat.completions.create.assert_called_once()
            args, kwargs = mock_client.chat.completions.create.call_args
            assert kwargs["model"] == "gpt-4o-mini"
            assert kwargs["temperature"] == 0.0
            assert kwargs["messages"][0]["content"] == "Test prompt"
    
    def test_analyze_sentiment(self):
        """Test analyze_sentiment method."""
        with patch('src.unified_ai_service.Anthropic') as mock_anthropic:
            # Set up mock response for the get_completion method
            mock_client = MagicMock()
            mock_client.messages.create.return_value.content = [
                MagicMock(text=json.dumps({
                    "sentiment": {
                        "polarity": "negative",
                        "urgency_level": 4,
                        "frustration_level": 3,
                        "technical_expertise": 2,
                        "business_impact": {"detected": True, "description": "Production system down"},
                        "key_phrases": ["system down", "urgent"],
                        "emotions": ["frustration", "worry"]
                    },
                    "category": "hardware_issue",
                    "component": "gpu",
                    "confidence": 0.95
                }))
            ]
            mock_anthropic.return_value = mock_client
            
            # Initialize service and patch calculate_priority_score
            service = UnifiedAIService(provider="claude")
            
            with patch('src.enhanced_sentiment.calculate_priority_score', return_value=8):
                # Test analyze_sentiment
                result = service.analyze_sentiment("My system is down! The GPU is not working.")
                
                # Verify results
                assert result["sentiment"]["polarity"] == "negative"
                assert result["sentiment"]["urgency_level"] == 4
                assert result["sentiment"]["frustration_level"] == 3
                assert result["sentiment"]["business_impact"]["detected"] is True
                assert result["category"] == "hardware_issue"
                assert result["component"] == "gpu"
                assert result["priority_score"] == 8
                assert result["confidence"] == 0.95
    
    def test_error_handling(self):
        """Test error handling in get_completion."""
        with patch('src.unified_ai_service.Anthropic') as mock_anthropic:
            # Set up mock for rate limit error
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
            mock_anthropic.return_value = mock_client
            
            # Initialize service
            service = UnifiedAIService(provider="claude")
            
            # Make sure time.sleep is mocked to speed up the test
            with patch('time.sleep'):
                # Test get_completion with error
                result = service.get_completion("Test prompt")
                assert "error" in result
                assert "Rate limit exceeded" in result["error"]


class TestUnifiedSentiment:
    """Tests for unified_sentiment module."""
    
    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        # Test case 1: High priority
        sentiment_data = {
            "urgency_level": 5,
            "frustration_level": 4,
            "technical_expertise": 2,  # Medium technical expertise (inverse relation)
            "business_impact": {"detected": True, "description": "Production down"}
        }
        score = calculate_priority_score(sentiment_data)
        assert score == 10  # Should be maximum score
        
        # Test case 2: Medium priority
        sentiment_data = {
            "urgency_level": 3,
            "frustration_level": 2,
            "technical_expertise": 3,  # Medium technical expertise
            "business_impact": {"detected": False}
        }
        score = calculate_priority_score(sentiment_data)
        assert 4 <= score <= 6  # Should be medium range
        
        # Test case 3: Low priority
        sentiment_data = {
            "urgency_level": 1,
            "frustration_level": 1,
            "technical_expertise": 5,  # High technical expertise (should lower priority)
            "business_impact": {"detected": False}
        }
        score = calculate_priority_score(sentiment_data)
        assert 1 <= score <= 3  # Should be low range
    
    def test_analyze_sentiment_direct(self):
        """Test analyze_sentiment function uses UnifiedAIService correctly."""
        # Create a mock for UnifiedAIService
        mock_service = MagicMock()
        mock_service.analyze_sentiment.return_value = {
            "sentiment": {
                "polarity": "negative",
                "urgency_level": 4,
                "frustration_level": 3,
                "technical_expertise": 2,
                "business_impact": {"detected": True, "description": "Production system down"},
                "key_phrases": ["system down", "urgent"],
                "emotions": ["frustration", "worry"]
            },
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.95,
            "priority_score": 8
        }
        
        # Patch the UnifiedAIService import to return our mock
        with patch('src.unified_sentiment.UnifiedAIService', return_value=mock_service):
            # Test analyze_sentiment
            result = analyze_sentiment(
                content="My system is down! The GPU is not working.",
                use_enhanced=True,
                ai_provider="claude"
            )
            
            # Verify the service was called correctly
            mock_service.analyze_sentiment.assert_called_once()
            args, kwargs = mock_service.analyze_sentiment.call_args
            assert kwargs["content"] == "My system is down! The GPU is not working."
            assert kwargs["use_enhanced"] is True
            
            # Verify results
            assert result["sentiment"]["polarity"] == "negative"
            assert result["category"] == "hardware_issue"
            assert result["component"] == "gpu"
            assert result["priority_score"] == 8
            assert result["confidence"] == 0.95
    
    def test_analyze_sentiment_fallbacks(self):
        """Test analyze_sentiment falls back to direct implementations if needed."""
        # Create ImportError for UnifiedAIService
        with patch('src.unified_sentiment.UnifiedAIService', side_effect=ImportError("No UnifiedAIService")):
            # Mock the direct implementation (enhanced_analyze_ticket_content)
            with patch('src.claude_enhanced_sentiment.enhanced_analyze_ticket_content') as mock_direct:
                mock_direct.return_value = {
                    "sentiment": "negative",
                    "category": "hardware_issue",
                    "component": "gpu",
                    "confidence": 0.95
                }
                
                # Test with Claude enhanced
                result = analyze_sentiment(
                    content="Test content",
                    use_enhanced=True,
                    ai_provider="claude"
                )
                
                # Verify the direct implementation was called
                mock_direct.assert_called_once_with("Test content")
                assert result["sentiment"] == "negative"
                assert result["category"] == "hardware_issue"
    
    def test_error_handling(self):
        """Test error handling in analyze_sentiment."""
        # Test with empty content
        result = analyze_sentiment("")
        assert result["error"] == "Empty content provided"
        assert result["sentiment"]["polarity"] == "unknown"
        assert result["category"] == "uncategorized"
        
        # Test with unsupported provider
        result = analyze_sentiment("Test content", ai_provider="unsupported")
        assert "Unsupported AI provider" in result["error"]
        
        # Test with other exceptions
        with patch('src.unified_sentiment.UnifiedAIService', side_effect=Exception("General error")):
            result = analyze_sentiment("Test content")
            assert "Error analyzing sentiment" in result["error"]
            assert result["error_type"] == "Exception"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
