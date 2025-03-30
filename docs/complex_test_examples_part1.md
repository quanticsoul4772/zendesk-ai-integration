# Complex Test Case Examples - Part 1: Basic Asynchronous and Caching Tests

This document contains examples for testing asynchronous operations, rate limiting, cache invalidation, and parallel processing in the Zendesk AI Integration project.

## Table of Contents

1. [Testing Asynchronous Processing](#testing-asynchronous-processing)
2. [Testing Rate Limiting and Retry Logic](#testing-rate-limiting-and-retry-logic)
3. [Testing Cache Invalidation](#testing-cache-invalidation)
4. [Testing Parallel Processing](#testing-parallel-processing)

[Return to Index](complex_test_examples_index.md)

## Testing Asynchronous Processing

Asynchronous operations can be challenging to test due to their non-deterministic nature. Here's an example of testing an async ticket processor:

```python
# tests/unit/test_async_processor.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.async_processor import AsyncTicketProcessor

class TestAsyncProcessor:
    """Tests for the asynchronous ticket processor."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock for async AI service."""
        with patch('src.async_processor.AiService') as mock:
            # Configure the async mock
            service_instance = AsyncMock()
            service_instance.analyze_content.return_value = {
                "sentiment": "positive",
                "category": "inquiry",
                "confidence": 0.85
            }
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_process_tickets_concurrently(self, mock_ai_service):
        """Test processing multiple tickets concurrently."""
        # Arrange
        processor = AsyncTicketProcessor(concurrency_limit=3)
        
        # Create test tickets
        test_tickets = [
            {"id": f"ticket-{i}", "content": f"Test content {i}"} 
            for i in range(5)
        ]
        
        # Configure the mock to add delay to simulate real async behavior
        original_analyze = mock_ai_service.analyze_content
        
        async def delayed_analyze(*args, **kwargs):
            # Add random delay between 0.1 and 0.3 seconds
            import random
            delay = random.uniform(0.1, 0.3)
            await asyncio.sleep(delay)
            return await original_analyze(*args, **kwargs)
        
        mock_ai_service.analyze_content.side_effect = delayed_analyze
        
        # Act
        start_time = asyncio.get_event_loop().time()
        results = await processor.process_tickets(test_tickets)
        end_time = asyncio.get_event_loop().time()
        
        # Assert
        # Verify all tickets were processed
        assert len(results) == 5
        
        # Verify each ticket has the expected analysis
        for result in results:
            assert "sentiment" in result
            assert result["sentiment"] == "positive"
        
        # Verify concurrency by checking the total time
        # If sequential, it would take ~1-1.5 seconds
        # With concurrency=3, should take ~0.4-0.6 seconds (2 batches)
        process_time = end_time - start_time
        assert process_time < 0.7, f"Processing took {process_time}s, should be faster with concurrency"
        
        # Verify the AI service was called for each ticket
        assert mock_ai_service.analyze_content.call_count == 5
```

## Testing Rate Limiting and Retry Logic

Rate limiting is common when working with external APIs. Here's how to test retry logic with rate limits:

```python
# tests/unit/test_rate_limit_handler.py
import pytest
from unittest.mock import patch, MagicMock
import time

from src.rate_limit_handler import RateLimitHandler
from src.exceptions import RateLimitError, ServiceUnavailableError

class TestRateLimitHandler:
    """Tests for the rate limit handler."""
    
    @pytest.fixture
    def mock_claude_service(self):
        """Create a mock for Claude service with rate limiting."""
        with patch('src.rate_limit_handler.call_claude_api') as mock:
            yield mock
    
    def test_retry_on_rate_limit(self, mock_claude_service):
        """Test successful retry after rate limit error."""
        # Arrange
        handler = RateLimitHandler(
            max_retries=3, 
            base_delay=0.1,  # Small delay for testing
            backoff_factor=2
        )
        
        # Mock the service to fail twice with rate limit, then succeed
        mock_claude_service.side_effect = [
            RateLimitError("Rate limit exceeded"),
            RateLimitError("Rate limit exceeded"),
            {"result": "success"}
        ]
        
        # Act
        start_time = time.time()
        result = handler.call_with_retry(
            prompt="Test prompt",
            max_tokens=100
        )
        end_time = time.time()
        
        # Assert
        assert result == {"result": "success"}
        
        # Verify the service was called exactly 3 times
        assert mock_claude_service.call_count == 3
        
        # Verify backoff delay was applied
        # Expected delays: 0.1s, 0.2s = 0.3s total minimum
        elapsed = end_time - start_time
        assert elapsed >= 0.3, f"Elapsed time ({elapsed}s) too short for proper backoff"
    
    def test_max_retries_exceeded(self, mock_claude_service):
        """Test exception raised when max retries exceeded."""
        # Arrange
        handler = RateLimitHandler(
            max_retries=2, 
            base_delay=0.1,
            backoff_factor=2
        )
        
        # Mock the service to always fail with rate limit
        mock_claude_service.side_effect = RateLimitError("Rate limit exceeded")
        
        # Act & Assert
        with pytest.raises(RateLimitError) as excinfo:
            handler.call_with_retry(
                prompt="Test prompt",
                max_tokens=100
            )
        
        # Verify exception message indicates max retries was exceeded
        assert "Max retries exceeded" in str(excinfo.value)
        
        # Verify the service was called exactly 3 times (initial + 2 retries)
        assert mock_claude_service.call_count == 3
    
    def test_non_rate_limit_error_not_retried(self, mock_claude_service):
        """Test that non-rate-limit errors are not retried."""
        # Arrange
        handler = RateLimitHandler(
            max_retries=3, 
            base_delay=0.1,
            backoff_factor=2
        )
        
        # Mock the service to fail with a non-rate-limit error
        mock_claude_service.side_effect = ServiceUnavailableError("Service unavailable")
        
        # Act & Assert
        with pytest.raises(ServiceUnavailableError):
            handler.call_with_retry(
                prompt="Test prompt",
                max_tokens=100
            )
        
        # Verify the service was called exactly once (no retries)
        assert mock_claude_service.call_count == 1
```

## Testing Cache Invalidation

Cache invalidation is notoriously challenging. Here's how to test that cached data is properly invalidated:

```python
# tests/unit/test_cache_invalidation.py
import pytest
from unittest.mock import patch, MagicMock
import time

from src.cache_manager import ZendeskCache
from src.zendesk_client import ZendeskClient

class TestCacheInvalidation:
    """Tests for cache invalidation logic."""
    
    @pytest.fixture
    def mock_zendesk_api(self):
        """Create a mock for Zendesk API."""
        with patch('src.zendesk_client.Zenpy') as mock:
            client_instance = MagicMock()
            
            # Configure ticket.update to return updated ticket
            def update_ticket(ticket):
                # Simulate the API updating ticket and returning it
                ticket.updated_at = time.time()
                return ticket
            
            client_instance.tickets.update.side_effect = update_ticket
            
            # Configure tickets.get to return different data each time
            # to simulate fetching fresh data
            mock_tickets = {}
            
            def get_ticket(id):
                if id not in mock_tickets:
                    ticket = MagicMock()
                    ticket.id = id
                    ticket.subject = f"Original Subject {id}"
                    ticket.updated_at = time.time()
                    mock_tickets[id] = ticket
                return mock_tickets[id]
            
            client_instance.tickets.get.side_effect = get_ticket
            
            mock.return_value = client_instance
            yield client_instance
    
    def test_cache_invalidated_after_update(self, mock_zendesk_api):
        """Test that cache is invalidated when a ticket is updated."""
        # Arrange
        cache = ZendeskCache(ttl=3600)  # 1 hour TTL
        client = ZendeskClient(cache=cache)
        
        ticket_id = 12345
        
        # Act - First get populates cache
        first_ticket = client.get_ticket(ticket_id)
        original_subject = first_ticket.subject
        
        # Verify first call went to API
        assert mock_zendesk_api.tickets.get.call_count == 1
        
        # Get again - should use cache
        cached_ticket = client.get_ticket(ticket_id)
        
        # Verify second call used cache
        assert mock_zendesk_api.tickets.get.call_count == 1
        
        # Now update the ticket
        first_ticket.subject = "Updated Subject"
        updated_ticket = client.update_ticket(first_ticket)
        
        # Get again after update - should invalidate cache and fetch fresh
        fresh_ticket = client.get_ticket(ticket_id)
        
        # Assert
        # Verify cache was invalidated by checking API call count
        assert mock_zendesk_api.tickets.get.call_count == 2
        
        # Verify we got the updated ticket
        assert fresh_ticket.subject == "Updated Subject"
        assert fresh_ticket.subject != original_subject
    
    def test_batch_invalidation(self, mock_zendesk_api):
        """Test invalidating multiple cache entries at once."""
        # Arrange
        cache = ZendeskCache(ttl=3600)  # 1 hour TTL
        client = ZendeskClient(cache=cache)
        
        # Create and cache multiple tickets
        ticket_ids = [101, 102, 103]
        tickets = {}
        
        for ticket_id in ticket_ids:
            tickets[ticket_id] = client.get_ticket(ticket_id)
        
        # Verify initial API calls
        assert mock_zendesk_api.tickets.get.call_count == 3
        
        # Get all again - should use cache
        for ticket_id in ticket_ids:
            cached_ticket = client.get_ticket(ticket_id)
        
        # Verify no additional API calls
        assert mock_zendesk_api.tickets.get.call_count == 3
        
        # Act - Invalidate multiple tickets
        client.invalidate_cache_entries(ticket_ids[:2])  # Invalidate first 2
        
        # Get all again
        for ticket_id in ticket_ids:
            fresh_ticket = client.get_ticket(ticket_id)
        
        # Assert
        # First two should have resulted in new API calls
        assert mock_zendesk_api.tickets.get.call_count == 5
```

## Testing Parallel Processing

Testing the batch processor's parallel execution capabilities:

```python
# tests/unit/test_parallel_processing.py
import pytest
import time
from unittest.mock import MagicMock

from src.batch_processor import BatchProcessor

class TestParallelProcessing:
    """Tests for parallel processing in batch processor."""
    
    def process_function(self, item):
        """Function that simulates processing an item with a delay."""
        time.sleep(0.1)  # Simulate work
        return {"id": item["id"], "result": f"Processed {item['id']}"}
    
    def test_parallel_processing_performance(self):
        """Test that parallel processing is faster than sequential."""
        # Arrange
        items = [{"id": i} for i in range(10)]
        
        # Sequential processor (max_workers=1)
        sequential_processor = BatchProcessor(max_workers=1)
        
        # Parallel processor
        parallel_processor = BatchProcessor(max_workers=5)
        
        # Act - Process with sequential
        start_sequential = time.time()
        sequential_results = sequential_processor.process_batch(
            items=items,
            process_function=self.process_function
        )
        sequential_time = time.time() - start_sequential
        
        # Act - Process with parallel
        start_parallel = time.time()
        parallel_results = parallel_processor.process_batch(
            items=items,
            process_function=self.process_function
        )
        parallel_time = time.time() - start_parallel
        
        # Assert
        # Both processors should produce same results
        assert len(sequential_results) == len(parallel_results)
        assert [r["id"] for r in sequential_results] == [r["id"] for r in parallel_results]
        
        # Parallel should be significantly faster
        # 10 items * 0.1s = ~1s sequential
        # With 5 workers, should be ~0.2-0.3s (accounting for overhead)
        assert parallel_time < sequential_time * 0.5, f"Parallel ({parallel_time}s) not significantly faster than sequential ({sequential_time}s)"
    
    def test_error_handling_during_parallel_processing(self):
        """Test that errors in worker threads are properly handled."""
        # Arrange
        items = [{"id": i} for i in range(10)]
        
        # Mock function that fails for even IDs
        def failing_process(item):
            if item["id"] % 2 == 0:
                raise ValueError(f"Error processing item {item['id']}")
            return {"id": item["id"], "result": f"Processed {item['id']}"}
        
        processor = BatchProcessor(
            max_workers=4,
            continue_on_error=True
        )
        
        # Act
        results = processor.process_batch(
            items=items,
            process_function=failing_process
        )
        
        # Assert
        # Should have results only for odd IDs
        assert len(results) == 5
        for result in results:
            assert result["id"] % 2 == 1, f"Got result for even ID {result['id']}, expected only odd IDs"
        
        # Processor should record errors
        assert len(processor.errors) == 5
        for error in processor.errors:
            assert error["error"].startswith("ValueError: Error processing item")
```
