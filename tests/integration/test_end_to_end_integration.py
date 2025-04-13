"""
End-to-end integration tests for the Zendesk AI Integration.

These tests verify that all components work together correctly.
"""
import pytest
import logging
import os
from datetime import datetime
from src.application.use_cases.generate_report_use_case import GenerateReportUseCase

logger = logging.getLogger(__name__)

def test_full_ticket_analysis_workflow(zendesk_client, ai_analyzer):
    """Test the complete workflow from fetching tickets to generating analysis."""
    # We've already mocked the necessary components, so we don't need to skip
    # Fetch a small number of tickets for testing
    tickets = zendesk_client.get_tickets(status="open", limit=2)
    
    if not tickets or len(tickets) == 0:
        tickets = zendesk_client.get_tickets(status="pending", limit=2)
    
    if not tickets or len(tickets) == 0:
        tickets = zendesk_client.get_tickets(status="all", limit=2)
    
    if not tickets or len(tickets) == 0:
        pytest.skip("No tickets found for integration test")
    
    # Log ticket details for debugging
    for ticket in tickets:
        logger.info(f"Test using ticket #{ticket.id}: {ticket.subject}")
    
    # Process tickets using AI analyzer
    analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=True)
    
    # Verify results
    assert len(analyses) == len(tickets), f"Expected {len(tickets)} analyses but got {len(analyses)}"
    
    for ticket_id, analysis in analyses.items():
        # Check that analysis has expected structure
        assert "category" in analysis, f"Analysis for ticket {ticket_id} missing 'category'"
        assert "sentiment" in analysis, f"Analysis for ticket {ticket_id} missing 'sentiment'"
        assert "priority_score" in analysis, f"Analysis for ticket {ticket_id} missing 'priority_score'"
        
        # Check that sentiment analysis has expected structure
        sentiment = analysis["sentiment"]
        assert "polarity" in sentiment, f"Sentiment for ticket {ticket_id} missing 'polarity'"
        assert "urgency_level" in sentiment, f"Sentiment for ticket {ticket_id} missing 'urgency_level'"
        
        # Log analysis results
        logger.info(f"Analysis for ticket #{ticket_id}:")
        logger.info(f"  Category: {analysis.get('category')}")
        logger.info(f"  Priority: {analysis.get('priority_score')}")
        logger.info(f"  Sentiment: {sentiment.get('polarity')}, Urgency: {sentiment.get('urgency_level')}")

def test_report_generation(zendesk_client, ai_analyzer):
    """Test the report generation functionality."""
    # We've already mocked the necessary components, so we don't need to skip
    
    # Import the report generator (assuming it exists)
    try:
#         from src.infrastructure.compatibility import generate_summary_report
    except ImportError:
        pytest.skip("Report generator module not available")
    
    # Fetch tickets from a specific view
    view_id = os.getenv("TEST_VIEW_ID")
    if not view_id:
        # Use a default view or skip
        views = zendesk_client.list_all_views()
        if views:
            view_id = views[0].id
        else:
            pytest.skip("No views available for testing report generation")
    
    # Generate a report
    report_data = generate_report_use_case.execute(
        zendesk_client=zendesk_client,
        ai_analyzer=ai_analyzer,
        view_id=view_id,
        days=7,  # Last 7 days
        include_sentiment=True
    )
    
    # Verify report structure
    assert "timestamp" in report_data, "Report missing timestamp"
    assert "view_name" in report_data, "Report missing view name"
    assert "ticket_count" in report_data, "Report missing ticket count"
    assert "categories" in report_data, "Report missing categories breakdown"
    assert "sentiment_summary" in report_data, "Report missing sentiment summary"
    
    # Log report summary
    logger.info(f"Generated report for view {report_data.get('view_name')}:")
    logger.info(f"  Total tickets: {report_data.get('ticket_count')}")
    logger.info(f"  Top category: {max(report_data.get('categories', {}).items(), key=lambda x: x[1])[0] if report_data.get('categories') else 'N/A'}")
