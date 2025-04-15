"""
Improved Integration Tests for Zendesk Client and Cache Integration

This version properly mocks the Zendesk client and ensures stable test results.
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
from src.modules.cache_manager import ZendeskCache
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository

# Mark all tests in this module as serial to prevent parallel execution issues
pytestmark = pytest.mark.serial

class TestImprovedZendeskCacheIntegration:
    """Test suite for Zendesk client and cache integration with improved mocking."""
    
    @pytest.fixture
    def zendesk_cache(self):
        """Create a fresh cache for each test."""
        cache = ZendeskCache(
            views_ttl=5,   # 5 seconds TTL for faster tests
            tickets_ttl=5,  # 5 seconds TTL for faster tests
            user_ttl=5      # 5 seconds TTL for faster tests
        )
        return cache
    
    @pytest.fixture
    def mock_zendesk_api(self):
        """Create a mock Zendesk API with controlled responses."""
        mock_api = MagicMock()
        
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
            ticket.id = 10000 + i
            ticket.subject = f"Test Subject {i}"
            ticket.description = f"Test Description {i}"
            ticket.status = "open" if i % 2 == 0 else "pending"
            mock_tickets.append(ticket)
        
        # Configure mock users
        mock_users = []
        for i in range(2):
            user = MagicMock()
            user.id = 20000 + i
            user.name = f"Test User {i}"
            user.email = f"user{i}@example.com"
            mock_users.append(user)
        
        # Set up the mock API responses
        mock_api.search.return_value = mock_tickets
        mock_api.views.list.return_value = mock_views
        mock_api.users.list.return_value = mock_users
        
        # Set up functions to return specific mock objects
        def get_view(view_id):
            for view in mock_views:
                if view.id == view_id:
                    return view
            return None
            
        def get_user(user_id):
            for user in mock_users:
                if user.id == user_id:
                    return user
            return None
        
        def get_ticket(ticket_id):
            for ticket in mock_tickets:
                if ticket.id == ticket_id:
                    return ticket
            return None
            
        def search_tickets(query, **kwargs):
            if "status:open" in query:
                return [t for t in mock_tickets if t.status == "open"]
            elif "status:pending" in query:
                return [t for t in mock_tickets if t.status == "pending"]
            else:
                return mock_tickets
        
        # Configure the mock API to use these functions
        mock_api.get_view = MagicMock(side_effect=get_view)
        mock_api.get_user = MagicMock(side_effect=get_user)
        mock_api.get_ticket = MagicMock(side_effect=get_ticket)
        mock_api.search_tickets = MagicMock(side_effect=search_tickets)
        
        return mock_api
    
    @pytest.fixture
    def zendesk_client(self, zendesk_cache, mock_zendesk_api):
        """Create a mocked ZendeskClient with the real cache."""
        client = MagicMock(spec=ZendeskClient)
        client.cache = zendesk_cache
        client.api = mock_zendesk_api
        
        # Configure client methods to use the cache
        def fetch_tickets(status="all", limit=100):
            cache_key = f"tickets-{status}-{limit}"
            
            # Check if in cache
            cached_value = zendesk_cache.get_tickets(cache_key)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, get from API
            if status == "open":
                tickets = mock_zendesk_api.search_tickets("status:open", limit=limit)
            elif status == "pending":
                tickets = mock_zendesk_api.search_tickets("status:pending", limit=limit)
            else:
                tickets = mock_zendesk_api.search_tickets("", limit=limit)
            
            # Store in cache
            zendesk_cache.set_tickets(cache_key, tickets)
            return tickets
        
        def fetch_views():
            cache_key = "all-views"
            
            # Check if in cache
            cached_value = zendesk_cache.get_views(cache_key)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, get from API
            views = mock_zendesk_api.views.list()
            
            # Store in cache
            zendesk_cache.set_views(cache_key, views)
            return views
        
        def get_view_by_id(view_id):
            cache_key = f"view-{view_id}"
            
            # Check if in cache
            cached_value = zendesk_cache.get_views(cache_key)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, get from API
            view = mock_zendesk_api.get_view(view_id)
            
            # Store in cache if found
            if view is not None:
                zendesk_cache.set_views(cache_key, view)
                
            return view
        
        def get_user_by_id(user_id):
            cache_key = f"user-{user_id}"
            
            # Check if in cache
            cached_value = zendesk_cache.get_user(cache_key)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, get from API
            user = mock_zendesk_api.get_user(user_id)
            
            # Store in cache if found
            if user is not None:
                zendesk_cache.set_user(cache_key, user)
                
            return user
        
        # Assign the methods to the client mock
        client.fetch_tickets.side_effect = fetch_tickets
        client.fetch_views.side_effect = fetch_views
        client.get_view_by_id.side_effect = get_view_by_id
        client.get_user_by_id.side_effect = get_user_by_id
        
        # Cache control methods
        client.invalidate_tickets = zendesk_cache.invalidate_tickets
        client.invalidate_views = zendesk_cache.invalidate_views
        client.invalidate_users = zendesk_cache.invalidate_users
        
        return client
    
    def test_fetch_tickets_cache_integration(self, zendesk_client, mock_zendesk_api):
        """Test fetch_tickets with caching integration."""
        # First call should go to the API
        tickets_first_call = zendesk_client.get_tickets(status="open")
        
        # Verify API was called
        assert mock_zendesk_api.search_tickets.call_count == 1
        
        # Reset the API call counter for clean testing
        mock_zendesk_api.search_tickets.reset_mock()
        
        # Second call should use the cache
        tickets_second_call = zendesk_client.get_tickets(status="open")
        
        # Verify API was NOT called again
        assert mock_zendesk_api.search_tickets.call_count == 0
        
        # Ensure same results returned
        assert len(tickets_first_call) == len(tickets_second_call)
    
    def test_fetch_tickets_different_params(self, zendesk_client, mock_zendesk_api):
        """Test fetch_tickets with different parameters uses different cache keys."""
        # Reset the API call counter
        mock_zendesk_api.search_tickets.reset_mock()
        
        # First call with open status
        zendesk_client.get_tickets(status="open")
        
        # Verify API was called
        assert mock_zendesk_api.search_tickets.call_count == 1
        
        # Reset the API call counter
        mock_zendesk_api.search_tickets.reset_mock()
        
        # Second call with pending status (different parameter)
        zendesk_client.get_tickets(status="pending")
        
        # Verify API was called again (different parameter means cache miss)
        assert mock_zendesk_api.search_tickets.call_count == 1
        
        # Reset the API call counter
        mock_zendesk_api.search_tickets.reset_mock()
        
        # Call each status again - should use cache for both
        zendesk_client.get_tickets(status="open")
        zendesk_client.get_tickets(status="pending")
        
        # Verify API was NOT called again
        assert mock_zendesk_api.search_tickets.call_count == 0
    
    def test_cache_invalidation(self, zendesk_client, mock_zendesk_api):
        """Test cache invalidation forces fresh API calls."""
        # First call
        zendesk_client.get_tickets(status="all")
        
        # Reset the API call counter
        mock_zendesk_api.search_tickets.reset_mock()
        
        # Second call should use cache
        zendesk_client.get_tickets(status="all")
        
        # Verify API was NOT called again
        assert mock_zendesk_api.search_tickets.call_count == 0
        
        # Invalidate tickets cache
        zendesk_client.invalidate_tickets()
        
        # Third call should hit API again
        zendesk_client.get_tickets(status="all")
        
        # Verify API was called after invalidation
        assert mock_zendesk_api.search_tickets.call_count == 1
    
    def test_fetch_views_cache_integration(self, zendesk_client, mock_zendesk_api):
        """Test fetch_views with caching integration."""
        # First call should go to the API
        views_first_call = zendesk_client.fetch_views()
        
        # Verify API was called
        assert mock_zendesk_api.views.list.call_count == 1
        
        # Reset the API call counter
        mock_zendesk_api.views.list.reset_mock()
        
        # Second call should use the cache
        views_second_call = zendesk_client.fetch_views()
        
        # Verify API was NOT called again
        assert mock_zendesk_api.views.list.call_count == 0
        
        # Ensure same results returned
        assert len(views_first_call) == len(views_second_call)
    
    def test_fetch_views_invalidation(self, zendesk_client, mock_zendesk_api):
        """Test view cache invalidation."""
        # First call
        zendesk_client.fetch_views()
        
        # Reset the API call counter
        mock_zendesk_api.views.list.reset_mock()
        
        # Second call should use cache
        zendesk_client.fetch_views()
        assert mock_zendesk_api.views.list.call_count == 0
        
        # Invalidate cache
        zendesk_client.invalidate_views()
        
        # Third call should hit API again
        zendesk_client.fetch_views()
        assert mock_zendesk_api.views.list.call_count == 1
    
    def test_get_view_by_id_caching(self, zendesk_client, mock_zendesk_api):
        """Test get_view_by_id with caching."""
        # First call should go to the API
        view_id = 12345
        zendesk_client.get_view_by_id(view_id)
        
        # API should have been called
        assert mock_zendesk_api.get_view.call_count == 1
        
        # Reset the API call counter
        mock_zendesk_api.get_view.reset_mock()
        
        # Second call should use cache
        zendesk_client.get_view_by_id(view_id)
        
        # API should NOT have been called again
        assert mock_zendesk_api.get_view.call_count == 0
    
    def test_cache_ttl_expiration(self, zendesk_client, mock_zendesk_api):
        """Test cache TTL expiration (simulate time passing)."""
        # First call should go to the API
        zendesk_client.get_tickets(status="all")
        
        # Reset the API call counter
        mock_zendesk_api.search_tickets.reset_mock()
        
        # Second call should use cache
        zendesk_client.get_tickets(status="all")
        assert mock_zendesk_api.search_tickets.call_count == 0
        
        # Wait for TTL to expire (cache TTL is 5 seconds)
        time.sleep(6)
        
        # Call again - should go to API because cache TTL expired
        zendesk_client.get_tickets(status="all")
        assert mock_zendesk_api.search_tickets.call_count == 1
    
    def test_view_name_lookup_caching(self, zendesk_client, mock_zendesk_api):
        """Test view name lookup with caching."""
        # Add view name lookup method to client
        def get_view_name(view_id):
            cache_key = f"view-name-{view_id}"
            
            # Check if in cache
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
        
        zendesk_client.get_view_name = get_view_name
        
        # First lookup should call get_view_by_id, which calls API
        mock_zendesk_api.get_view.reset_mock()
        zendesk_client.get_view_name(12345)
        assert mock_zendesk_api.get_view.call_count == 1
        
        # Reset the API call counter
        mock_zendesk_api.get_view.reset_mock()
        
        # Second lookup should use cache for the name
        view_name = zendesk_client.get_view_name(12345)
        assert mock_zendesk_api.get_view.call_count == 0
        assert view_name == "Test View 1"
        
        # Check that view name was cached separately
        assert zendesk_client.cache.get_views(f"view-name-12345") == "Test View 1"

    def test_pattern_based_invalidation(self, zendesk_client, mock_zendesk_api):
        """Test pattern-based invalidation for ticket cache."""
        # Add tickets with specific patterns
        zendesk_client.cache.set_tickets("user-123-ticket-1", "test-value-1")
        zendesk_client.cache.set_tickets("user-123-ticket-2", "test-value-2")
        zendesk_client.cache.set_tickets("user-456-ticket-1", "test-value-3")
        
        # Add invalidation pattern for user-123 tickets
        zendesk_client.cache.add_tickets_invalidation_pattern("user-123-.*")
        
        # Invalidate using the pattern
        count = zendesk_client.cache.invalidate_tickets_by_pattern("user-123-.*")
        
        # Should have invalidated 2 items
        assert count == 2
        
        # Check which ones remain
        assert zendesk_client.cache.get_tickets("user-123-ticket-1") is None
        assert zendesk_client.cache.get_tickets("user-123-ticket-2") is None
        assert zendesk_client.cache.get_tickets("user-456-ticket-1") == "test-value-3"
        
    def test_custom_ttl_handling(self, zendesk_client):
        """Test custom TTL handling for specific patterns."""
        # Set up a pattern with custom TTL
        zendesk_client.cache.add_tickets_invalidation_pattern("custom-ttl-.*", custom_ttl=2)
        
        # Add entries - one matching the pattern, one not
        zendesk_client.cache.set_tickets("custom-ttl-test", "pattern-value")
        zendesk_client.cache.set_tickets("regular-test", "regular-value")
        
        # Verify both are initially available
        assert zendesk_client.cache.get_tickets("custom-ttl-test") == "pattern-value"
        assert zendesk_client.cache.get_tickets("regular-test") == "regular-value"
        
        # Wait for the custom TTL to expire but not the default TTL
        time.sleep(3)
        
        # Pattern-matched entry should be expired, regular one still available
        assert zendesk_client.cache.get_tickets("custom-ttl-test") is None
        assert zendesk_client.cache.get_tickets("regular-test") == "regular-value"
