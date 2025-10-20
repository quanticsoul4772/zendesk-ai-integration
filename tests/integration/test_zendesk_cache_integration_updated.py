"""
Integration Tests for Zendesk Client and Cache Integration

Tests the integration between Zendesk client and cache components.
Updated version that includes previously skipped tests.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
import time
from datetime import datetime, timedelta

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
    def mock_zendesk_api(self):
        """Fixture for mocked Zendesk API responses."""
        # Create mock tickets
        mock_tickets = []
        for i in range(10):
            ticket = MagicMock()
            ticket.id = 10000 + i
            ticket.subject = f"Test Subject {i}"
            ticket.description = f"Test Description {i}"
            ticket.status = "open" if i % 2 == 0 else "pending"
            ticket.created_at = datetime.now() - timedelta(days=i % 5)
            ticket.updated_at = datetime.now() - timedelta(hours=i)
            mock_tickets.append(ticket)
        
        # Create mock views
        mock_views = []
        for i in range(3):
            view = MagicMock()
            view.id = 20000 + i
            view.title = f"Test View {i}"
            view.created = datetime.now() - timedelta(days=30)
            view.updated = datetime.now() - timedelta(days=i)
            mock_views.append(view)
        
        # Create mock users
        mock_users = []
        for i in range(5):
            user = MagicMock()
            user.id = 30000 + i
            user.name = f"Test User {i}"
            user.email = f"user{i}@example.com"
            user.created_at = datetime.now() - timedelta(days=i * 10)
            mock_users.append(user)
        
        # Create a mock API client
        mock_api = MagicMock()
        
        # Configure mock methods for tickets
        def search_tickets(query, **kwargs):
            if 'status:open' in query:
                return [t for t in mock_tickets if t.status == 'open']
            elif 'status:pending' in query:
                return [t for t in mock_tickets if t.status == 'pending']
            elif 'ticket_id' in query:
                ticket_id = int(query.split(':')[1].strip())
                for ticket in mock_tickets:
                    if ticket.id == ticket_id:
                        return [ticket]
                return []
            else:
                return mock_tickets
        
        mock_api.search.side_effect = search_tickets
        
        # Configure mock methods for views
        mock_api.views.list.return_value = mock_views
        
        def get_view(id):
            for view in mock_views:
                if view.id == id:
                    return view
            return None
        
        mock_api.views.return_value = MagicMock(side_effect=get_view)
        
        # Configure mock methods for users
        def get_user(id):
            for user in mock_users:
                if user.id == id:
                    return user
            return None
        
        mock_api.users.return_value = MagicMock(side_effect=get_user)
        
        # Configure mock for tickets from view
        def get_tickets_from_view(view_id, **kwargs):
            # Return different subsets based on view_id
            if view_id == 20000:  # First view
                return mock_tickets[:3]
            elif view_id == 20001:  # Second view
                return mock_tickets[3:7]
            elif view_id == 20002:  # Third view
                return mock_tickets[7:]
            else:
                return []
        
        mock_api.views.tickets.return_value = MagicMock(side_effect=get_tickets_from_view)
        
        return mock_api
    
    @pytest.fixture
    def zendesk_client(self, mock_zendesk_api):
        """Create a ZendeskClient with a mocked API and real cache."""
        # Create a real cache
        cache = ZendeskCache()
        
        # Create a mock ZendeskClient that uses the real cache
        client = MagicMock(spec=ZendeskClient)
        client.cache = cache
        
        # Configure the client's methods to use the mock API
        def fetch_tickets(status="all", limit=100):
            if status == "open":
                tickets = mock_zendesk_api.search(query="status:open", limit=limit)
            elif status == "pending":
                tickets = mock_zendesk_api.search(query="status:pending", limit=limit)
            else:
                tickets = mock_zendesk_api.search(query="", limit=limit)
            
            # Store in cache
            cache_key = f"tickets-{status}-{limit}"
            cache.set_tickets(cache_key, tickets)
            return tickets
        
        def fetch_ticket_by_id(ticket_id):
            # Check cache first
            cache_key = f"ticket-{ticket_id}"
            cached_ticket = cache.get_tickets(cache_key)
            if cached_ticket:
                return cached_ticket
            
            # If not in cache, fetch from API
            tickets = mock_zendesk_api.search(query=f"ticket_id:{ticket_id}")
            if tickets:
                ticket = tickets[0]
                # Store in cache
                cache.set_tickets(cache_key, ticket)
                return ticket
            return None
        
        def fetch_views():
            # Check cache first
            cache_key = "all-views"
            cached_views = cache.get_views(cache_key)
            if cached_views:
                return cached_views
            
            # If not in cache, fetch from API
            views = mock_zendesk_api.views.list()
            # Store in cache
            cache.set_views(cache_key, views)
            return views
        
        def get_view_by_id(view_id):
            # Check cache first
            cache_key = f"view-{view_id}"
            cached_view = cache.get_views(cache_key)
            if cached_view:
                return cached_view
            
            # If not in cache, fetch from API
            view = mock_zendesk_api.views(id=view_id)
            if view:
                # Store in cache
                cache.set_views(cache_key, view)
            return view
        
        def fetch_tickets_from_view(view_id, limit=100):
            # Check cache first
            cache_key = f"view-tickets-{view_id}-{limit}"
            cached_tickets = cache.get_tickets(cache_key)
            if cached_tickets:
                return cached_tickets
            
            # If not in cache, fetch from API
            tickets = mock_zendesk_api.views.tickets(view_id, limit=limit)
            # Store in cache
            cache.set_tickets(cache_key, tickets)
            return tickets
        
        def get_user_by_id(user_id):
            # Check cache first
            cache_key = f"user-{user_id}"
            cached_user = cache.get_user(cache_key)
            if cached_user:
                return cached_user
            
            # If not in cache, fetch from API
            user = mock_zendesk_api.users(id=user_id)
            if user:
                # Store in cache
                cache.set_user(cache_key, user)
            return user
        
        def invalidate_ticket_cache(ticket_id):
            # Invalidate the ticket in the cache
            cache.invalidate_ticket(ticket_id)
        
        def invalidate_all_tickets():
            # Invalidate all tickets
            cache.invalidate_tickets()
        
        def invalidate_view_cache(view_id):
            # Use pattern-based invalidation for the view
            cache.invalidate_views_by_pattern(f"view-{view_id}")
        
        def invalidate_all_views():
            # Invalidate all views
            cache.invalidate_views()
        
        # Configure the client's methods
        client.fetch_tickets.side_effect = fetch_tickets
        client.fetch_ticket_by_id.side_effect = fetch_ticket_by_id
        client.fetch_views.side_effect = fetch_views
        client.get_view_by_id.side_effect = get_view_by_id
        client.fetch_tickets_from_view.side_effect = fetch_tickets_from_view
        client.get_user_by_id.side_effect = get_user_by_id
        client.invalidate_ticket_cache.side_effect = invalidate_ticket_cache
        client.invalidate_all_tickets.side_effect = invalidate_all_tickets
        client.invalidate_view_cache.side_effect = invalidate_view_cache
        client.invalidate_all_views.side_effect = invalidate_all_views
        
        return client
    
    def test_fetch_tickets_cache_integration(self, zendesk_client, mock_zendesk_api):
        """Test fetch_tickets with caching integration."""
        # First call should go to the API
        tickets_first_call = zendesk_client.get_tickets(status="open")
        
        # Second call should use the cache
        tickets_second_call = zendesk_client.get_tickets(status="open")
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache was used
        assert cache_stats["tickets_cache"]["performance"]["hits"] >= 1
        
        # Ensure same results returned
        assert len(tickets_first_call) == len(tickets_second_call)
        
        # Verify mock API was only called once
        assert mock_zendesk_api.search.call_count == 1
    
    def test_fetch_tickets_different_params(self, zendesk_client, mock_zendesk_api):
        """Test fetch_tickets with different parameters uses different cache keys."""
        # Reset mock
        mock_zendesk_api.search.reset_mock()
        
        # First call with open status
        tickets_open = zendesk_client.get_tickets(status="open")
        
        # Second call with pending status
        tickets_pending = zendesk_client.get_tickets(status="pending")
        
        # Both should hit the API since they have different parameters
        assert mock_zendesk_api.search.call_count == 2
        
        # Call each again - should use cache
        tickets_open_again = zendesk_client.get_tickets(status="open")
        tickets_pending_again = zendesk_client.get_tickets(status="pending")
        
        # API call count should remain at 2
        assert mock_zendesk_api.search.call_count == 2
        
        # Cache stats should show hits
        cache_stats = zendesk_client.cache.get_stats()
        assert cache_stats["tickets_cache"]["performance"]["hits"] >= 2
    
    def test_cache_invalidation(self, zendesk_client, mock_zendesk_api):
        """Test cache invalidation forces fresh API calls."""
        # Reset mock
        mock_zendesk_api.search.reset_mock()
        
        # First call
        tickets_first = zendesk_client.get_tickets(status="all")
        
        # Should call API
        assert mock_zendesk_api.search.call_count == 1
        
        # Second call should use cache
        tickets_second = zendesk_client.get_tickets(status="all")
        assert mock_zendesk_api.search.call_count == 1
        
        # Invalidate cache
        zendesk_client.invalidate_all_tickets()
        
        # Third call should hit API again
        tickets_third = zendesk_client.get_tickets(status="all")
        assert mock_zendesk_api.search.call_count == 2
    
    def test_fetch_views_cache_integration(self, zendesk_client, mock_zendesk_api):
        """Test fetch_views with caching integration."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # First call should go to the API
        views_first_call = zendesk_client.fetch_views()
        
        # Reset call count
        mock_zendesk_api.views.list.reset_mock()
        
        # Second call should use the cache
        views_second_call = zendesk_client.fetch_views()
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache was used
        assert cache_stats["views_cache"]["performance"]["hits"] >= 1
        
        # Verify API wasn't called again
        assert mock_zendesk_api.views.list.call_count == 0
    
    def test_fetch_views_invalidation(self, zendesk_client, mock_zendesk_api):
        """Test view cache invalidation."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # First call
        views_first = zendesk_client.fetch_views()
        
        # Reset call count
        mock_zendesk_api.views.list.reset_mock()
        
        # Second call should use cache
        views_second = zendesk_client.fetch_views()
        assert mock_zendesk_api.views.list.call_count == 0
        
        # Invalidate cache
        zendesk_client.invalidate_all_views()
        
        # Third call should hit API again
        views_third = zendesk_client.fetch_views()
        assert mock_zendesk_api.views.list.call_count == 1
    
    def test_get_view_by_id_caching(self, zendesk_client, mock_zendesk_api):
        """Test get_view_by_id with caching."""
        # Reset cache
        zendesk_client.cache.clear_all()
        
        # Get a view
        view_id = 20000
        view_first = zendesk_client.get_view_by_id(view_id)
        
        # Get the same view again
        view_second = zendesk_client.get_view_by_id(view_id)
        
        # Get cache stats
        cache_stats = zendesk_client.cache.get_stats()
        
        # Verify cache was used
        assert cache_stats["views_cache"]["performance"]["hits"] >= 1
        
        # Get a different view
        view_other = zendesk_client.get_view_by_id(20001)
        
        # Should store under a different key
        assert zendesk_client.cache.get_views(f"view-{view_id}") is not None
        assert zendesk_client.cache.get_views(f"view-20001") is not None
    
    def test_cache_ttl_expiration(self, zendesk_client, mock_zendesk_api):
        """Test cache TTL expiration (simulate time passing)."""
        # Create a cache with very short TTLs for testing
        test_cache = ZendeskCache(views_ttl=2, tickets_ttl=1, user_ttl=3)
        
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
        
        # Store data in views cache (longer TTL)
        test_cache.set_views("test-view-ttl", "test-view-value")
        
        # Wait a bit but not enough to expire views
        time.sleep(1)
        
        # Views should still be cached
        assert test_cache.get_views("test-view-ttl") == "test-view-value"
        
        # Wait more to expire views
        time.sleep(1.5)
        
        # Views should now be expired
        assert test_cache.get_views("test-view-ttl") is None
    
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
        view_name_first = zendesk_client.get_view_name(20000)
        
        # Get cache stats
        stats_before = zendesk_client.cache.get_stats()
        
        # Second lookup should use cache
        view_name_second = zendesk_client.get_view_name(20000)
        
        # Get updated stats
        stats_after = zendesk_client.cache.get_stats()
        
        # Verify cache hits increased
        assert stats_after["views_cache"]["performance"]["hits"] > stats_before["views_cache"]["performance"]["hits"]
        
        # Values should match
        assert view_name_first == view_name_second
    
    def test_custom_ttl_functionality(self, zendesk_client):
        """Test custom TTL functionality for views cache."""
        # Create a cache with custom TTL support for testing
        test_cache = ZendeskCache(views_ttl=10, tickets_ttl=10, user_ttl=10)
        
        # Store some test data
        test_cache.set_tickets("normal-ttl", "normal-value")
        
        # Get with a custom (shorter) TTL
        assert test_cache.get_tickets("normal-ttl", custom_ttl=5) == "normal-value"
        
        # Add a pattern with custom TTL
        test_cache.add_tickets_invalidation_pattern("pattern-.*", custom_ttl=2)
        
        # Store data matching the pattern
        test_cache.set_tickets("pattern-test", "pattern-value")
        
        # Wait a bit but not enough to expire normal TTL
        time.sleep(1)
        
        # Both should still be available
        assert test_cache.get_tickets("normal-ttl") == "normal-value"
        assert test_cache.get_tickets("pattern-test") == "pattern-value"
        
        # Wait more to expire pattern TTL but not normal TTL
        time.sleep(1.5)
        
        # Pattern-matched item should be expired, normal item still available
        assert test_cache.get_tickets("pattern-test") is None
        assert test_cache.get_tickets("normal-ttl") == "normal-value"
    
    def test_pattern_based_invalidation(self, zendesk_client):
        """Test pattern-based cache invalidation."""
        # Create a cache for testing
        test_cache = ZendeskCache()
        
        # Store some test data
        test_cache.set_tickets("ticket-10001", "ticket-1-value")
        test_cache.set_tickets("ticket-10002", "ticket-2-value")
        test_cache.set_tickets("view-ticket-20001", "view-ticket-value")
        
        # Invalidate by pattern
        count = test_cache.invalidate_tickets_by_pattern("ticket-1000.*")
        
        # Should have invalidated 2 items
        assert count == 2
        
        # Verify the right items were invalidated
        assert test_cache.get_tickets("ticket-10001") is None
        assert test_cache.get_tickets("ticket-10002") is None
        assert test_cache.get_tickets("view-ticket-20001") == "view-ticket-value"
    
    def test_selective_cache_invalidation(self, zendesk_client):
        """Test selective invalidation of cache entries."""
        # Create a cache for testing
        test_cache = ZendeskCache()
        
        # Store some test data
        test_cache.set_tickets("ticket-10001", "ticket-1-value")
        test_cache.set_tickets("ticket-10002", "ticket-2-value")
        test_cache.set_tickets("ticket-10003", "ticket-3-value")
        
        # Invalidate one specific ticket
        test_cache.invalidate_ticket("10002")
        
        # Verify only that ticket was invalidated
        assert test_cache.get_tickets("ticket-10001") == "ticket-1-value"
        assert test_cache.get_tickets("ticket-10002") is None
        assert test_cache.get_tickets("ticket-10003") == "ticket-3-value"
    
    def test_cache_statistics_tracking(self, zendesk_client):
        """Test cache statistics tracking."""
        # Clear the cache and reset stats
        zendesk_client.cache.clear_all()
        zendesk_client.cache.reset_statistics()
        
        # Perform some operations
        zendesk_client.cache.set_tickets("stats-test-1", "value-1")
        zendesk_client.cache.set_tickets("stats-test-2", "value-2")
        
        # Cache misses
        assert zendesk_client.cache.get_tickets("non-existent") is None
        assert zendesk_client.cache.get_tickets("another-non-existent") is None
        
        # Cache hits
        assert zendesk_client.cache.get_tickets("stats-test-1") == "value-1"
        assert zendesk_client.cache.get_tickets("stats-test-2") == "value-2"
        assert zendesk_client.cache.get_tickets("stats-test-1") == "value-1"
        
        # Get statistics
        stats = zendesk_client.cache.get_stats()
        
        # Verify statistics
        assert stats["tickets_cache"]["performance"]["hits"] == 3
        assert stats["tickets_cache"]["performance"]["misses"] == 2
        assert stats["tickets_cache"]["performance"]["hit_rate"] == 0.6  # 3/(3+2)
