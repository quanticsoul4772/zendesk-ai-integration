"""
Workflow Integration Test Module

This module contains tests for the integration of different components in a realistic workflow scenario.
"""

import pytest
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def test_ticket_workflow_with_caching(zendesk_client, ai_analyzer):
    """Test the entire workflow with caching to ensure it works correctly."""
    # Set up test parameters
    status = "open"  # Fetch open tickets
    limit = 5  # Limit to 5 tickets (to keep the test reasonable)
    
    # Workflow #1: First Run (Cold Cache)
    logger.info("WORKFLOW #1: COLD CACHE")
    
    # Record start time
    start_time = time.time()
    
    # Step 1: Fetch tickets (should be cache miss)
    logger.info("Step 1: Fetching Tickets")
    step_start = time.time()
    tickets = zendesk_client.fetch_tickets(status=status, limit=limit)
    step_duration = time.time() - step_start
    logger.info(f"- Fetched {len(tickets)} tickets in {step_duration:.2f} seconds")
    
    # Skip the test if no tickets are found
    if not tickets:
        pytest.skip("No tickets found for workflow test")
    
    # Step 2: Analyze tickets using batch processing
    logger.info("Step 2: Analyzing Tickets with Batch Processing")
    step_start = time.time()
    analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=True)
    step_duration = time.time() - step_start
    logger.info(f"- Analyzed {len(analyses)} tickets in {step_duration:.2f} seconds")
    
    # Record total time for first workflow
    total_duration_first = time.time() - start_time
    logger.info(f"Total Workflow #1 Duration: {total_duration_first:.2f} seconds")
    
    # Workflow #2: Second Run (Warm Cache)
    logger.info("WORKFLOW #2: WARM CACHE")
    
    # Record start time
    start_time = time.time()
    
    # Step 1: Fetch tickets again (should be cache hit)
    logger.info("Step 1: Fetching Tickets Again")
    step_start = time.time()
    tickets_again = zendesk_client.fetch_tickets(status=status, limit=limit)
    second_fetch_duration = time.time() - step_start
    logger.info(f"- Fetched {len(tickets_again)} tickets in {second_fetch_duration:.2f} seconds")
    
    # Step 2: Analyze tickets using batch processing
    logger.info("Step 2: Analyzing Tickets with Batch Processing")
    step_start = time.time()
    analyses_again = ai_analyzer.analyze_tickets_batch(tickets_again, use_claude=True)
    step_duration = time.time() - step_start
    logger.info(f"- Analyzed {len(analyses_again)} tickets in {step_duration:.2f} seconds")
    
    # Record total time for second workflow
    total_duration_second = time.time() - start_time
    logger.info(f"Total Workflow #2 Duration: {total_duration_second:.2f} seconds")
    
    # Performance Comparison
    logger.info("PERFORMANCE COMPARISON")
    
    # Check cache hit metrics
    cache_stats = zendesk_client.cache.get_stats()
    logger.info(f"Cache Statistics: {cache_stats}")
    
    # Check if ticket fetching was faster with cache
    assert second_fetch_duration < 0.1, "Ticket fetch time should improve significantly with cache"
    
    # Compare overall workflow times
    assert total_duration_second < total_duration_first, "Overall workflow should be faster with cache"
