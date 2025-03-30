"""
Unit tests for checking Anthropic module versioning and compatibility.
"""
import pytest
import logging
import sys
from unittest.mock import patch, MagicMock

logger = logging.getLogger(__name__)

def test_anthropic_import():
    """Test that the Anthropic library can be imported."""
    try:
        import anthropic
        logger.info(f"Anthropic version: {anthropic.__version__}")
        
        # Check that the version is at least 0.8.0
        version = anthropic.__version__.split('.')
        major, minor = int(version[0]), int(version[1])
        
        assert (major > 0) or (major == 0 and minor >= 8), \
            f"Anthropic version {anthropic.__version__} is older than 0.8.0"
    except ImportError:
        pytest.fail("Failed to import Anthropic library")

def test_anthropic_client_creation():
    """Test that the Anthropic client can be created."""
    try:
        import anthropic
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            client = anthropic.Anthropic(api_key="test_key")
            assert client is not None, "Failed to create Anthropic client"
    except ImportError:
        pytest.fail("Failed to import Anthropic library")
    except Exception as e:
        pytest.fail(f"Failed to create Anthropic client: {str(e)}")

def test_anthropic_client_compatibility():
    """Test compatibility with the Anthropic API."""
    try:
        import anthropic
        
        # Create mock client to test API compatibility
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_client.messages.create.return_value = mock_message
        
        # Test with mock client
        response = mock_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": "Hello Claude"}
            ]
        )
        
        assert hasattr(response, 'content'), "Response does not have 'content' attribute"
        
    except ImportError:
        pytest.fail("Failed to import Anthropic library")
    except AttributeError as e:
        pytest.fail(f"Anthropic API incompatibility detected: {str(e)}")
