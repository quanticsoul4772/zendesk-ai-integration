"""
Unit Tests for Cache Manager Module

Tests the functionality of the cache_manager.py module.
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import module to test
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCache


class TestZendeskCache:
    """Test suite for ZendeskCache functionality."""
    
    def test_views_cache_hit(self):
        """Test cache hit for views."""
        cache = ZendeskCache()
        test_key = "views_test"
        test_value = ["view1", "view2"]
        
        # Set value in cache
        cache.set_views(test_key, test_value)
        
        # Get value from cache
        result = cache.get_views(test_key)
        
        # Assertions
        assert result == test_value
    
    def test_views_cache_miss(self):
        """Test cache miss for views."""
        cache = ZendeskCache()
        test_key = "nonexistent_key"
        
        # Get value that doesn't exist
        result = cache.get_views(test_key)
        
        # Assertions
        assert result is None
    
    def test_tickets_cache_operations(self):
        """Test ticket cache set, get, and invalidate operations."""
        cache = ZendeskCache()
        test_key = "tickets_test"
        test_value = [{"id": "12345", "subject": "Test"}]
        
        # Set value in cache
        cache.set_tickets(test_key, test_value)
        
        # Get value from cache
        result = cache.get_tickets(test_key)
        
        # Assertions
        assert result == test_value
        
        # Invalidate specific ticket
        cache.invalidate_ticket("12345")
        
        # Check that cache is invalidated
        assert cache.get_tickets(test_key) is None
    
    def test_user_cache_operations(self):
        """Test user cache set, get, and invalidate operations."""
        cache = ZendeskCache()
        test_key = "user_12345"
        test_value = {"id": "12345", "name": "Test User"}
        
        # Set value in cache
        cache.set_user(test_key, test_value)
        
        # Get value from cache
        result = cache.get_user(test_key)
        
        # Assertions
        assert result == test_value
        
        # Invalidate specific user
        cache.invalidate_user("12345")
        
        # Check that cache is invalidated
        assert cache.get_user(test_key) is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation methods."""
        cache = ZendeskCache()
        
        # Set values in different caches
        cache.set_views("views_test", ["view1"])
        cache.set_tickets("tickets_test", ["ticket1"])
        cache.set_user("user_test", {"name": "user1"})
        
        # Invalidate views cache
        cache.invalidate_views()
        assert cache.get_views("views_test") is None
        assert cache.get_tickets("tickets_test") is not None
        assert cache.get_user("user_test") is not None
        
        # Invalidate tickets cache
        cache.invalidate_tickets()
        assert cache.get_tickets("tickets_test") is None
        assert cache.get_user("user_test") is not None
        
        # Invalidate users cache
        cache.invalidate_users()
        assert cache.get_user("user_test") is None
    
    def test_clear_all(self):
        """Test clearing all caches."""
        cache = ZendeskCache()
        
        # Set values in different caches
        cache.set_views("views_test", ["view1"])
        cache.set_tickets("tickets_test", ["ticket1"])
        cache.set_user("user_test", {"name": "user1"})
        
        # Clear all caches
        cache.clear_all()
        
        # Verify all caches are empty
        assert cache.get_views("views_test") is None
        assert cache.get_tickets("tickets_test") is None
        assert cache.get_user("user_test") is None
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = ZendeskCache()
        
        # Set values in different caches
        cache.set_views("views_test", ["view1"])
        cache.set_tickets("tickets_test", ["ticket1"])
        cache.set_tickets("tickets_test2", ["ticket2"])
        
        # Get stats
        stats = cache.get_stats()
        
        # Assertions
        assert "views_cache" in stats
        assert "tickets_cache" in stats
        assert "user_cache" in stats
        assert stats["views_cache"]["size"] == 1
        assert stats["tickets_cache"]["size"] == 2
        assert stats["user_cache"]["size"] == 0
    
    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        cache = ZendeskCache()
        num_threads = 10
        iterations = 100
        
        # Track any exceptions that occur in threads
        exceptions = []
        
        def cache_operation_thread():
            """Thread function that performs cache operations."""
            try:
                for i in range(iterations):
                    key = f"test_key_{threading.get_ident()}_{i}"
                    cache.set_views(key, [f"value_{i}"])
                    result = cache.get_views(key)
                    assert result == [f"value_{i}"]
            except Exception as e:
                exceptions.append(e)
        
        # Create and start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=cache_operation_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Assert no exceptions occurred
        assert not exceptions, f"Exceptions occurred during threaded operations: {exceptions}"
    
    def test_empty_collection_handling(self):
        """Test handling of empty collections in cache."""
        cache = ZendeskCache()
        test_key = "empty_collection"
        
        # Set empty list in cache
        cache.set_views(test_key, [])
        
        # Get value from cache - should return None for empty collection
        result = cache.get_views(test_key)
        
        # Assertions
        assert result is None  # Empty collections should return None to force refresh
    
    @patch('cachetools.TTLCache')
    def test_ttl_expiration(self, mock_ttl_cache):
        """Test TTL expiration for views cache."""
        # Mock the TTLCache to use a very short TTL for testing
        mock_cache_instance = MagicMock()
        mock_ttl_cache.return_value = mock_cache_instance
        
        cache = ZendeskCache()
        test_key = "ttl_test"
        test_value = ["view1"]
        
        # Configure mock to simulate TTL expiration
        # First call returns the value, second call raises KeyError (expired)
        mock_cache_instance.__getitem__.side_effect = [test_value, KeyError(test_key)]
        mock_cache_instance.get.side_effect = lambda k, default=None: test_value if k == test_key else default
        
        # Set value in cache
        cache.set_views(test_key, test_value)
        
        # First get should hit
        result1 = cache.get_views(test_key)
        assert result1 == test_value
        
        # Simulate passage of time (TTL expired)
        mock_cache_instance.get.side_effect = lambda k, default=None: default
        
        # Second get should miss (TTL expired)
        result2 = cache.get_views(test_key)
        assert result2 is None
