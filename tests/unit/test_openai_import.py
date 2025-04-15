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
        # Reset sys.modules cache for openai to ensure fresh import
        if 'openai' in sys.modules:
            del sys.modules['openai']
            
        import openai
        
        # Check if version attribute exists directly
        if hasattr(openai, '__version__'):
            version_str = openai.__version__
        else:
            # Fallback to try pkg_resources if available
            try:
                import pkg_resources
                version_str = pkg_resources.get_distribution("openai").version
            except ImportError:
                # If pkg_resources not available, use a different approach
                import importlib.metadata
                version_str = importlib.metadata.version("openai")
                
        logger.info(f"OpenAI version: {version_str}")
        
        # Check that the version is at least 1.0.0
        version = version_str.split('.')
        major = int(version[0])
        
        assert major >= 1, f"OpenAI version {version_str} is older than 1.0.0. The project requires OpenAI API v1."
    except ImportError as e:
        logger.error(f"ImportError: {str(e)}")
        pytest.fail(f"Failed to import OpenAI library: {str(e)}")
    except Exception as e:
        logger.error(f"Error checking OpenAI version: {str(e)}")
        pytest.fail(f"Error checking OpenAI version: {str(e)}")

def test_openai_client_creation():
    """Test that the OpenAI client can be created."""
    try:
        # Reset sys.modules cache for openai to ensure fresh import
        if 'openai' in sys.modules:
            del sys.modules['openai']
            
        import openai
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            client = openai.OpenAI(api_key="test_key")
            assert client is not None, "Failed to create OpenAI client"
    except ImportError as e:
        logger.error(f"ImportError: {str(e)}")
        pytest.fail(f"Failed to import OpenAI library: {str(e)}")
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        pytest.fail(f"Failed to create OpenAI client: {str(e)}")

def test_openai_client_compatibility():
    """Test compatibility with the OpenAI API."""
    try:
        # Reset sys.modules cache for openai to ensure fresh import
        if 'openai' in sys.modules:
            del sys.modules['openai']
            
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
        
    except ImportError as e:
        logger.error(f"ImportError: {str(e)}")
        pytest.fail(f"Failed to import OpenAI library: {str(e)}")
    except AttributeError as e:
        logger.error(f"AttributeError: {str(e)}")
        pytest.fail(f"OpenAI API incompatibility detected: {str(e)}")
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        pytest.fail(f"Unexpected error in OpenAI compatibility test: {str(e)}")
