"""
Pytest configuration file for end-to-end test fixtures.

This file contains fixtures specifically for end-to-end testing of the Zendesk AI integration.
"""

import pytest
import sys
import os
import io
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the src directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

@pytest.fixture
def mock_zenpy():
    """Mock Zenpy directly at import level for end-to-end tests."""
    with patch.dict(sys.modules, {'zenpy': MagicMock()}) as mock_zenpy:
        # Create a mock Zenpy class
        mock_zenpy_class = MagicMock()
        mock_zenpy.Zenpy = mock_zenpy_class
        
        # Create a mock Zenpy client
        mock_client = MagicMock()
        mock_zenpy_class.return_value = mock_client
        
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
        mock_client.views.return_value = mock_views
        
        # Configure search to return tickets
        mock_client.search.return_value = mock_tickets
        
        # Configure views.tickets
        mock_client.views.tickets.return_value = mock_tickets
        
        yield mock_zenpy

@pytest.fixture
def mock_openai():
    """Mock OpenAI at the import level for end-to-end tests."""
    with patch.dict(sys.modules, {'openai': MagicMock()}) as mock_openai:
        # Create the necessary classes and methods
        mock_openai_class = MagicMock()
        mock_openai.OpenAI = mock_openai_class
        
        # Create a mock client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock the chat completions
        mock_chat = MagicMock()
        mock_client.chat = mock_chat
        
        # Mock completions.create
        mock_completion = MagicMock()
        mock_chat.completions = mock_completion
        
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        
        # Configure completion to return different responses based on input
        def create_side_effect(**kwargs):
            prompt = kwargs.get('messages', [{}])[0].get('content', '')
            
            if "GPU" in prompt or "gpu" in prompt:
                content = '{"sentiment":{"polarity":"negative","urgency_level":4,"frustration_level":3,"business_impact":{"detected":true}},"category":"hardware_issue","component":"gpu","confidence":0.9}'
            else:
                content = '{"sentiment":{"polarity":"neutral","urgency_level":2,"frustration_level":1,"business_impact":{"detected":false}},"category":"general_inquiry","component":"none","confidence":0.8}'
            
            mock_response.choices[0].message.content = content
            return mock_response
            
        mock_completion.create.side_effect = create_side_effect
        
        yield mock_openai

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic at the import level for end-to-end tests."""
    with patch.dict(sys.modules, {'anthropic': MagicMock()}) as mock_anthropic:
        # Create the necessary classes and methods
        mock_anthropic_class = MagicMock()
        mock_anthropic.Anthropic = mock_anthropic_class
        
        # Create a mock client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock the messages
        mock_messages = MagicMock()
        mock_client.messages = mock_messages
        
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        
        # Configure create to return different responses based on input
        def create_side_effect(**kwargs):
            prompt = kwargs.get('messages', [{}])[0].get('content', '')
            
            if "GPU" in prompt or "gpu" in prompt:
                content = {"text": '{"sentiment":{"polarity":"negative","urgency_level":4,"frustration_level":3,"business_impact":{"detected":true}},"category":"hardware_issue","component":"gpu","confidence":0.9}'}
            else:
                content = {"text": '{"sentiment":{"polarity":"neutral","urgency_level":2,"frustration_level":1,"business_impact":{"detected":false}},"category":"general_inquiry","component":"none","confidence":0.8}'}
            
            mock_response.content[0] = content
            return mock_response
            
        mock_messages.create.side_effect = create_side_effect
        
        yield mock_anthropic

@pytest.fixture
def mock_pymongo():
    """Mock PyMongo at the import level for end-to-end tests."""
    with patch.dict(sys.modules, {'pymongo': MagicMock()}) as mock_pymongo:
        # Create the MongoClient class
        mock_mongo_class = MagicMock()
        mock_pymongo.MongoClient = mock_mongo_class
        
        # Create a mock client
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        # Set up mock database and collection
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Configure database access
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Track inserted documents
        inserted_documents = []
        
        # Configure insert_one
        def insert_one_side_effect(document):
            inserted_documents.append(document)
            result = MagicMock()
            result.inserted_id = f"mock_id_{len(inserted_documents)}"
            return result
            
        mock_collection.insert_one.side_effect = insert_one_side_effect
        
        # Configure find operations
        def find_side_effect(query=None, **kwargs):
            return inserted_documents
            
        mock_collection.find.side_effect = find_side_effect
        
        # Add the inserted_documents to the mock for tests to access
        mock_pymongo.inserted_documents = inserted_documents
        
        yield mock_pymongo

@pytest.fixture
def mock_environment():
    """Set up mock environment variables for testing."""
    with patch.dict(os.environ, {
        "ZENDESK_EMAIL": "test@example.com",
        "ZENDESK_API_TOKEN": "test_token",
        "ZENDESK_SUBDOMAIN": "testsubdomain",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB_NAME": "test_db",
        "MONGODB_COLLECTION_NAME": "test_collection",
        "WEBHOOK_SECRET_KEY": "test_webhook_secret",
        "ALLOWED_IPS": "127.0.0.1,192.168.1.1/24"
    }):
        yield
