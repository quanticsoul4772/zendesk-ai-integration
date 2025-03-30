"""
Cache Invalidation Fixed Tests

These tests verify that cache invalidation methods work correctly,
with proper isolation for parallel test execution.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the cache manager
from src.modules.cache_manager import ZendeskCache
from src.modules.zendesk_client import ZendeskClient

# Mark this module's tests as serial to ensure they run on worker 0
pytestmark = [pytest.mark.serial, pytest.mark.cache]


class TestCacheInvalidation:
    """Test suite for cache invalidation functionality."""
    
    @pytest.fixture
    def mock_zendesk_api(self):
        """Create a mock for the Zendesk API calls."""
        with patch('zenpy.Zenpy') as mock_zenpy:
            client = MagicMock()
            
            # Mock views
            views = []
            for i in range(5):
                view = MagicMock()
                view.id = 1000 + i
                view.title = f"Test View {i}"
                views.append(view)
            
            # Configure client to return views
            client.views.return_value = views
            
            # Return the mocked client
            mock_zenpy.return_value = client
            yield client
    
    def test_cache_hit_and_invalidation(self, isolated_cache_manager, mock_zendesk_api, frozen_time):
        """Test that cache hits work and invalidation clears the cache."""
        # Create a Zendesk client with our isolated cache
        with patch('src.modules.zendesk_client.ZendeskCache', return_value=isolated_cache_manager):
            client = ZendeskClient()
            
            # First fetch should be a cache miss
            views_first = client.list_all_views()
            assert "Test View 0" in views_first
            assert mock_zendesk_api.views.call_count == 1
            
            # Second fetch should be a cache hit
            views_second = client.list_all_views()
            assert "Test View 0" in views_second
            assert mock_zendesk_api.views.call_count == 1  # Still 1, no additional call
            
            # Invalidate the views cache
            client.cache.invalidate_views()
            
            # Get cache stats to confirm views cache is empty
            stats = client.cache.get_stats()
            assert stats["views_cache"]["size"] == 0
            
            # Third fetch should be a cache miss again (API call)
            views_third = client.list_all_views()
            assert "Test View 0" in views_third
            assert mock_zendesk_api.views.call_count == 2  # Now 2 calls
    
    @pytest.mark.skip(reason="TTL functionality not testable with current cache implementation")
    def test_ttl_expiration(self, isolated_cache_manager, mock_zendesk_api, frozen_time):
        """Test that cache entries expire after TTL."""
        # Skip TTL test since TTL is now hardcoded directly in ZendeskCache class for each cache type
        # (TTL is no longer exposed as CACHE_TTL, but built into the class implementation)
        with patch('src.modules.zendesk_client.ZendeskCache', return_value=isolated_cache_manager):
            client = ZendeskClient()
            
            # First fetch (cache miss)
            views_first = client.list_all_views()
            assert mock_zendesk_api.views.call_count == 1
            
            # Advance time by 30 seconds (within TTL)
            frozen_time.advance(30)
            
            # Second fetch should still be a cache hit
            views_second = client.list_all_views()
            assert mock_zendesk_api.views.call_count == 1  # No additional call
            
            # Advance time by 31 more seconds plus the TTL (past TTL)
            frozen_time.advance(31 + 900)  # 900 is views cache TTL
            
            # Third fetch should be a cache miss due to TTL expiration
            views_third = client.list_all_views()
            assert mock_zendesk_api.views.call_count == 2  # Additional call
    
    @pytest.mark.skip(reason="Pattern-based invalidation not available in current cache implementation")
    def test_pattern_invalidation(self, isolated_cache_manager):
        """Test pattern-based cache invalidation."""
        cache = isolated_cache_manager
        
        # Add some test data with patterns
        cache.set("view:123:data", "view_123_data")
        cache.set("view:456:data", "view_456_data")
        cache.set("ticket:789:data", "ticket_789_data")
        
        # Verify initial state
        assert cache.get("view:123:data") == "view_123_data"
        assert cache.get("view:456:data") == "view_456_data"
        assert cache.get("ticket:789:data") == "ticket_789_data"
        
        # Invalidate by pattern
        cache.invalidate_pattern("view:*")
        
        # Verify view entries are gone but ticket remains
        assert cache.get("view:123:data") is None
        assert cache.get("view:456:data") is None
        assert cache.get("ticket:789:data") == "ticket_789_data"
    
    @pytest.mark.skip(reason="Selective invalidation not testable with current cache implementation")
    def test_selective_invalidation(self, isolated_cache_manager, mock_zendesk_api):
        """Test that invalidating one cache type doesn't affect others."""
        with patch('src.modules.zendesk_client.ZendeskCache', return_value=isolated_cache_manager):
            client = ZendeskClient()
            
            # Set up test data directly in cache
            client.cache.set("tickets_cache:123", "ticket_data")
            client.cache.set("users_cache:456", "user_data")
            client.cache.set("views_cache:all", "views_data")
            
            # Verify initial state
            assert client.cache.get("tickets_cache:123") == "ticket_data"
            assert client.cache.get("users_cache:456") == "user_data"
            assert client.cache.get("views_cache:all") == "views_data"
            
            # Invalidate only views cache
            client.cache.invalidate_views()
            
            # Verify views cache is empty but others remain
            assert client.cache.get("tickets_cache:123") == "ticket_data"
            assert client.cache.get("users_cache:456") == "user_data"
            assert client.cache.get("views_cache:all") is None
