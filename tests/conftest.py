"""
Pytest Configuration and Fixtures

This module contains pytest configuration and fixtures used across all test modules.
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import builtins
import flask

# Add the src directory to the Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Import test utilities
from tests.test_utils import create_mock_ticket, create_mock_tickets, create_mock_ai_response


# Set up test execution ID for test isolation
@pytest.fixture(scope="session")
def execution_id():
    """Generate a unique execution ID for test isolation."""
    import uuid
    return str(uuid.uuid4())[:8]

# Set up mock environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Set up mock environment variables for testing."""
    with patch.dict(os.environ, {
        "ZENDESK_EMAIL": "test@example.com",
        "ZENDESK_API_TOKEN": "test_token",
        "ZENDESK_SUBDOMAIN": "testsubdomain",
        "OPENAI_API_KEY": "sk-test-openaikey-for-testing-purposes",
        "ANTHROPIC_API_KEY": "sk-ant-api03-test-key-for-testing-only",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB_NAME": "test_db",
        "MONGODB_COLLECTION_NAME": "test_collection",
        "WEBHOOK_SECRET_KEY": "test_webhook_secret"
    }):
        yield


# Mock ticket for testing
@pytest.fixture
def mock_ticket():
    """Create a mock Zendesk ticket for testing."""
    return create_mock_ticket(
        ticket_id="12345",
        subject="Test GPU Issue",
        description="My GPU keeps crashing during rendering jobs.",
        status="open"
    )


# Mock tickets for batch testing
@pytest.fixture
def mock_tickets():
    """Create a list of mock tickets for testing."""
    return create_mock_tickets(count=5)


# Mock AI analysis result
@pytest.fixture
def mock_ai_result():
    """Create a mock AI analysis result for testing."""
    return create_mock_ai_response(
        sentiment="negative",
        category="hardware_issue",
        component="gpu",
        confidence=0.85,
        enhanced=True
    )


# Mock Zendesk client
@pytest.fixture
def mock_zendesk_client():
    """Create a mock Zendesk client for testing."""
    with patch('zenpy.Zenpy', new=MagicMock()) as mock_zenpy:
        client_instance = MagicMock()
        
        # Configure default behavior
        mock_tickets = create_mock_tickets()
        client_instance.search.return_value = mock_tickets
        
        # Mock the tickets method to also return mock_tickets
        # This ensures compatibility with both client.search and client.tickets calls
        tickets_mock = MagicMock()
        tickets_mock.return_value = mock_tickets
        client_instance.tickets = tickets_mock
        
        mock_zenpy.return_value = client_instance
        yield client_instance


# Mock Anthropic client
@pytest.fixture
def mock_anthropic_client():
    """Mock the Anthropic client completely to prevent API calls"""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="{\"sentiment\": \"negative\", \"category\": \"hardware_issue\", \"component\": \"gpu\", \"confidence\": 0.9}")]
    
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    
    with patch('anthropic.Anthropic', return_value=mock_client):
        yield mock_client

# Mock Claude service for regular testing
@pytest.fixture
def mock_claude_service(mock_anthropic_client):
    """Create a mock for Claude service API calls."""
    # Need to patch both import paths since claude_enhanced_sentiment.py uses a relative import
    with patch('src.claude_service.call_claude_with_retries') as mock_call, \
         patch('src.claude_enhanced_sentiment.call_claude_with_retries') as enhanced_mock_call:
        # Configure default successful response for basic tests
        basic_response = {
            "sentiment": "negative",
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.9
        }
        
        # Configure more complex response for enhanced tests
        enhanced_response = {
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
        
        # Set up the return values for each mock
        mock_call.return_value = basic_response
        enhanced_mock_call.return_value = enhanced_response
        
        # Return the basic mock for regular test functions
        yield mock_call


# Mock Enhanced Claude service
@pytest.fixture
def mock_enhanced_claude_service(mock_anthropic_client):
    """Create a mock for Enhanced Claude service API calls."""
    # Need to patch both import paths since claude_enhanced_sentiment.py uses a relative import
    with patch('src.claude_enhanced_sentiment.call_claude_with_retries') as enhanced_mock_call:
        # Configure more complex response for enhanced tests
        enhanced_response = {
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
        
        enhanced_mock_call.return_value = enhanced_response
        
        # Return the enhanced mock for enhanced test functions
        yield enhanced_mock_call


# Mock OpenAI client
@pytest.fixture
def mock_openai_client():
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = """
    {
        "sentiment": {
            "polarity": "negative",
            "urgency_level": 3,
            "frustration_level": 4,
            "business_impact": {"detected": true, "description": "Production impact"}
        },
        "category": "hardware_issue",
        "component": "gpu",
        "confidence": 0.9
    }
    """
    
    # Create client instance
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    # Set up the patches
    with patch('openai.OpenAI', return_value=mock_client):
        yield mock_client

# Mock OpenAI service
@pytest.fixture
def mock_openai_service(mock_openai_client):
    """Create a mock for OpenAI service API calls that depends on mock_openai_client."""
    with patch('src.ai_service.get_openai_client', return_value=mock_openai_client) as mock_get_client, \
         patch('src.ai_service.openai.OpenAI', return_value=mock_openai_client), \
         patch('src.ai_service.call_openai_with_retries') as mock_call, \
         patch('src.enhanced_sentiment.call_openai_with_retries') as enhanced_mock_call:
        # Configure the mock to return a successful response
        mock_response = {
            "sentiment": {
                "polarity": "negative",
                "urgency_level": 4,
                "frustration_level": 3,
                "business_impact": {"detected": True, "description": "Production impact"},
                "key_phrases": ["urgent issue", "system down", "need help"],
                "emotions": ["frustrated", "worried"]
            },
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.9
        }
        
        # Set the response for both regular and enhanced mocks
        mock_call.return_value = mock_response
        enhanced_mock_call.return_value = mock_response
        
        yield mock_call


# Mock MongoDB
@pytest.fixture
def mock_mongodb():
    """Create a mock for MongoDB client."""
    with patch('pymongo.MongoClient') as mock_client_class:
        # Configure mock collection
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Create mock client instance
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        
        # Set this as the return value of MongoClient()
        mock_client_class.return_value = mock_client
        
        # Configure default behavior for common operations
        mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id_12345")
        mock_collection.find_one.return_value = None
        mock_collection.find.return_value = []
        
        # Set up the close method as a MagicMock to track calls
        mock_client.close = MagicMock()
        
        # Return the mocks for the test to use
        yield mock_client_class, mock_db, mock_collection
        
# Isolated cache manager for testing cache operations
@pytest.fixture
def isolated_cache_manager():
    """Create an isolated cache manager that doesn't interfere with other tests."""
    from src.modules.cache_manager import ZendeskCache
    
    # Create a unique instance
    cache = ZendeskCache()
    
    # Ensure it's empty to start
    cache.clear_all()
    
    yield cache
    
    # Clean up after the test
    cache.clear_all()

# Frozen time fixture for testing TTL and time-based operations
@pytest.fixture
def frozen_time():
    """Create a mock for time that can be advanced for testing."""
    # Save the original time function
    original_time = time.time
    
    # Create a class to manage the frozen time
    class FrozenTime:
        def __init__(self):
            self.current_time = original_time()
            
        def time_function(self):
            return self.current_time
            
        def advance(self, seconds):
            self.current_time += seconds
    
    # Create an instance
    frozen = FrozenTime()
    
    # Patch the time.time function
    with patch('time.time', frozen.time_function):
        yield frozen
        
    # No need to restore as the patch context manager handles it

# Add Flask Context mock for Security tests
@pytest.fixture
def mock_flask_context():
    """Create a mock Flask application context and request context."""
    mock_app = flask.Flask("mock_app")
    mock_app.config["TESTING"] = True
    
    # Create a mock request with the headers we want
    class MockRequest:
        remote_addr = "127.0.0.1"
        headers = {"X-API-Key": "valid_key", "X-Zendesk-Webhook-Signature": "valid_signature"}
    
    # Patch the flask request object
    with patch("flask.request", MockRequest()), \
         patch("flask.current_app", mock_app), \
         patch("src.security.request", MockRequest()), \
         patch("src.security.validate_api_key", return_value=True), \
         patch("src.security.verify_webhook_signature", return_value=True):
        yield

# Mock for reporter base classes
@pytest.fixture
def mock_reporter_common():
    """Create mocks for the reporter common functionality."""
    with patch("src.modules.reporters.sentiment_report.SentimentReporter._calculate_time_period", 
              return_value=(datetime.utcnow(), "last 7 days")), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter._format_timestamp",
              return_value="2025-03-30 12:00:00"), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter._format_percentage",
              return_value="50.0%"), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter._get_view_by_id_or_name",
              return_value=MagicMock(title="Test View")), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter.output",
              return_value=None), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter._format_ticket_details",
              return_value="Ticket details"), \
         patch("src.modules.reporters.sentiment_report.SentimentReporter._filter_high_priority_tickets",
              return_value=[]), \
         patch("src.modules.reporters.hardware_report.HardwareReporter._analyze_component_distribution",
              return_value={}), \
         patch("src.modules.reporters.hardware_report.HardwareReporter._format_ticket_details",
              return_value="Hardware ticket details"), \
         patch("src.modules.reporters.hardware_report.HardwareReporter._format_component_distribution",
              return_value="Component distribution"), \
         patch("src.modules.reporters.pending_report.PendingReporter._format_ticket_details",
              return_value="Pending ticket details"), \
         patch("src.modules.reporters.pending_report.PendingReporter._categorize_tickets",
              return_value={"categories": {}, "tickets_by_category": {}}), \
         patch("src.modules.reporters.enhanced_sentiment_report.EnhancedSentimentReporter._format_urgency_level",
              return_value="Medium"), \
         patch("src.modules.reporters.enhanced_sentiment_report.EnhancedSentimentReporter._format_frustration_level",
              return_value="Low"), \
         patch("src.modules.reporters.enhanced_sentiment_report.EnhancedSentimentReporter._extract_emotions",
              return_value={"frustrated": 2, "worried": 1}), \
         patch("src.modules.reporters.enhanced_sentiment_report.EnhancedSentimentReporter._extract_key_phrases",
              return_value=["system crashing", "important deadline"]), \
         patch("src.modules.reporters.enhanced_sentiment_report.EnhancedSentimentReporter._generate_executive_summary",
              return_value="Executive summary\n\nDetailed analysis shows..."):
        yield
