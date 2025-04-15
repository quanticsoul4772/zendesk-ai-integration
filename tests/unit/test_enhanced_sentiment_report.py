"""
Unit Tests for Enhanced Sentiment Report Module

Tests the functionality of the enhanced_sentiment_report.py module.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
import io

# Import module to test
from src.modules.reporters.enhanced_sentiment_report import EnhancedSentimentReporter


class TestEnhancedSentimentReporter:
    """Test suite for Enhanced Sentiment Reporter functionality."""
    
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
                    "technical_expertise": 2,
                    "business_impact": {
                        "detected": True,
                        "description": "Production system down affecting multiple teams"
                    },
                    "key_phrases": ["system crashing", "deadline approaching"],
                    "emotions": ["frustrated", "worried"]
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
                    "technical_expertise": 3,
                    "business_impact": {"detected": False},
                    "key_phrases": ["memory upgrade", "performance improvement"],
                    "emotions": ["neutral"]
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
                    "technical_expertise": 1,
                    "business_impact": {"detected": False},
                    "key_phrases": ["thank you", "great service"],
                    "emotions": ["grateful", "satisfied"]
                },
                "category": "general_inquiry",
                "component": "none",
                "priority_score": 1,
                "timestamp": datetime.utcnow() - timedelta(days=3)
            }
        ]
    
    def test_init(self, mock_dependencies):
        """Test reporter initialization."""
        reporter = EnhancedSentimentReporter()
        
        # Check initial state
        assert reporter is not None
    
    def test_generate_report_no_data(self, mock_dependencies):
        """Test report generation with no data."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Generate report
            report = reporter.generate_report(
                zendesk_client=mock_dependencies["zendesk_client"],
                db_repository=mock_dependencies["db_repository"],
                days=7
            )
            
            # Check output
            output = captured_output.getvalue()
            assert "ENHANCED SENTIMENT ANALYSIS REPORT" in output
            assert "Total tickets analyzed: 0" in output
            
            # Check returned report
            assert report is not None
            
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_data(self, mock_dependencies, sample_analyses):
        """Test report generation with sample data."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Configure mock to return sample data
        mock_dependencies["db_repository"].find_analyses_since.return_value = sample_analyses
        mock_dependencies["db_repository"].get_sentiment_statistics.return_value = {
            "count": 3,
            "time_period": "week",
            "sentiment_distribution": {"positive": 1, "negative": 1, "neutral": 1},
            "average_urgency": 2.33,
            "average_frustration": 1.67,
            "average_priority": 4.0,
            "business_impact_count": 1,
            "business_impact_percentage": 33.3
        }
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Generate report
            report = reporter.generate_report(
                zendesk_client=mock_dependencies["zendesk_client"],
                db_repository=mock_dependencies["db_repository"],
                days=7,
                analyses=sample_analyses
            )
            
            # Check output
            output = captured_output.getvalue()
            assert "ENHANCED SENTIMENT ANALYSIS REPORT" in output
            
            # Check returned report
            assert report is not None
            assert "ENHANCED SENTIMENT ANALYSIS REPORT" in report
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_output_file(self, mock_dependencies, sample_analyses, tmp_path):
        """Test report generation with output to file."""
        # Setup
        reporter = EnhancedSentimentReporter()
        output_file = str(tmp_path / "test_report.txt")
        
        # Configure mock to return sample data
        mock_dependencies["db_repository"].find_analyses_since.return_value = sample_analyses
        
        # Generate report with output file
        with patch('builtins.open', create=True) as mock_open:
            report = reporter.generate_report(
                mock_dependencies["zendesk_client"],
                mock_dependencies["db_repository"],
                days=7,
                output_file=output_file
            )
            
            # Check file was written
            mock_open.assert_called_once_with(output_file, 'w', encoding='utf-8')
            mock_open.return_value.__enter__.return_value.write.assert_called()
    
    def test_generate_executive_summary(self, sample_analyses):
        """Test executive summary generation."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Get statistics
        stats = {
            "count": 3,
            "sentiment_distribution": {"positive": 1, "negative": 1, "neutral": 1},
            "average_urgency": 2.33,
            "average_frustration": 1.67,
            "average_priority": 4.0,
            "business_impact_count": 1,
            "business_impact_percentage": 33.3
        }
        
        # Call the method
        summary = reporter._generate_executive_summary(stats, sample_analyses)
        
        # Check result
        assert "EXECUTIVE SUMMARY" in summary
        assert "Total Tickets Analyzed: 3" in summary
        assert "33.3% of tickets indicate business impact" in summary
    
    def test_format_urgency_level(self):
        """Test urgency level formatting."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Test various levels
        assert "Very Low" in reporter._format_urgency_level(1)
        assert "Low" in reporter._format_urgency_level(2)
        assert "Medium" in reporter._format_urgency_level(3)
        assert "High" in reporter._format_urgency_level(4)
        assert "Critical" in reporter._format_urgency_level(5)
        
        # Test with percentage
        assert "20%" in reporter._format_urgency_level(1)
        assert "40%" in reporter._format_urgency_level(2)
        assert "60%" in reporter._format_urgency_level(3)
        assert "80%" in reporter._format_urgency_level(4)
        assert "100%" in reporter._format_urgency_level(5)
    
    def test_format_frustration_level(self):
        """Test frustration level formatting."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Test various levels
        assert "None" in reporter._format_frustration_level(1)
        assert "Slight" in reporter._format_frustration_level(2)
        assert "Moderate" in reporter._format_frustration_level(3)
        assert "High" in reporter._format_frustration_level(4)
        assert "Extreme" in reporter._format_frustration_level(5)
        
        # Test with percentage
        assert "20%" in reporter._format_frustration_level(1)
        assert "40%" in reporter._format_frustration_level(2)
        assert "60%" in reporter._format_frustration_level(3)
        assert "80%" in reporter._format_frustration_level(4)
        assert "100%" in reporter._format_frustration_level(5)
    
    def test_extract_emotions(self, sample_analyses):
        """Test emotion extraction from analyses."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Call the method
        emotions = reporter._extract_emotions(sample_analyses)
        
        # Check result
        assert isinstance(emotions, dict)
        assert "frustrated" in emotions
        assert "worried" in emotions
        assert "grateful" in emotions
        assert "satisfied" in emotions
        assert emotions["frustrated"] == 1
        assert emotions["worried"] == 1
    
    def test_extract_key_phrases(self, sample_analyses):
        """Test key phrase extraction from analyses."""
        # Setup
        reporter = EnhancedSentimentReporter()
        
        # Call the method
        phrases = reporter._extract_key_phrases(sample_analyses)
        
        # Check result
        assert isinstance(phrases, list)
        assert len(phrases) > 0
        assert any("system crashing" in phrase for phrase in phrases)
        assert any("deadline approaching" in phrase for phrase in phrases)
        assert any("thank you" in phrase for phrase in phrases)
