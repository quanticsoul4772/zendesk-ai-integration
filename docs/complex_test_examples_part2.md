# Complex Test Case Examples - Part 2: System Integration and Concurrency Tests

This document contains examples for testing error propagation, database transactions, long-running processes, and race conditions in the Zendesk AI Integration project.

## Table of Contents

1. [Testing Error Propagation](#testing-error-propagation)
2. [Testing Database Transactions](#testing-database-transactions)
3. [Testing Long-Running Processes](#testing-long-running-processes)
4. [Testing Race Conditions](#testing-race-conditions)

[Return to Index](complex_test_examples_index.md)

## Testing Error Propagation

Testing how errors propagate through complex component chains:

```python
# tests/integration/test_error_propagation.py
import pytest
from unittest.mock import patch, MagicMock

from src.workflow_manager import WorkflowManager
from src.exceptions import (
    ZendeskError, 
    ClaudeServiceError,
    DatabaseError,
    WorkflowError
)

class TestErrorPropagation:
    """Tests for error propagation through components."""
    
    @pytest.fixture
    def workflow_mocks(self):
        """Set up mocks for all workflow components."""
        with patch('src.workflow_manager.ZendeskClient') as mock_zendesk, \
             patch('src.workflow_manager.ClaudeService') as mock_claude, \
             patch('src.workflow_manager.DbRepository') as mock_db, \
             patch('src.workflow_manager.ReportGenerator') as mock_report:
            
            yield {
                "zendesk": mock_zendesk.return_value,
                "claude": mock_claude.return_value,
                "db": mock_db.return_value,
                "report": mock_report.return_value
            }
    
    def test_zendesk_error_propagation(self, workflow_mocks):
        """Test Zendesk error propagates correctly through workflow."""
        # Arrange
        workflow = WorkflowManager()
        
        # Configure Zendesk to raise error
        workflow_mocks["zendesk"].fetch_tickets.side_effect = ZendeskError(
            "API rate limit exceeded"
        )
        
        # Act & Assert
        with pytest.raises(WorkflowError) as excinfo:
            workflow.process_pending_tickets(days=7)
        
        # Verify original error is captured in workflow error
        assert "API rate limit exceeded" in str(excinfo.value)
        assert "Zendesk" in str(excinfo.value)
        
        # Verify other components were not called
        workflow_mocks["claude"].analyze_ticket.assert_not_called()
        workflow_mocks["db"].save_analysis.assert_not_called()
        workflow_mocks["report"].generate_report.assert_not_called()
    
    def test_claude_error_propagation(self, workflow_mocks):
        """Test Claude error propagates correctly through workflow."""
        # Arrange
        workflow = WorkflowManager()
        
        # Configure Zendesk to return tickets
        mock_ticket = MagicMock()
        mock_ticket.id = "123"
        mock_ticket.subject = "Test Ticket"
        workflow_mocks["zendesk"].fetch_tickets.return_value = [mock_ticket]
        
        # Configure Claude to raise error
        workflow_mocks["claude"].analyze_ticket.side_effect = ClaudeServiceError(
            "Claude service unavailable"
        )
        
        # Act & Assert
        with pytest.raises(WorkflowError) as excinfo:
            workflow.process_pending_tickets(days=7)
        
        # Verify original error is captured in workflow error
        assert "Claude service unavailable" in str(excinfo.value)
        assert "AI analysis" in str(excinfo.value)
        
        # Verify only Zendesk was called, later components weren't
        workflow_mocks["zendesk"].fetch_tickets.assert_called_once()
        workflow_mocks["claude"].analyze_ticket.assert_called_once()
        workflow_mocks["db"].save_analysis.assert_not_called()
        workflow_mocks["report"].generate_report.assert_not_called()
    
    def test_partial_failure_handling(self, workflow_mocks):
        """Test handling when some tickets fail but others succeed."""
        # Arrange
        workflow = WorkflowManager(continue_on_error=True)
        
        # Configure Zendesk to return multiple tickets
        mock_tickets = []
        for i in range(3):
            ticket = MagicMock()
            ticket.id = str(i + 1)
            ticket.subject = f"Test Ticket {i + 1}"
            mock_tickets.append(ticket)
        
        workflow_mocks["zendesk"].fetch_tickets.return_value = mock_tickets
        
        # Configure Claude to fail for the second ticket only
        def mock_analyze(ticket):
            if ticket.id == "2":
                raise ClaudeServiceError(f"Error analyzing ticket {ticket.id}")
            return {"sentiment": "positive", "confidence": 0.9}
        
        workflow_mocks["claude"].analyze_ticket.side_effect = mock_analyze
        
        # Act
        results = workflow.process_pending_tickets(days=7)
        
        # Assert
        # Should have processed 2 tickets successfully
        assert len(results["successful"]) == 2
        assert results["successful"][0]["ticket_id"] == "1"
        assert results["successful"][1]["ticket_id"] == "3"
        
        # Should have recorded 1 failure
        assert len(results["failed"]) == 1
        assert results["failed"][0]["ticket_id"] == "2"
        assert "Error analyzing ticket 2" in results["failed"][0]["error"]
        
        # Verify save_analysis was called twice (for successful tickets)
        assert workflow_mocks["db"].save_analysis.call_count == 2
```

## Testing Database Transactions

Testing database transaction handling and rollback logic:

```python
# tests/unit/test_db_transactions.py
import pytest
from unittest.mock import patch, MagicMock

from src.db_repository import DbRepository
from src.exceptions import DatabaseError

class TestDatabaseTransactions:
    """Tests for database transaction handling."""
    
    @pytest.fixture
    def mock_db_client(self):
        """Create a mock for MongoDB client with transaction support."""
        with patch('src.db_repository.MongoClient') as mock_client:
            # Create mock for the client instance
            client_instance = MagicMock()
            
            # Create mock for the database
            mock_db = MagicMock()
            client_instance.__getitem__.return_value = mock_db
            
            # Create mock for collections
            mock_analyses = MagicMock()
            mock_tickets = MagicMock()
            mock_db.__getitem__.side_effect = lambda x: {
                'analyses': mock_analyses,
                'tickets': mock_tickets
            }.get(x, MagicMock())
            
            # Create mock for the session
            mock_session = MagicMock()
            client_instance.start_session.return_value.__enter__.return_value = mock_session
            
            # Store references for easy access in tests
            client_instance.mock_analyses = mock_analyses
            client_instance.mock_tickets = mock_tickets
            client_instance.mock_session = mock_session
            
            mock_client.return_value = client_instance
            yield client_instance
    
    def test_successful_transaction(self, mock_db_client):
        """Test successful transaction that commits changes."""
        # Arrange
        repo = DbRepository()
        
        # Prepare test data
        ticket_id = "123"
        analysis_data = {
            "sentiment": "positive",
            "category": "inquiry",
            "confidence": 0.9
        }
        
        # Act
        repo.save_analysis_with_history(ticket_id, analysis_data)
        
        # Assert
        # Verify session was started
        mock_db_client.start_session.assert_called_once()
        
        # Verify transaction was used
        mock_db_client.mock_session.start_transaction.assert_called_once()
        
        # Verify both collections were updated
        mock_db_client.mock_analyses.insert_one.assert_called_once()
        mock_db_client.mock_tickets.update_one.assert_called_once()
        
        # Verify transaction was committed
        mock_db_client.mock_session.commit_transaction.assert_called_once()
        mock_db_client.mock_session.end_session.assert_called_once()
    
    def test_transaction_rollback_on_error(self, mock_db_client):
        """Test transaction rollback when an error occurs."""
        # Arrange
        repo = DbRepository()
        
        # Configure first insert to succeed but second to fail
        mock_db_client.mock_analyses.insert_one.return_value = MagicMock()
        mock_db_client.mock_tickets.update_one.side_effect = Exception("Database error")
        
        # Prepare test data
        ticket_id = "123"
        analysis_data = {
            "sentiment": "positive",
            "category": "inquiry",
            "confidence": 0.9
        }
        
        # Act & Assert
        with pytest.raises(DatabaseError) as excinfo:
            repo.save_analysis_with_history(ticket_id, analysis_data)
        
        # Verify exception was caught and re-raised
        assert "Database error" in str(excinfo.value)
        
        # Verify first operation was called
        mock_db_client.mock_analyses.insert_one.assert_called_once()
        
        # Verify second operation was attempted
        mock_db_client.mock_tickets.update_one.assert_called_once()
        
        # Verify transaction was aborted
        mock_db_client.mock_session.abort_transaction.assert_called_once()
        mock_db_client.mock_session.end_session.assert_called_once()
```

## Testing Long-Running Processes

Testing timeout handling and checkpoint functionality in long-running processes:

```python
# tests/unit/test_long_running_processes.py
import pytest
import time
from unittest.mock import patch, MagicMock

from src.batch_processor import BatchProcessor, TimeoutError

class TestLongRunningProcesses:
    """Tests for handling long-running processes."""
    
    @pytest.fixture
    def mock_checkpoint_manager(self):
        """Create a mock for the checkpoint manager."""
        with patch('src.batch_processor.CheckpointManager') as mock:
            manager_instance = MagicMock()
            mock.return_value = manager_instance
            yield manager_instance
    
    def test_process_timeout(self):
        """Test that processing times out after specified duration."""
        # Arrange
        processor = BatchProcessor(timeout_seconds=1)
        
        # Create a processing function that takes too long
        def slow_process(item):
            time.sleep(2)  # Longer than timeout
            return {"id": item["id"], "result": "Processed"}
        
        items = [{"id": 1}]
        
        # Act & Assert
        with pytest.raises(TimeoutError) as excinfo:
            processor.process_batch(items, slow_process)
        
        assert "Processing timed out after 1 seconds" in str(excinfo.value)
    
    def test_checkpoint_creation(self, mock_checkpoint_manager):
        """Test that checkpoints are created during processing."""
        # Arrange
        processor = BatchProcessor(
            checkpoint_interval=2,  # Create checkpoint every 2 items
            use_checkpoints=True
        )
        
        items = [{"id": i} for i in range(5)]
        
        # Processing function with built-in counter
        processed_count = 0
        
        def counting_process(item):
            nonlocal processed_count
            processed_count += 1
            return {"id": item["id"], "result": f"Processed {item['id']}"}
        
        # Act
        results = processor.process_batch(
            items=items,
            process_function=counting_process
        )
        
        # Assert
        # Should have processed all items
        assert len(results) == 5
        
        # Should have created checkpoints at appropriate intervals
        # Expect checkpoints after item 1 (index 0) and item 3 (index 2)
        assert mock_checkpoint_manager.save_checkpoint.call_count == 2
        
        # Verify checkpoint contents
        call_args_list = mock_checkpoint_manager.save_checkpoint.call_args_list
        
        # First checkpoint after 2 items
        first_call_args = call_args_list[0][0]
        assert first_call_args[1] == 2  # Items processed
        assert len(first_call_args[0]) == 2  # Results
        
        # Second checkpoint after 4 items
        second_call_args = call_args_list[1][0]
        assert second_call_args[1] == 4  # Items processed
        assert len(second_call_args[0]) == 4  # Results
    
    def test_resume_from_checkpoint(self, mock_checkpoint_manager):
        """Test resuming processing from a checkpoint."""
        # Arrange
        # Configure checkpoint manager to return a saved checkpoint
        mock_checkpoint_manager.load_latest_checkpoint.return_value = {
            "results": [{"id": i, "result": f"Processed {i}"} for i in range(3)],
            "processed_count": 3,
            "timestamp": time.time() - 60  # 1 minute ago
        }
        
        processor = BatchProcessor(
            use_checkpoints=True,
            checkpoint_interval=2
        )
        
        # Full item list
        items = [{"id": i} for i in range(5)]
        
        # Track processed items
        processed_items = []
        
        def tracking_process(item):
            processed_items.append(item["id"])
            return {"id": item["id"], "result": f"Processed {item['id']}"}
        
        # Act
        results = processor.process_batch(
            items=items,
            process_function=tracking_process,
            resume_from_checkpoint=True
        )
        
        # Assert
        # Should have all 5 results
        assert len(results) == 5
        
        # First 3 should be from checkpoint
        assert results[0]["id"] == 0
        assert results[1]["id"] == 1
        assert results[2]["id"] == 2
        
        # Should have only processed items 3 and 4
        assert processed_items == [3, 4]
        
        # Should have created one more checkpoint after item 4
        assert mock_checkpoint_manager.save_checkpoint.call_count == 1
```

## Testing Race Conditions

Testing race condition handling in multi-threaded scenarios:

```python
# tests/unit/test_race_conditions.py
import pytest
import threading
import time
from unittest.mock import patch, MagicMock

from src.cache_manager import ThreadSafeCache

class TestRaceConditions:
    """Tests for race condition handling in concurrent operations."""
    
    def test_concurrent_cache_access(self):
        """Test that cache handles concurrent access correctly."""
        # Arrange
        cache = ThreadSafeCache()
        
        # Set up test data
        test_key = "test_key"
        original_value = "original_value"
        new_value = "new_value"
        
        # Initialize cache with original value
        cache.set(test_key, original_value)
        
        # Create a flag to track race condition occurrence
        race_detected = threading.Event()
        
        # Define thread functions that might create race conditions
        def reader_thread():
            # Simulate slow read to increase chance of race condition
            time.sleep(0.01)
            value = cache.get(test_key)
            if value != original_value and value != new_value:
                # Detected intermediate/corrupted state
                race_detected.set()
            
        def writer_thread():
            # Update the value
            cache.set(test_key, new_value)
        
        # Act - Create and start multiple reader and writer threads
        threads = []
        for _ in range(20):
            threads.append(threading.Thread(target=reader_thread))
            threads.append(threading.Thread(target=writer_thread))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        # No race condition should be detected
        assert not race_detected.is_set(), "Race condition detected: corrupt value read"
        
        # Final value should be new_value
        assert cache.get(test_key) == new_value
    
    def test_increment_counter_concurrency(self):
        """Test atomic counter increments with concurrent access."""
        # Arrange
        cache = ThreadSafeCache()
        counter_key = "counter"
        cache.set(counter_key, 0)
        
        # Number of increments per thread
        increments_per_thread = 100
        thread_count = 10
        expected_final_count = increments_per_thread * thread_count
        
        # Define thread function
        def increment_counter():
            for _ in range(increments_per_thread):
                # Get current value
                current = cache.get(counter_key)
                # Simulate some processing delay to increase race condition probability
                time.sleep(0.001)
                # Update with new value
                cache.set(counter_key, current + 1)
        
        # Act - Run multiple threads
        threads = []
        for _ in range(thread_count):
            threads.append(threading.Thread(target=increment_counter))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        final_count = cache.get(counter_key)
        # Without proper concurrency control, final count would be less than expected
        # due to lost updates
        assert final_count < expected_final_count, "Non-atomic operations detected lost updates"
    
    def test_atomic_increment_operation(self):
        """Test atomic increment operation that properly handles concurrency."""
        # Arrange
        cache = ThreadSafeCache()
        counter_key = "atomic_counter"
        cache.set(counter_key, 0)
        
        # Number of increments per thread
        increments_per_thread = 100
        thread_count = 10
        expected_final_count = increments_per_thread * thread_count
        
        # Define thread function using atomic increment
        def atomic_increment_counter():
            for _ in range(increments_per_thread):
                # Use atomic operation instead of get-and-set
                cache.atomic_increment(counter_key)
        
        # Act - Run multiple threads
        threads = []
        for _ in range(thread_count):
            threads.append(threading.Thread(target=atomic_increment_counter))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        final_count = cache.get(counter_key)
        # With atomic operations, should get exactly the expected count
        assert final_count == expected_final_count, f"Expected {expected_final_count}, got {final_count}"
```
