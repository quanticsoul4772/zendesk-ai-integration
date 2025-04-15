"""
Test suite for the menu actions functionality.

This module contains tests for the ZendeskMenuActions class.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path for importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from src.modules.menu.menu_actions import ZendeskMenuActions

# Create test fixtures
@pytest.fixture
def mock_zendesk_client():
    """Create a mock ZendeskClient for testing."""
    client = MagicMock()
    
    # Mock fetch_tickets_from_view method
    client.fetch_tickets_from_view.return_value = [
        MagicMock(id=1, subject="Test Ticket 1", description="Description 1"),
        MagicMock(id=2, subject="Test Ticket 2", description="Description 2"),
    ]
    
    return client

@pytest.fixture
def mock_ai_analyzer():
    """Create a mock AIAnalyzer for testing."""
    analyzer = MagicMock()
    
    # Mock analyze_tickets_batch method
    analyzer.analyze_tickets_batch.return_value = [
        {"ticket_id": 1, "sentiment": {"polarity": "positive"}, "priority_score": 3},
        {"ticket_id": 2, "sentiment": {"polarity": "negative"}, "priority_score": 8},
    ]
    
    return analyzer

@pytest.fixture
def mock_db_repository():
    """Create a mock DBRepository for testing."""
    repo = MagicMock()
    
    # Set up repository methods
    repo.save_analysis.return_value = "abc123"
    repo.get_user_preferences.return_value = {"recent_views": []}
    
    return repo

@pytest.fixture
def mock_pending_reporter():
    """Create a mock PendingReporter for testing."""
    reporter = MagicMock()
    reporter.generate_report.return_value = "Mock Pending Report"
    return reporter

@pytest.fixture
def mock_sentiment_reporter():
    """Create a mock EnhancedSentimentReporter for testing."""
    reporter = MagicMock()
    reporter.generate_report.return_value = "Mock Sentiment Report"
    return reporter

@pytest.fixture
def report_modules(mock_pending_reporter, mock_sentiment_reporter):
    """Create a dictionary of report modules for testing."""
    return {
        "pending": mock_pending_reporter,
        "sentiment_enhanced": mock_sentiment_reporter,
    }

# Test the ZendeskMenuActions class
class TestZendeskMenuActions:
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_initialization(self, mock_create_menu, mock_zendesk_client, mock_ai_analyzer, 
                           mock_db_repository, report_modules):
        """Test that ZendeskMenuActions initializes correctly with components."""
        # Setup
        mock_menu = MagicMock()
        mock_menu.show.return_value = None  # Simulate Esc key press
        mock_create_menu.return_value = mock_menu
        
        # Execute
        menu = ZendeskMenuActions(
            zendesk_client=mock_zendesk_client,
            ai_analyzer=mock_ai_analyzer,
            db_repository=mock_db_repository,
            report_modules=report_modules
        )
        
        # Verify
        assert menu.zendesk_client == mock_zendesk_client
        assert menu.ai_analyzer == mock_ai_analyzer
        assert menu.db_repository == mock_db_repository
        assert menu.report_modules == report_modules
        assert "run_sentiment_analysis" in menu.action_handlers
        assert "generate_report" in menu.action_handlers
        assert "view_tickets" in menu.action_handlers
    
    @patch('src.modules.menu.zendesk_menu.create_menu')
    @patch('builtins.print')
    @patch('builtins.input', return_value='')
    def test_action_run_sentiment_analysis(self, mock_input, mock_print, mock_create_menu,
                                         mock_zendesk_client, mock_ai_analyzer, 
                                         mock_db_repository, report_modules):
        """Test the run sentiment analysis action."""
        # Setup
        mock_menu = MagicMock()
        mock_menu.show.return_value = None
        mock_create_menu.return_value = mock_menu
        
        # Configure datetime mock
        mock_datetime.now.return_value.strftime.return_value = '20250331_2200'
        menu = ZendeskMenuActions(
            zendesk_client=mock_zendesk_client,
            ai_analyzer=mock_ai_analyzer,
            db_repository=mock_db_repository,
            report_modules=report_modules
        )
        
        # Execute
        menu._action_run_sentiment_analysis(123, "Test View")
        
        # Verify
        mock_zendesk_client.fetch_tickets_from_view.assert_called_once_with(123)
        mock_ai_analyzer.analyze_tickets_batch.assert_called_once()
        assert mock_db_repository.save_analysis.call_count == 2  # Two tickets
    
    @patch('src.modules.menu.zendesk_menu.create_menu')
    @patch('builtins.print')
    @patch('builtins.input', return_value='')
    @patch('src.modules.menu.menu_actions.datetime')
    def test_action_generate_report(self, mock_datetime, mock_input, mock_print, mock_create_menu,
                                  mock_zendesk_client, mock_ai_analyzer, 
                                  mock_db_repository, report_modules):
        """Test the generate report action."""
        # Setup
        mock_menu = MagicMock()
        mock_menu.show.return_value = None
        mock_create_menu.return_value = mock_menu
        menu = ZendeskMenuActions(
            zendesk_client=mock_zendesk_client,
            ai_analyzer=mock_ai_analyzer,
            db_repository=mock_db_repository,
            report_modules=report_modules
        )
        
        # Execute - Pending report
        menu._action_generate_report(123, "Test View", "pending")
        
        # Verify pending report
        report_modules["pending"].generate_report.assert_called_once()
        
        # Reset mocks
        mock_print.reset_mock()
        mock_input.reset_mock()
        
        # Execute - Enhanced report with no analyses
        mock_db_repository.find_analyses_for_view.return_value = []
        with patch('builtins.input', return_value='n'):  # Simulate user declining to run analysis
            menu._action_generate_report(123, "Test View", "enhanced")
        
        # Verify user was prompted but analysis was not run
        assert mock_ai_analyzer.analyze_tickets_batch.call_count == 1  # Still just the one call from earlier
    
    @patch('src.modules.menu.zendesk_menu.create_menu')
    @patch('builtins.print')
    @patch('builtins.input', return_value='')
    @patch('webbrowser.open')
    def test_action_view_tickets(self, mock_webbrowser, mock_input, mock_print, mock_create_menu,
                               mock_zendesk_client, mock_db_repository):
        """Test the view tickets action."""
        # Setup
        mock_menu = MagicMock()
        mock_menu.show.return_value = None
        mock_create_menu.return_value = mock_menu
        # Set up the subdomain property
        mock_zendesk_client.client.subdomain = "testcompany"
        
        menu = ZendeskMenuActions(
            zendesk_client=mock_zendesk_client,
            db_repository=mock_db_repository
        )
        
        # Execute
        menu._action_view_tickets(123, "Test View")
        
        # Verify
        mock_webbrowser.assert_called_once_with("https://testcompany.zendesk.com/agent/filters/123")
