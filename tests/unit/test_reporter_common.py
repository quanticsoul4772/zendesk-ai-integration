"""
Unit Tests for Common Reporter Functionality

Tests common functionality shared across reporter modules.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
import io

# Import sample reporter for testing
from src.modules.reporters.sentiment_report import SentimentReporter


class TestReporterCommon:
    """Test suite for common reporter functionality."""
    
    @pytest.fixture
    def reporter(self):
        """Create a reporter instance for testing."""
        return SentimentReporter()
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies for testing."""
        mock_zendesk = MagicMock()
        mock_db = MagicMock()
        
        return {
            "zendesk_client": mock_zendesk,
            "db_repository": mock_db
        }
    
    def test_output_to_console(self, reporter):
        """Test output to console."""
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Call the method
            test_content = "Test output to console"
            reporter.output(test_content)
            
            # Check stdout
            output = captured_output.getvalue()
            assert test_content in output
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_output_to_file(self, reporter, tmp_path):
        """Test output to file."""
        # Setup
        output_file = str(tmp_path / "test_output.txt")
        test_content = "Test output to file"
        
        # Call the method with file output
        with patch('builtins.open', create=True) as mock_open:
            reporter.output(test_content, output_file)
            
            # Check file was written
            mock_open.assert_called_once_with(output_file, 'w', encoding='utf-8')
            mock_open.return_value.__enter__.return_value.write.assert_called_once_with(test_content)
    
    def test_calculate_time_period(self, reporter):
        """Test time period calculation."""
        # Test with days
        days = 7
        start_date, time_period = reporter._calculate_time_period(days=days)
        
        # Check result
        assert isinstance(start_date, datetime)
        delta = datetime.utcnow() - start_date
        assert delta.days == days
        assert time_period == f"the last {days} days"
    
    def test_calculate_time_period_with_view(self, reporter, mock_dependencies):
        """Test time period calculation with view."""
        # Configure the mock zendesk client
        mock_zendesk = mock_dependencies["zendesk_client"]
        
        # Configure mock view
        mock_view = MagicMock()
        mock_view.title = "Test View"
        mock_zendesk.get_view_by_id.return_value = mock_view
        
        # Test with view
        view_id = "12345"
        start_date, time_period = reporter._calculate_time_period(view=view_id, zendesk_client=mock_zendesk)
        
        # Check result
        assert time_period.startswith("the last")
        assert "Test View" in time_period
    
    def test_calculate_time_period_with_views(self, reporter, mock_dependencies):
        """Test time period calculation with multiple views."""
        # Configure the mock zendesk client
        mock_zendesk = mock_dependencies["zendesk_client"]
        
        # Configure mock views
        mock_view1 = MagicMock()
        mock_view1.id = "12345"
        mock_view1.title = "Test View 1"
        
        mock_view2 = MagicMock()
        mock_view2.id = "67890"
        mock_view2.title = "Test View 2"
        
        # Configure get_view_by_id to return the appropriate view
        def mock_get_view_by_id(view_id):
            if view_id == "12345":
                return mock_view1
            elif view_id == "67890":
                return mock_view2
            return None
            
        mock_zendesk.get_view_by_id.side_effect = mock_get_view_by_id
        
        # Test with multiple views
        views = ["12345", "67890"]
        start_date, time_period = reporter._calculate_time_period(
            views=views, 
            days=7,
            zendesk_client=mock_zendesk
        )
        
        # Check result
        assert time_period.startswith("the last 7 days in views:")
        assert "Test View 1" in time_period
        assert "Test View 2" in time_period
    
    def test_get_view_by_id_or_name(self, reporter, mock_dependencies):
        """Test getting view by ID or name."""
        # Configure mocks
        mock_view = MagicMock()
        mock_view.id = "12345"
        mock_view.title = "Test View"
        
        mock_dependencies["zendesk_client"].get_view_by_id.return_value = mock_view
        mock_dependencies["zendesk_client"].get_view_by_name.return_value = None
        
        # Test with ID
        view = reporter._get_view_by_id_or_name("12345", mock_dependencies["zendesk_client"])
        
        # Check result
        assert view is not None
        assert view.id == "12345"
        assert view.title == "Test View"
        mock_dependencies["zendesk_client"].get_view_by_id.assert_called_once_with("12345")
        mock_dependencies["zendesk_client"].get_view_by_name.assert_not_called()
    
    def test_get_view_by_id_or_name_with_name(self, reporter, mock_dependencies):
        """Test getting view by name when ID lookup fails."""
        # Configure mocks
        mock_zendesk = mock_dependencies["zendesk_client"]
        
        # First, configure ID lookup to fail
        mock_zendesk.get_view_by_id.return_value = None
        
        # Configure name lookup to succeed
        mock_view = MagicMock()
        mock_view.id = "12345"
        mock_view.title = "Test View"
        
        # Add get_view_by_name method to mock
        mock_zendesk.get_view_by_name = MagicMock(return_value=mock_view)
        
        # Test with name
        view = reporter._get_view_by_id_or_name("Test View", mock_zendesk)
        
        # Check result
        assert view is not None
        assert view.id == "12345"
        assert view.title == "Test View"
        mock_zendesk.get_view_by_id.assert_called_once_with("Test View")
        mock_zendesk.get_view_by_name.assert_called_once_with("Test View")
    
    def test_format_timestamp(self, reporter):
        """Test timestamp formatting."""
        # Test data
        timestamp = datetime(2023, 1, 1, 12, 30, 45)
        
        # Call the method
        formatted = reporter._format_timestamp(timestamp)
        
        # Check result
        assert "2023-01-01" in formatted
        assert "12:30:45" in formatted
    
    def test_format_percentage(self, reporter):
        """Test percentage formatting."""
        # Test various values
        assert reporter._format_percentage(0) == "0.0%"
        assert reporter._format_percentage(0.5) == "50.0%"
        assert reporter._format_percentage(1) == "100.0%"
        assert reporter._format_percentage(0.333) == "33.3%"
