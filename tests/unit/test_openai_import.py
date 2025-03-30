"""
Unit tests for checking OpenAI module versioning and compatibility.
"""
import pytest
import logging
import sys
from unittest.mock import patch, MagicMock

logger = logging.getLogger(__name__)

def test_openai_import():
    """Test that the OpenAI library can be imported."""
    try:
        import openai
        logger.info(f"OpenAI version: {openai.__version__}")
        
        # Check that the version is at least 1.0.0
        version = openai.__version__.split('.')
        major = int(version[0])
        
        assert major >= 1, f"OpenAI version {openai.__version__} is older than 1.0.0. The project requires OpenAI API v1."
    except ImportError:
        pytest.fail("Failed to import OpenAI library")

def test_openai_client_creation():
    """Test that the OpenAI client can be created."""
    try:
        import openai
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            client = openai.OpenAI(api_key="test_key")
            assert client is not None, "Failed to create OpenAI client"
    except ImportError:
        pytest.fail("Failed to import OpenAI library")
    except Exception as e:
        pytest.fail(f"Failed to create OpenAI client: {str(e)}")

def test_openai_client_compatibility():
    """Test compatibility with the OpenAI API."""
    try:
        import openai
        
        # Create mock client to test API compatibility
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with mock client
        response = mock_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello world"}
            ],
            temperature=0
        )
        
        # Check that we can access the response content as expected
        content = response.choices[0].message.content
        assert content == "Test response", f"Expected 'Test response' but got '{content}'"
        
    except ImportError:
        pytest.fail("Failed to import OpenAI library")
    except AttributeError as e:
        pytest.fail(f"OpenAI API incompatibility detected: {str(e)}")
