"""Unit test fixtures for Zendesk AI Integration.

This module contains fixtures specific to unit tests.
"""

import pytest
import time
import uuid
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Import the cache manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.modules.cache_manager import ZendeskCache

@pytest.fixture(scope="session")
def execution_id():
    """
    Generate a unique execution ID for the test run.
    This helps isolate tests that run in parallel.
    """
    return str(uuid.uuid4())[:8]

@pytest.fixture
def isolated_cache_manager():
    """
    Create an isolated cache manager instance for testing.
    Each test gets its own clean instance.
    """
    cache = ZendeskCache()
    cache.clear_all()  # Start with a clean cache
    yield cache
    cache.clear_all()  # Clean up after test

@pytest.fixture
def frozen_time():
    """
    A fixture that freezes time, providing a controllable datetime for tests.
    """
    class FrozenTimeHelper:
        def __init__(self):
            self.current_time = datetime.utcnow()
            self.patcher = patch('datetime.datetime')
            self.mock_datetime = self.patcher.start()
            self.mock_datetime.utcnow.return_value = self.current_time
            # Make sure the real datetime class is still accessible
            self.mock_datetime.side_effect = datetime
            
        def advance(self, seconds):
            """Advance the frozen time by the specified number of seconds."""
            self.current_time += timedelta(seconds=seconds)
            self.mock_datetime.utcnow.return_value = self.current_time
            
        def cleanup(self):
            """Stop the patching."""
            self.patcher.stop()
    
    helper = FrozenTimeHelper()
    yield helper
    helper.cleanup()

@pytest.fixture
def mock_mongodb():
    """
    Create mocks for MongoDB connection components.
    Returns a tuple of (mock_client_class, mock_db, mock_collection).
    """
    # Create the mock objects
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Configure client to return db
    mock_client.__getitem__.return_value = mock_db
    
    # Configure db to return collection
    mock_db.__getitem__.return_value = mock_collection
    
    # Configure collection.index_information to return some indexes by default
    mock_collection.index_information.return_value = {
        "ticket_id_1": {},
        "timestamp_1": {}
    }
    
    # Create a mock for the client class
    with patch('pymongo.MongoClient') as mock_client_class:
        mock_client_class.return_value = mock_client
        
        # Return the mocks so tests can configure them further if needed
        yield (mock_client_class, mock_db, mock_collection)

@pytest.fixture
def mock_claude_service():
    """
    Mock the Claude Service for testing.
    """
    # Use patch to mock the call_claude_with_retries function
    patcher = patch('src.claude_service.call_claude_with_retries')
    mock = patcher.start()
    yield mock
    patcher.stop()

@pytest.fixture
def mock_enhanced_claude_service():
    """
    Mock the Claude Enhanced Sentiment service for testing.
    """
    # Use patch to mock the call_claude_with_retries function
    patcher = patch('src.claude_enhanced_sentiment.call_claude_with_retries')
    mock = patcher.start()
    yield mock
    patcher.stop()

@pytest.fixture
def mock_zendesk_client():
    """Create a mock Zendesk client for testing."""
    # Create a mock client
    mock_client = MagicMock()
    
    # Set up mock tickets
    mock_tickets = []
    for i in range(5):
        ticket = MagicMock()
        ticket.id = f"{10000 + i}"
        ticket.subject = f"Test Subject {i}"
        ticket.description = f"Test Description {i}" + (" GPU issue" if i % 2 == 0 else "")
        ticket.status = "open" if i < 3 else "pending"
        ticket.created_at = datetime.utcnow() - timedelta(days=i)
        ticket.updated_at = datetime.utcnow() - timedelta(hours=i)
        ticket.tags = [f"tag_{i}"]
        mock_tickets.append(ticket)
    
    # Set up a collection of mock views
    mock_views = []
    for i in range(3):
        view = MagicMock()
        view.id = 1000 + i
        view.title = f"Test View {i}"
        mock_views.append(view)
    
    # Configure client methods
    mock_client.tickets.return_value = mock_tickets
    
    # Configure views method to return views list and view by ID based on context
    mock_view_by_id = MagicMock()
    mock_view_by_id.id = 123
    mock_view_by_id.title = "Test View by ID"
    
    # Set up views as a smart MagicMock that can handle both list and individual calls
    views_mock = MagicMock()
    
    # For direct call without parameters, return list of views
    views_mock.return_value = mock_views
    
    # For call with id parameter, return specific view
    def views_with_params(*args, **kwargs):
        if 'id' in kwargs and kwargs['id'] == 123:
            return mock_view_by_id
        return mock_views
    views_mock.side_effect = views_with_params
    
    mock_client.views = views_mock
    
    # Configure search to return tickets
    mock_client.search.return_value = mock_tickets
    
    # Configure views.tickets
    mock_client.views.tickets.return_value = mock_tickets
    
    # Configure list method for the views
    mock_client.views.list.return_value = mock_views
    
    # The key part: mock both Zenpy import and instantiation
    with patch('src.modules.zendesk_client.Zenpy', create=True) as mock_zenpy_class:
        mock_zenpy_class.return_value = mock_client
        yield mock_client
