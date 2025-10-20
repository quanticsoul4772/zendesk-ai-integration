"""
Unit Tests for Improved Cache Invalidation

These tests verify that the improved cache invalidation mechanisms work correctly,
including TTL management, pattern-based invalidation, and statistics.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
import os
import sys
import random

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the cache manager
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCache, TTLCacheWithInvalidation, CacheStatistics

class TestCacheInvalidationImproved:
    """Test suite for improved cache invalidation functionality."""
    
    @pytest.fixture
    def cache_instance(self):
        """Fixture to provide a cache instance with short TTLs for testing."""
        return ZendeskCache(views_ttl=5, tickets_ttl=3, user_ttl=7)
    
    def test_statistics_reset(self, cache_instance):
        """Test statistics reset functionality."""
        # Perform some operations to generate statistics
        cache_instance.set_tickets("stats-test", "value")
        assert cache_instance.get_tickets("stats-test") == "value"
        assert cache_instance.get_tickets("nonexistent") is None
        
        # Get initial statistics
        initial_stats = cache_instance.get_stats()
        assert initial_stats["tickets_cache"]["performance"]["hits"] == 1
        assert initial_stats["tickets_cache"]["performance"]["misses"] == 1
        
        # Reset statistics
        cache_instance.reset_statistics()
        
        # Get statistics after reset
        reset_stats = cache_instance.get_stats()
        assert reset_stats["tickets_cache"]["performance"]["hits"] == 0
        assert reset_stats["tickets_cache"]["performance"]["misses"] == 0
    
    def test_ttl_enforcement(self, cache_instance):
        """Test TTL is properly enforced for different cache types."""
        # Set entries in all caches
        cache_instance.set_tickets("ttl-ticket", "ticket-value")
        cache_instance.set_views("ttl-view", "view-value")
        cache_instance.set_user("ttl-user", "user-value")
        
        # Wait past tickets TTL but not views or user TTL
        time.sleep(4)
        
        # Tickets should be expired, others still valid
        assert cache_instance.get_tickets("ttl-ticket") is None
        assert cache_instance.get_views("ttl-view") == "view-value"
        assert cache_instance.get_user("ttl-user") == "user-value"
        
        # Wait past views TTL but not user TTL
        time.sleep(2)
        
        # Views should now be expired, user still valid
        assert cache_instance.get_views("ttl-view") is None
        assert cache_instance.get_user("ttl-user") == "user-value"
        
        # Wait past user TTL
        time.sleep(2)
        
        # User should now be expired
        assert cache_instance.get_user("ttl-user") is None
    
    def test_custom_ttl_with_get(self, cache_instance):
        """Test custom TTL when retrieving values."""
        # Set a value with default TTL
        cache_instance.set_tickets("custom-ticket", "value")
        
        # Get with a much shorter custom TTL
        assert cache_instance.get_tickets("custom-ticket", custom_ttl=1) == "value"
        
        # Wait past custom TTL but not default TTL
        time.sleep(1.5)
        
        # With custom TTL it should be expired, with default still valid
        assert cache_instance.get_tickets("custom-ticket", custom_ttl=1) is None
        assert cache_instance.get_tickets("custom-ticket") == "value"
    
    def test_pattern_specific_ttl(self, cache_instance):
        """Test pattern-specific TTL for cached items."""
        # Add patterns with custom TTLs
        cache_instance.add_tickets_invalidation_pattern("short-.*", custom_ttl=1)
        cache_instance.add_tickets_invalidation_pattern("medium-.*", custom_ttl=2)
        
        # Set values matching different patterns
        cache_instance.set_tickets("short-1", "short-value")
        cache_instance.set_tickets("medium-1", "medium-value")
        cache_instance.set_tickets("long-1", "long-value")  # Default TTL
        
        # All should be valid initially
        assert cache_instance.get_tickets("short-1") == "short-value"
        assert cache_instance.get_tickets("medium-1") == "medium-value"
        assert cache_instance.get_tickets("long-1") == "long-value"
        
        # Wait past short TTL
        time.sleep(1.5)
        
        # Short should be expired, others valid
        assert cache_instance.get_tickets("short-1") is None
        assert cache_instance.get_tickets("medium-1") == "medium-value"
        assert cache_instance.get_tickets("long-1") == "long-value"
        
        # Wait past medium TTL
        time.sleep(1)
        
        # Medium should now be expired, long still valid
        assert cache_instance.get_tickets("medium-1") is None
        assert cache_instance.get_tickets("long-1") == "long-value"
    
    def test_custom_ttl_setting(self, cache_instance):
        """Test setting custom TTL for cache types."""
        # Get original TTL
        original_ttl = cache_instance._default_ttls["tickets"]
        
        # Set a new TTL
        assert cache_instance.set_custom_ttl("tickets", 10)
        
        # Verify TTL was updated
        assert cache_instance._default_ttls["tickets"] == 10
        
        # Test with invalid cache type
        assert not cache_instance.set_custom_ttl("invalid", 10)
    
    def test_custom_cache_size(self, cache_instance):
        """Test setting custom cache size."""
        # Get original size
        original_size = cache_instance._tickets_cache.maxsize
        
        # Set a new size
        assert cache_instance.set_custom_cache_size("tickets", 50)
        
        # Verify size was updated
        assert cache_instance._tickets_cache.maxsize == 50
        
        # Test with invalid cache type
        assert not cache_instance.set_custom_cache_size("invalid", 50)
        
        # Test with very small size to force eviction
        assert cache_instance.set_custom_cache_size("tickets", 2)
        
        # Add more items than the cache can hold
        cache_instance.set_tickets("size-1", "value-1")
        cache_instance.set_tickets("size-2", "value-2")
        cache_instance.set_tickets("size-3", "value-3")  # Should evict earliest item
        
        # First item should be evicted
        assert len([k for k in cache_instance._tickets_cache.keys()]) == 2
    
    def test_cache_statistics_accuracy(self, cache_instance):
        """Test cache statistics are accurately tracked."""
        # Reset statistics
        cache_instance.reset_statistics()
        
        # Record a specific number of hits and misses
        for i in range(5):
            cache_instance.set_tickets(f"stat-key-{i}", f"value-{i}")
            
        # 5 hits
        for i in range(5):
            assert cache_instance.get_tickets(f"stat-key-{i}") == f"value-{i}"
            
        # 3 misses
        for i in range(5, 8):
            assert cache_instance.get_tickets(f"stat-key-{i}") is None
        
        # Get statistics
        stats = cache_instance.get_stats()
        
        # Verify statistics
        assert stats["tickets_cache"]["performance"]["hits"] == 5
        assert stats["tickets_cache"]["performance"]["misses"] == 3
        assert stats["tickets_cache"]["performance"]["hit_rate"] == 5/8
    
    def test_concurrent_access(self, cache_instance):
        """Test cache handles concurrent access correctly."""
        # Reset statistics
        cache_instance.reset_statistics()
        
        # Number of operations per thread
        ops_per_thread = 100
        
        # Function for thread to execute
        def worker():
            for i in range(ops_per_thread):
                key = f"concurrent-{random.randint(1, 10)}"
                
                # 80% reads, 20% writes
                if random.random() < 0.8:
                    # Read operation
                    value = cache_instance.get_tickets(key)
                    if value is None:
                        # On miss, also write
                        cache_instance.set_tickets(key, f"value-{i}")
                else:
                    # Write operation
                    cache_instance.set_tickets(key, f"value-{i}")
        
        # Create and start threads
        threads = []
        num_threads = 5
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Get statistics
        stats = cache_instance.get_stats()
        
        # Verify statistics reflect all operations
        total_operations = stats["tickets_cache"]["performance"]["hits"] + stats["tickets_cache"]["performance"]["misses"]
        assert total_operations > 0  # Should have recorded some operations
    
    def test_lru_mru_functions(self, cache_instance):
        """Test LRU and MRU functions work correctly."""
        # Fill cache with test data
        for i in range(10):
            cache_instance.set_tickets(f"lru-key-{i}", f"value-{i}")
        
        # Access items in a specific order to establish LRU/MRU
        for i in [3, 5, 7, 2, 9]:
            cache_instance.get_tickets(f"lru-key-{i}")
        
        # Get LRU items (least recently used)
        lru_items = cache_instance.get_lru_items("tickets", 3)
        
        # Should not contain recently accessed items
        lru_keys = [item[0] for item in lru_items]
        for i in [3, 5, 7, 2, 9]:
            assert f"lru-key-{i}" not in lru_keys[:2]  # The first 2 should not be recently accessed
        
        # Get MRU items (most recently used)
        mru_items = cache_instance.get_mru_items("tickets", 3)
        
        # Should contain recently accessed items
        mru_keys = [item[0] for item in mru_items]
        assert f"lru-key-9" in mru_keys  # Last accessed should be in MRU
    
    def test_cache_chaining(self, cache_instance):
        """Test methods can be chained for convenience."""
        # Chain multiple operations
        result = (cache_instance
                 .set_tickets("chain-1", "value-1")
                 .set_tickets("chain-2", "value-2")
                 .get_tickets("chain-1"))
                 
        # Last operation should return the value
        assert result == "value-1"
