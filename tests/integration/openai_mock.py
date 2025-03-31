"""
Monkey patching module for OpenAI API mocking.

This module provides functions to override the OpenAI API calls with mock implementations.
Import this module at the beginning of any test file that needs OpenAI mocking.

Example:
    import tests.integration.openai_mock  # This will apply the patches automatically
"""

import logging
import json
from unittest.mock import patch, MagicMock
import sys

# Get logger
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
            "key_phrases": ["wondering about order status", "estimated delivery date"],
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
            "key_phrases": ["system keeps freezing", "slowing down our development"],
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
            "key_phrases": ["URGENT HELP NEEDED", "severely impacting our business"],
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

def mock_call_openai_with_retries(prompt, **kwargs):
    """Mock implementation of call_openai_with_retries"""
    logger.info("Using monkey-patched OpenAI API call")
    
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
    logger.info("Using monkey-patched OpenAI get_completion")
    result = mock_call_openai_with_retries(prompt)
    return json.dumps(result, indent=2)

# Create a mock OpenAI client that can be used when the actual client is instantiated
class MockOpenAIClient:
    def __init__(self, **kwargs):
        logger.info("Creating MockOpenAIClient instead of real OpenAI client")
    
    class ChatCompletions:
        @staticmethod
        def create(**kwargs):
            prompt = kwargs.get("messages", [{}])[0].get("content", "")
            result = mock_call_openai_with_retries(prompt)
            
            # Create a mock response object with the expected structure
            class MockResponse:
                class Message:
                    def __init__(self, content):
                        self.content = content
                
                class Choice:
                    def __init__(self, message):
                        self.message = message
                
                def __init__(self, content):
                    self.choices = [self.Choice(self.Message(json.dumps(content)))]
            
            return MockResponse(result)
    
    chat = ChatCompletions()

# Apply the monkey patching
try:
    # Try to import and patch directly
    import src.ai_service
    # Replace the real functions with our mocks
    logger.info("Applying monkey patches to OpenAI functions")
    src.ai_service.call_openai_with_retries = mock_call_openai_with_retries
    src.ai_service.get_completion_from_openai = mock_get_completion_from_openai
    
    # Also try to patch the OpenAI client itself if it's imported
    try:
        import openai
        openai.OpenAI = MockOpenAIClient
        logger.info("OpenAI client successfully patched")
    except (ImportError, AttributeError):
        logger.info("OpenAI client not directly importable, will be patched when used")
        
    # Add the mock to sys.modules to ensure it's used for future imports
    sys.modules['openai'] = MagicMock()
    sys.modules['openai'].OpenAI = MockOpenAIClient
    
    logger.info("OpenAI monkey patching complete")
    
except (ImportError, AttributeError) as e:
    logger.warning(f"Could not directly patch OpenAI functions: {str(e)}")
    logger.info("Patches will be applied via pytest fixtures instead")
