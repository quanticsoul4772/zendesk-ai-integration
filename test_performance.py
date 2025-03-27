#!/usr/bin/env python3
"""
Performance Testing Script for Zendesk AI Integration

This script tests the performance improvements from caching and batch processing.
"""

import time
import logging
import argparse
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance_test")

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

def test_caching():
    """Test the caching functionality"""
    from src.modules.zendesk_client import ZendeskClient
    
    # Create a Zendesk client (which initializes the cache)
    client = ZendeskClient()
    
    # First fetch will be a cache miss
    logger.info("First fetch (cache miss)...")
    start_time = time.time()
    views_first = client.list_all_views()
    first_duration = time.time() - start_time
    logger.info(f"First fetch took {first_duration:.2f} seconds")
    
    # Second fetch should be a cache hit
    logger.info("Second fetch (should be cache hit)...")
    start_time = time.time()
    views_second = client.list_all_views()
    second_duration = time.time() - start_time
    logger.info(f"Second fetch took {second_duration:.2f} seconds")
    
    # Calculate the improvement
    if first_duration > 0:
        improvement = (first_duration - second_duration) / first_duration * 100
        logger.info(f"Cache improved performance by {improvement:.2f}%")
    
    # Verify data consistency
    assert views_first == views_second, "Cache returned different data than direct API call"
    
    # Get and show cache stats
    stats = client.cache.get_stats()
    logger.info(f"Cache statistics: {stats}")
    
    return {
        "first_duration": first_duration,
        "second_duration": second_duration,
        "improvement_percentage": improvement,
        "cache_stats": stats
    }

def test_batch_processing(batch_size=5, max_workers=3):
    """Test the batch processing functionality"""
    from src.modules.zendesk_client import ZendeskClient
    from src.modules.ai_analyzer import AIAnalyzer
    from src.modules.batch_processor import BatchProcessor
    
    # Create clients
    zendesk_client = ZendeskClient()
    
    # Create an analyzer with custom batch settings for testing
    ai_analyzer = AIAnalyzer()
    ai_analyzer.batch_processor = BatchProcessor(
        max_workers=max_workers,
        batch_size=batch_size,
        show_progress=True
    )
    
    # Fetch some test tickets by status instead of by view
    logger.info("Fetching tickets with status 'open' for testing")
    tickets = zendesk_client.fetch_tickets(status="open", limit=5)
    
    if not tickets:
        logger.info("No open tickets found, trying 'pending' status")
        tickets = zendesk_client.fetch_tickets(status="pending", limit=5)
    
    if not tickets:
        logger.info("No pending tickets found, trying 'all' status")
        tickets = zendesk_client.fetch_tickets(status="all", limit=5)
    
    logger.info(f"Fetched {len(tickets)} tickets for testing")
    
    if not tickets:
        logger.error("No tickets found for testing")
        return None
    
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
    if sequential_duration > 0:
        improvement = (sequential_duration - batch_duration) / sequential_duration * 100
        speedup = sequential_duration / batch_duration if batch_duration > 0 else float('inf')
        logger.info(f"Batch processing improved performance by {improvement:.2f}% (speedup factor: {speedup:.2f}x)")
    
    return {
        "tickets_count": len(tickets),
        "sequential_duration": sequential_duration,
        "batch_duration": batch_duration,
        "improvement_percentage": improvement,
        "speedup_factor": speedup,
        "max_workers": max_workers,
        "batch_size": batch_size
    }

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test performance optimizations")
    parser.add_argument(
        "--test", 
        choices=["cache", "batch", "all"], 
        default="all",
        help="Which test to run (cache, batch, or all)"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=5,
        help="Batch size for batch processing test"
    )
    parser.add_argument(
        "--max-workers", 
        type=int, 
        default=3,
        help="Maximum worker threads for batch processing test"
    )
    
    args = parser.parse_args()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "cache_test": None,
        "batch_test": None
    }
    
    if args.test in ["cache", "all"]:
        logger.info("=== TESTING CACHE PERFORMANCE ===")
        results["cache_test"] = test_caching()
        logger.info("Cache test completed")
        
    if args.test in ["batch", "all"]:
        logger.info("=== TESTING BATCH PROCESSING PERFORMANCE ===")
        results["batch_test"] = test_batch_processing(
            batch_size=args.batch_size,
            max_workers=args.max_workers
        )
        logger.info("Batch processing test completed")
    
    # Print results summary
    logger.info("=== PERFORMANCE TEST SUMMARY ===")
    if results["cache_test"]:
        cache_test = results["cache_test"]
        logger.info(f"Cache Performance: {cache_test['improvement_percentage']:.2f}% improvement")
        logger.info(f"  First fetch: {cache_test['first_duration']:.2f} seconds")
        logger.info(f"  Second fetch: {cache_test['second_duration']:.2f} seconds")
    
    if results["batch_test"]:
        batch_test = results["batch_test"]
        logger.info(f"Batch Processing Performance: {batch_test['improvement_percentage']:.2f}% improvement")
        logger.info(f"  Sequential: {batch_test['sequential_duration']:.2f} seconds for {batch_test['tickets_count']} tickets")
        logger.info(f"  Batch ({batch_test['max_workers']} workers, size {batch_test['batch_size']}): {batch_test['batch_duration']:.2f} seconds")
        logger.info(f"  Speedup factor: {batch_test['speedup_factor']:.2f}x")
    
    logger.info("Performance tests completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
