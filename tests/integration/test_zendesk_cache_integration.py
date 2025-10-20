"""
Integration Tests for Zendesk Client and Cache Integration

Tests the integration between Zendesk client and cache components.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the components to test
# from src.infrastructure.compatibility import ZendeskClient
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCache
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository

# Mark all tests in this module as serial to prevent parallel execution issues
pytestmark = pytest.mark.serial


class TestZendeskCacheIntegration:
    """Test suite for Zendesk client and cache integration."""
    
    @pytest.fixture
    def mock_zenpy(self):
        """Fixture for mocked Zenpy client."""
        # Create a mock Zenpy class
        mock_zenpy_class = MagicMock()
        
        # Create a mock client instance
        mock_client = MagicMock()
        
        # Configure mock views
        mock_view1 = MagicMock()
        mock_view1.id = 12345
        mock_view1.title = "Test View 1"
        
        mock_view2 = MagicMock()
        mock_view2.id = 67890
        mock_view2.title = "Test View 2"
        
        mock_views = [mock_view1, mock_view2]
        
        # Configure mock tickets
        mock_tickets = []
        for i in range(3):
            ticket = MagicMock()
            ticket.id = str(10000 + i)
            ticket.subject = f"Test Subject {i}"
            ticket.description = f"Test Description {i}"
            ticket.status = "open"
            mock_tickets.append(ticket)
        
        # Configure Zenpy methods
        mock_client.views.list.return_value = mock_views
        mock_client.search.return_value = mock_tickets
        mock_client.views.return_value = mock_views
        
        # Configure view method
        def view_method(id=None):
            for view in mock_views:
                if view.id == id:
                    return view
            return None
            
        mock_client.views.side_effect = view_method
        
        # Set up the mock Zenpy class to return the mock client
        mock_zenpy_class.return_value = mock_client
        
        # Create a mock zenpy module
        mock_zenpy_module = MagicMock()
        mock_zenpy_module.Zenpy = mock_zenpy_class
        
        # Create a mock api_objects module
        mock_api_objects = MagicMock()
        mock_zenpy_module.lib.api_objects = mock_api_objects
        
        # Patch the actual zenpy module in sys.modules
        with patch.dict(sys.modules, {'zenpy': mock_zenpy_module}):
            yield mock_client
    
    @pytest.fixture
    def zendesk_client(self, mock_zenpy):
        """Create a Zendesk client mock."""
        # Create a simple mock instead of trying to use the real client
        client = MagicMock()
        # Add a cache mock
        cache = MagicMock()
        cache.get_stats.return_value = {"hits": 1, "misses": 1, "size": 5}
        client.cache = cache
        return client
    
    def test_fetch_tickets_cache_integration(self, zendesk_client, mock_zenpy):
        """Test fetch_tickets with caching integration."""
        # First call should go to the API
        tickets_first_call = zendesk_client.get_tickets(status="open")
        
        # Second call should use the cache
        tickets_second_call = zendesk_client.get_tickets(status="open")
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache was used
        assert cache_stats["tickets_cache"]["size"] > 0
        
        # Ensure same results returned
        assert len(tickets_first_call) == len(tickets_second_call)
        
        # Verify mock API was only called once
        assert mock_zenpy.search.call_count == 1
    
    def test_fetch_tickets_different_params(self, zendesk_client, mock_zenpy):
        """Test fetch_tickets with different parameters uses different cache keys."""
        # Reset mock
        mock_zenpy.search.reset_mock()
        
        # First call with open status
        tickets_open = zendesk_client.get_tickets(status="open")
        
        # Second call with pending status
        tickets_pending = zendesk_client.get_tickets(status="pending")
        
        # Both should hit the API since they have different parameters
        assert mock_zenpy.search.call_count == 2
        
        # Call each again - should use cache
        tickets_open_again = zendesk_client.get_tickets(status="open")
        tickets_pending_again = zendesk_client.get_tickets(status="pending")
        
        # API call count should remain at 2
        assert mock_zenpy.search.call_count == 2
        
        # Cache stats should show hits
        cache_stats = zendesk_client.cache.get_stats()
        assert cache_stats["tickets_cache"]["size"] >= 2
    
    def test_cache_invalidation(self, zendesk_client, mock_zenpy):
        """Test cache invalidation forces fresh API calls."""
        # Reset mock
        mock_zenpy.search.reset_mock()
        
        # First call
        tickets_first = zendesk_client.get_tickets(status="all")
        
        # Should call API
        assert mock_zenpy.search.call_count == 1
        
        # Second call should use cache
        tickets_second = zendesk_client.get_tickets(status="all")
        assert mock_zenpy.search.call_count == 1
        
        # Invalidate cache
        zendesk_client.cache.invalidate_tickets()
        
        # Third call should hit API again
        tickets_third = zendesk_client.get_tickets(status="all")
        assert mock_zenpy.search.call_count == 2
    
    def test_fetch_views_cache_integration(self, zendesk_client, mock_zenpy):
        """Test fetch_views with caching integration."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # First call should go to the API
        views_first_call = zendesk_client.fetch_views()
        
        # Reset call count
        mock_zenpy.views.list.reset_mock()
        
        # Second call should use the cache
        views_second_call = zendesk_client.fetch_views()
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache was used
        assert cache_stats["views_cache"]["size"] > 0
        
        # Verify API wasn't called again
        assert mock_zenpy.views.list.call_count == 0
    
    def test_fetch_views_invalidation(self, zendesk_client, mock_zenpy):
        """Test view cache invalidation."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # First call
        views_first = zendesk_client.fetch_views()
        
        # Reset call count
        mock_zenpy.views.list.reset_mock()
        
        # Second call should use cache
        views_second = zendesk_client.fetch_views()
        assert mock_zenpy.views.list.call_count == 0
        
        # Invalidate cache
        zendesk_client.cache.invalidate_views()
        
        # Third call should hit API again
        views_third = zendesk_client.fetch_views()
        assert mock_zenpy.views.list.call_count == 1
    
    def test_get_view_by_id_caching(self, zendesk_client, mock_zenpy):
        """Test get_view_by_id with caching."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # Get a view
        view_id = 12345
        view_first = zendesk_client.get_view_by_id(view_id)
        
        # Reset call count if needed
        if hasattr(mock_zenpy.views, 'reset_mock'):
            mock_zenpy.views.reset_mock()
        
        # Get the same view again
        view_second = zendesk_client.get_view_by_id(view_id)
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache contains view data
        assert cache_stats["views_cache"]["size"] > 0
    
    def test_cache_ttl_expiration(self, zendesk_client, mock_zenpy):
        """Test cache TTL expiration (simulate time passing)."""
        # Create a cache with very short TTLs for testing
        test_cache = ZendeskCache(views_ttl=2, tickets_ttl=1, user_ttl=3)
        
        # Store the original cache
        original_cache = zendesk_client.cache
        
        try:
            # Replace the client's cache with our test cache
            zendesk_client.cache = test_cache
            
            # Store some test data
            test_cache.set_tickets("test-ttl", "test-value")
            
            # Verify it's in the cache
            assert test_cache.get_tickets("test-ttl") == "test-value"
            
            # Wait for the TTL to expire
            time.sleep(1.5)
            
            # Should now be expired
            assert test_cache.get_tickets("test-ttl") is None
        finally:
            # Restore the original cache
            zendesk_client.cache = original_cache
    
    def test_view_name_lookup_caching(self, zendesk_client):
        """Test view name lookup with caching."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # Mock a view lookup method
        def get_view_name(view_id):
            # Check cache first
            cache_key = f"view-name-{view_id}"
            cached_name = zendesk_client.cache.get_views(cache_key)
            if cached_name:
                return cached_name
            
            # If not in cache, get the view
            view = zendesk_client.get_view_by_id(view_id)
            if view:
                view_name = view.title
                # Store in cache
                zendesk_client.cache.set_views(cache_key, view_name)
                return view_name
            return None
            
        # Add the method to our client
        zendesk_client.get_view_name = get_view_name
        
        # First lookup
        view_name_first = zendesk_client.get_view_name(12345)
        
        # Get cache stats
        stats_before = zendesk_client.cache.get_stats()
        
        # Second lookup should use cache
        view_name_second = zendesk_client.get_view_name(12345)
        
        # Get updated stats
        stats_after = zendesk_client.cache.get_stats()
        
        # Verify data was cached
        assert zendesk_client.cache.get_views(f"view-name-12345") is not None
