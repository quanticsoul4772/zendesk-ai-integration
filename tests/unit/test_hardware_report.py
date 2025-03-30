"""
Unit Tests for Hardware Report Module

Tests the functionality of the hardware_report.py module.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
import io

# Import module to test
from src.modules.reporters.hardware_report import HardwareReporter


class TestHardwareReporter:
    """Test suite for Hardware Reporter functionality."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies for testing."""
        mock_zendesk = MagicMock()
        mock_db = MagicMock()
        
        # Configure mocks
        mock_db.find_analyses_since.return_value = []
        
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
                "subject": "CPU Overheating",
                "sentiment": {
                    "polarity": "negative",
                    "urgency_level": 3,
                    "frustration_level": 2,
                    "business_impact": {"detected": False}
                },
                "category": "hardware_issue",
                "component": "cpu",
                "priority_score": 5,
                "timestamp": datetime.utcnow() - timedelta(days=3)
            },
            {
                "ticket_id": "12348",
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
    
    @pytest.fixture
    def sample_tickets(self):
        """Create sample tickets for testing."""
        tickets = []
        for i in range(4):
            ticket = MagicMock()
            ticket.id = str(12345 + i)
            ticket.subject = f"Test Subject {i}"
            ticket.description = f"Test Description {i}"
            ticket.status = "open" if i < 2 else "pending"
            tickets.append(ticket)
        return tickets
    
    def test_init(self, mock_dependencies):
        """Test reporter initialization."""
        reporter = HardwareReporter()
        
        # Check initial state
        assert reporter is not None
    
    def test_generate_report_no_data(self, mock_dependencies):
        """Test report generation with no data."""
        # Setup
        reporter = HardwareReporter()
        
        # Configure mock to return no tickets
        mock_dependencies["zendesk_client"].fetch_tickets.return_value = []
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Get tickets for the report
            tickets = mock_dependencies["zendesk_client"].fetch_tickets(view_id="12345")
            
            # Generate report
            report = reporter.generate_report(tickets)
            
            # Check output
            output = captured_output.getvalue()
            
            # Check returned report
            assert report is not None
            assert "No hardware component data found" in report
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_data(self, mock_dependencies, sample_tickets, sample_analyses):
        """Test report generation with sample data."""
        # Setup
        reporter = HardwareReporter()
        
        # Configure mocks
        mock_dependencies["zendesk_client"].fetch_tickets.return_value = sample_tickets
        
        # Map tickets to analyses
        def get_analysis_side_effect(ticket_id):
            for analysis in sample_analyses:
                if analysis["ticket_id"] == ticket_id:
                    return analysis
            return None
        
        mock_dependencies["db_repository"].get_analysis_by_ticket_id.side_effect = get_analysis_side_effect
        
        # Capture stdout to test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Get tickets for the report
            tickets = mock_dependencies["zendesk_client"].fetch_tickets(status="open")
            
            # Generate report
            report = reporter.generate_report(tickets)
            
            # Check output
            output = captured_output.getvalue()
            
            # Check returned report
            assert report is not None
            assert "HARDWARE COMPONENT REPORT" in report
        finally:
            sys.stdout = sys.__stdout__  # Reset stdout
    
    def test_generate_report_with_output_file(self, mock_dependencies, sample_tickets, sample_analyses, tmp_path):
        """Test report generation with output to file."""
        # Setup
        reporter = HardwareReporter()
        output_file = str(tmp_path / "test_report.txt")
        
        # Configure mocks
        mock_dependencies["zendesk_client"].fetch_tickets.return_value = sample_tickets
        
        # Map tickets to analyses
        def get_analysis_side_effect(ticket_id):
            for analysis in sample_analyses:
                if analysis["ticket_id"] == ticket_id:
                    return analysis
            return None
        
        mock_dependencies["db_repository"].get_analysis_by_ticket_id.side_effect = get_analysis_side_effect
        
        # Get tickets for the report
        tickets = mock_dependencies["zendesk_client"].fetch_tickets(status="open")
        
        # Generate report
        report = reporter.generate_report(tickets)
        
        # Write report to file
        with patch('builtins.open', create=True) as mock_open:
            reporter.output(report, output_file)
            
            # Check file was written
            mock_open.assert_called_once_with(output_file, 'w', encoding='utf-8')
            mock_open.return_value.__enter__.return_value.write.assert_called()
    
    def test_analyze_component_distribution(self, sample_analyses):
        """Test component distribution analysis."""
        # Setup
        reporter = HardwareReporter()
        
        # Call the method
        distribution = reporter._analyze_component_distribution(sample_analyses)
        
        # Check result
        assert len(distribution) > 0
        assert "counts" in distribution
        assert "gpu" in distribution["counts"]
        assert "memory" in distribution["counts"]
        assert "cpu" in distribution["counts"]
        assert distribution["counts"]["gpu"] == 1
        assert distribution["counts"]["memory"] == 1
        assert distribution["counts"]["cpu"] == 1
    
    def test_format_component_distribution(self, sample_analyses):
        """Test formatting component distribution."""
        # Setup
        reporter = HardwareReporter()
        
        # Get component distribution
        distribution = reporter._analyze_component_distribution(sample_analyses)
        
        # Call the method
        formatted = reporter._format_component_distribution(distribution)
        
        # Check result
        assert "COMPONENT DISTRIBUTION" in formatted
        assert "gpu" in formatted.lower()
        assert "memory" in formatted.lower()
        assert "cpu" in formatted.lower()
    
    def test_format_ticket_details(self, sample_analyses):
        """Test formatting ticket details."""
        # Setup
        reporter = HardwareReporter()
        
        # Call the method
        details = reporter._format_ticket_details(sample_analyses[0])
        
        # Check result
        assert "#12345" in details
        assert "GPU Issue" in details
        assert "gpu" in details
        assert "hardware_issue" in details
