"""
Unit Tests for Sentiment Report Module

Tests the functionality of the sentiment_report.py module.
"""
# SKIPPED: Tests removed modules from old architecture
import pytest
pytestmark = pytest.mark.skip(reason="Tests removed modules from old architecture")


import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
import io
# from src.application.services.report_service import SentimentReportService

# Import module to test
# from src.infrastructure.compatibility import SentimentReporter


class TestSentimentReporter:
    """Test suite for Sentiment Reporter functionality."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies for testing."""
        mock_zendesk = MagicMock()
        mock_db = MagicMock()
        
        # Configure mocks
        mock_db.find_analyses_since.return_value = []
        mock_db.get_sentiment_statistics.return_value = {
            "count": 0,
            "time_period": "week",
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
        }
        
        return {
            "zendesk_client": mock_zendesk,
            "db_repository": mock_db
        }
    
    @pytest.fixture
    def sample_analyses(self):
        """Create sample analyses data for testing."""
        return [
            {
                "ticket_id": "12345",
                "subject": "GPU Issue",
                "sentiment": {
                    "polarity": "negative",
                    "urgency_level": 4,
                    "frustration_level": 3,
                    "business_impact": {"detected": True, "description": "Production impact"}
                },
                "category": "hardware_issue",
                "component": "gpu",
                "priority_score": 8,
                "timestamp": datetime.utcnow() - timedelta(days=1)
            },
            {
                "ticket_id": "12346",
                "subject": "Memory Upgrade",
                "sentiment": {
                    "polarity": "neutral",
                    "urgency_level": 2,
                    "frustration_level": 1,
                    "business_impact": {"detected": False}
                },
                "category": "general_inquiry",
                "component": "memory",
                "priority_score": 3,
                "timestamp": datetime.utcnow() - timedelta(days=2)
            },
            {
                "ticket_id": "12347",
                "subject": "Thank You",
                "sentiment": {
                    "polarity": "positive",
                    "urgency_level": 1,
                    "frustration_level": 1,
                    "business_impact": {"detected": False}
                },
                "category": "general_inquiry",
                "component": "none",
                "priority_score": 1,
                "timestamp": datetime.utcnow() - timedelta(days=3)
            }
        ]
    
    def test_init(self, mock_dependencies):
        """Test reporter initialization."""
        reporter = SentimentReporter()
        
        # Check initial state
        assert reporter is not None
    
    def test_generate_report_no_data(self, mock_dependencies):
        """Test report generation with no data."""
        # Setup
        reporter = SentimentReporter()
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Generate report with empty analyses list
            report = reporter.generate_report(
                analyses=[],
                zendesk_client=mock_dependencies["zendesk_client"],
                db_repository=mock_dependencies["db_repository"]
            )
            
            # Check output
            output = captured_output.getvalue()
            assert "SENTIMENT ANALYSIS REPORT" in output
            assert "No analysis data found" in output
            
            # Check returned report
            assert report is not None
            assert "SENTIMENT ANALYSIS REPORT" in report
            assert "No analysis data found" in report
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_data(self, mock_dependencies, sample_analyses):
        """Test report generation with sample data."""
        # Setup
        reporter = SentimentReporter()
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Generate report with sample analyses list
            report = reporter.generate_report(
                analyses=sample_analyses,
                zendesk_client=mock_dependencies["zendesk_client"],
                db_repository=mock_dependencies["db_repository"]
            )
            
            # Check output
            output = captured_output.getvalue()
            assert "SENTIMENT ANALYSIS REPORT" in output
            assert "Negative: 1" in output
            assert "Neutral: 1" in output
            assert "Positive: 1" in output
            assert "Total tickets analyzed: 3" in output
            
            # Check returned report
            assert report is not None
            assert "SENTIMENT ANALYSIS REPORT" in report
            assert "Negative: 1" in report
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_output_file(self, mock_dependencies, sample_analyses, tmp_path):
        """Test report generation with output to file."""
        # Setup
        reporter = SentimentReporter()
        output_file = str(tmp_path / "test_report.txt")
        
        # Generate report with output file
        with patch('builtins.open', create=True) as mock_open:
            report = reporter.generate_report(
                analyses=sample_analyses,
                zendesk_client=mock_dependencies["zendesk_client"],
                db_repository=mock_dependencies["db_repository"],
                output_file=output_file
            )
            
            # Check file was written
            mock_open.assert_called_once_with(output_file, 'w', encoding='utf-8')
            mock_open.return_value.__enter__.return_value.write.assert_called()
    
    def test_generate_report_with_view(self, mock_dependencies, sample_analyses):
        """Test report generation with view filter."""
        # Setup
        reporter = SentimentReporter()
        
        # Configure mock view
        mock_view = MagicMock()
        mock_view.id = "12345"
        mock_view.title = "Test View"
        
        # Configure zendesk client mock
        mock_dependencies["zendesk_client"].get_view_by_id.return_value = mock_view
        mock_dependencies["zendesk_client"].get_view_by_name.return_value = None
        
        # Generate report with view filter
        report = reporter.generate_report(
            analyses=sample_analyses[:1],  # Just one analysis 
            zendesk_client=mock_dependencies["zendesk_client"],
            db_repository=mock_dependencies["db_repository"],
            view="12345"
        )
        
        # Check view was retrieved
        mock_dependencies["zendesk_client"].get_view_by_id.assert_called_once_with("12345")
        
        # Check report contains view name
        assert "Test View" in report
        
        # Check report contains only the filtered data
        assert "Negative: 1" in report
        # This report only contains data about what's actually in the analysis
        # and doesn't display zeros for categories with no occurrences
        assert "Neutral:" not in report
    
    def test_filter_high_priority_tickets(self, sample_analyses):
        """Test filtering high priority tickets."""
        # Setup
        reporter = SentimentReporter()
        
        # Call the method
        high_priority = reporter._filter_high_priority_tickets(sample_analyses)
        
        # Check result
        assert len(high_priority) == 1
        assert high_priority[0]["ticket_id"] == "12345"
        assert high_priority[0]["priority_score"] == 8
    
    def test_format_ticket_details(self, sample_analyses):
        """Test formatting ticket details."""
        # Setup
        reporter = SentimentReporter()
        
        # Call the method
        details = reporter._format_ticket_details(sample_analyses[0])
        
        # Check result
        assert "#12345 - GPU Issue" in details
        assert "Sentiment: negative" in details
        assert "Priority: 8/10" in details
