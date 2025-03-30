"""
Cache Invalidation Test

This module contains tests for the cache invalidation functionality.
"""

import pytest
import time
import logging

logger = logging.getLogger(__name__)

def test_cache_invalidation(zendesk_client):
    """Test that cache invalidation works correctly."""
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
    
    # Now invalidate the views cache
    logger.info("Invalidating the views cache...")
    zendesk_client.cache.invalidate_views()
    
    # Get cache stats to confirm views cache is empty
    stats_before = zendesk_client.cache.get_stats()
    logger.info(f"Cache statistics after invalidation: {stats_before}")
    
    # Third fetch should be a cache miss again
    logger.info("Third fetch after invalidation (should be cache miss)...")
    start_time = time.time()
    views_third = zendesk_client.list_all_views()
    third_duration = time.time() - start_time
    logger.info(f"Third fetch took {third_duration:.2f} seconds")
    
    # Get cache stats to confirm views cache is populated again
    stats_after = zendesk_client.cache.get_stats()
    logger.info(f"Cache statistics after re-fetch: {stats_after}")
    
    # Verify expected behavior
    # Check that second fetch was from cache (fast)
    assert second_duration < 0.1, f"Second fetch took {second_duration:.2f} seconds - cache hit should be faster"
    
    # Check that third fetch was slow (cache miss after invalidation)
    assert third_duration > second_duration, "Third fetch should be slower than second fetch (cache miss vs hit)"
    
    # Check that views cache was empty after invalidation
    assert stats_before['views_cache']['size'] == 0, f"Views cache not empty after invalidation: {stats_before['views_cache']['size']} items"
    
    # Check that views cache was populated after third fetch
    assert stats_after['views_cache']['size'] > 0, "Views cache still empty after third fetch"
