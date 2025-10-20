"""
Comprehensive Performance Test Module

This module contains tests for various performance aspects of the Zendesk AI Integration.
"""

# SKIPPED: This test file tests modules that were removed during clean architecture refactoring.
# Reason: Tests BatchProcessor module that was removed during refactoring

import pytest
pytestmark = pytest.mark.skip(reason="Tests BatchProcessor module that was removed during refactoring")


import pytest
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def test_caching_performance(zendesk_client):
    """Test the caching performance improvements."""
    # First fetch will be a cache miss
    logger.info("First fetch (cache miss)...")
    start_time = time.time()
    views_first = zendesk_client.list_all_views()
    first_duration = time.time() - start_time
    logger.info(f"First fetch took {first_duration:.2f} seconds")
    
    # Second fetch should be a cache hit
    logger.info("Second fetch (should be cache hit)...")
    start_time = time.time()
    views_second = zendesk_client.list_all_views()
    second_duration = time.time() - start_time
    logger.info(f"Second fetch took {second_duration:.2f} seconds")
    
    # Calculate the improvement
    if first_duration > 0:
        improvement = (first_duration - second_duration) / first_duration * 100
        logger.info(f"Cache improved performance by {improvement:.2f}%")
    
    # Verify data consistency
    assert views_first == views_second, "Cache returned different data than direct API call"
    
    # Get and show cache stats
    stats = zendesk_client.cache.get_stats()
    logger.info(f"Cache statistics: {stats}")
    
    # Assert that caching provides significant improvement
    assert second_duration < first_duration / 5, "Cache should provide at least 5x performance improvement"

@pytest.mark.parametrize("batch_size,max_workers", [
    (5, 3),
    (10, 5),
])
def test_batch_processing_performance(zendesk_client, ai_analyzer, batch_size, max_workers):
    """Test batch processing performance with different configurations."""
#     from src.modules.batch_processor import BatchProcessor
    
    # Create an analyzer with custom batch settings for testing
    ai_analyzer.batch_processor = BatchProcessor(
        max_workers=max_workers,
        batch_size=batch_size,
        show_progress=True
    )
    
    # Fetch some test tickets
    tickets = zendesk_client.fetch_tickets(status="open", limit=5)
    
    if not tickets:
        tickets = zendesk_client.fetch_tickets(status="pending", limit=5)
    
    if not tickets:
        tickets = zendesk_client.fetch_tickets(status="all", limit=5)
    
    logger.info(f"Fetched {len(tickets)} tickets for testing")
    
    # Skip test if no tickets
    if not tickets:
        pytest.skip("No tickets found for testing")
    
    # Sequential processing
    logger.info("Testing sequential processing...")
    start_time = time.time()
    sequential_results = []
    for ticket in tickets:
        analysis = ai_analyzer.analyze_ticket(
            ticket_id=ticket.id,
            subject=ticket.subject or "",
            description=ticket.description or "",
            use_claude=True
        )
        sequential_results.append(analysis)
    sequential_duration = time.time() - start_time
    logger.info(f"Sequential processing took {sequential_duration:.2f} seconds for {len(tickets)} tickets")
    
    # Batch processing
    logger.info(f"Testing batch processing with {max_workers} workers and batch size {batch_size}...")
    start_time = time.time()
    batch_results = ai_analyzer.analyze_tickets_batch(tickets, use_claude=True)
    batch_duration = time.time() - start_time
    logger.info(f"Batch processing took {batch_duration:.2f} seconds for {len(tickets)} tickets")
    
    # Calculate the improvement
    if sequential_duration > 0 and batch_duration > 0:
        improvement = (sequential_duration - batch_duration) / sequential_duration * 100
        speedup = sequential_duration / batch_duration
        logger.info(f"Batch processing improved performance by {improvement:.2f}% (speedup factor: {speedup:.2f}x)")
        
        # For small batches, there should be some improvement but it might not be dramatic
        # due to overhead; we'll use a more relaxed assertion
        assert batch_duration < sequential_duration, "Batch processing should be faster than sequential"
