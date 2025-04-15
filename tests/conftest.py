"""
Root conftest.py file for detecting test type and applying appropriate mocks.

This file configures pytest to automatically detect whether we're running unit or integration
tests and applies the appropriate mocking strategy.
"""

import pytest
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Set up logging with proper cleanup handlers
import atexit
from logging.handlers import MemoryHandler

logger = logging.getLogger(__name__)

# Configure root logger only if it hasn't been configured
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

# Ensure proper cleanup of logging handlers at exit
def cleanup_logging_handlers():
    """Clean up logging handlers to prevent file handle leaks."""
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'close'):
            try:
                handler.close()
            except:
                pass

# Register cleanup function
atexit.register(cleanup_logging_handlers)

# Fixture to ensure proper logging setup and teardown for each test
@pytest.fixture(autouse=True)
def setup_and_cleanup_logging():
    """Ensure proper logging setup and cleanup for each test."""
    # Setup: ensure handlers are in good state
    for handler in logging.getLogger().handlers:
        # Only check file and stream handlers
        if hasattr(handler, 'stream') and handler.stream:
            # Check only if the stream has a 'closed' attribute
            if hasattr(handler.stream, 'closed') and handler.stream.closed:
                # Replace closed stream handlers
                handler.close()
                logging.getLogger().removeHandler(handler)
    
    # Continue with test    
    yield
    
    # Teardown: flush all handlers
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'flush'):
            try:
                handler.flush()
            except Exception:
                pass

# Detect test environment
def is_integration_test(item):
    """Determine if the test is an integration test based on path"""
    return "integration" in item.nodeid

def is_sentiment_analysis_test(item):
    """Determine if the test is related to sentiment analysis"""
    return "sentiment_analysis" in item.nodeid or "ai_service" in item.nodeid

# Root level fixture to detect and apply mocking based on test type
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    This hook runs before each test and applies the appropriate mocking strategy
    based on the test type and location.
    """
    # For integration tests, use the monkey patching approach
    if is_integration_test(item):
        logger.info(f"Setting up integration test mocks for: {item.nodeid}")
        # Import the monkey patching module
        try:
            import tests.integration.openai_mock
            logger.info("Monkey patching module imported successfully")
        except ImportError:
            logger.warning("Could not import monkey patching module, will try direct mocking")
            # Apply direct mocking as a fallback
            try:
                import src.ai_service
                from tests.integration.openai_mock import mock_call_openai_with_retries, mock_get_completion_from_openai
                
                # Replace the real functions with our mocks
                src.ai_service.call_openai_with_retries = mock_call_openai_with_retries
                src.ai_service.get_completion_from_openai = mock_get_completion_from_openai
                logger.info("Direct mocking applied successfully")
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not apply direct mocking: {str(e)}")
                logger.info("Mocking will be applied via pytest fixtures")
    
    # For sentiment analysis tests, ensure we're using our test mocks
    elif is_sentiment_analysis_test(item):
        logger.info(f"Setting up sentiment analysis test mocks for: {item.nodeid}")
        # Use similar approach but with unit test appropriate mocks
        try:
            import src.ai_service
            # Only apply basic mocking for unit tests - each test should handle its own mocks
            logger.info("Unit test detection complete, individual tests will handle mocking")
        except ImportError:
            logger.warning("Could not import ai_service for unit test detection")
