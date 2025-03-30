"""
Unit Tests for Batch Processor Module

Tests the functionality of the batch_processor.py module.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
import concurrent.futures
import time

# Import module to test
from src.modules.batch_processor import BatchProcessor


class TestBatchProcessor:
    """Test suite for Batch Processor functionality."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        processor = BatchProcessor()
        
        # Check default values
        assert processor.max_workers == 5
        assert processor.batch_size == 10
        assert processor.show_progress is True
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        processor = BatchProcessor(max_workers=3, batch_size=5, show_progress=False)
        
        # Check custom values
        assert processor.max_workers == 3
        assert processor.batch_size == 5
        assert processor.show_progress is False
    
    def test_process_batch_empty(self):
        """Test processing an empty batch."""
        processor = BatchProcessor()
        
        # Process empty list
        results = processor.process_batch([], lambda x: x)
        
        # Should return empty list
        assert results == []
    
    @patch('src.modules.batch_processor.concurrent.futures.ThreadPoolExecutor')
    def test_process_batch_single(self, mock_executor_class):
        """Test processing a single batch."""
        # Test data
        items = [1, 2, 3, 4, 5]
        
        # Configure mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Configure mock futures
        mock_futures = []
        for item in items:
            mock_future = MagicMock()
            mock_future.result.return_value = item * 2  # Double the input
            mock_futures.append(mock_future)
        
        # Configure mock executor methods
        mock_executor.submit.side_effect = mock_futures
        
        # Mock as_completed to return futures in order
        with patch('src.modules.batch_processor.concurrent.futures.as_completed',
                  return_value=mock_futures):
            
            # Create processor with progress bar disabled
            processor = BatchProcessor(show_progress=False)
            
            # Define process function
            def process_func(item):
                return item * 2
            
            # Process batch
            results = processor.process_batch(items, process_func)
            
            # Verify results
            assert results == [2, 4, 6, 8, 10]
            
            # Verify executor was created with right max_workers
            mock_executor_class.assert_called_once_with(max_workers=5)
            
            # Verify submit was called for each item
            assert mock_executor.submit.call_count == 5
            for i, item in enumerate(items):
                submit_call = mock_executor.submit.call_args_list[i]
                assert submit_call[0][0] == process_func
                assert submit_call[0][1] == item
    
    @patch('src.modules.batch_processor.concurrent.futures.ThreadPoolExecutor')
    @patch('src.modules.batch_processor.tqdm')
    def test_process_batch_with_progress(self, mock_tqdm, mock_executor_class):
        """Test batch processing with progress bar."""
        # Test data
        items = [1, 2, 3, 4, 5]
        
        # Configure mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Configure mock futures
        mock_futures = []
        for item in items:
            mock_future = MagicMock()
            mock_future.result.return_value = item * 2
            mock_futures.append(mock_future)
        
        # Configure mock executor methods
        mock_executor.submit.side_effect = mock_futures
        
        # Configure mock tqdm
        mock_progress = MagicMock()
        mock_tqdm.return_value = mock_progress
        
        # Mock as_completed to return futures in order
        with patch('src.modules.batch_processor.concurrent.futures.as_completed',
                  return_value=mock_futures):
            
            # Create processor with progress bar enabled
            processor = BatchProcessor(show_progress=True)
            
            # Process batch
            results = processor.process_batch(items, lambda x: x * 2)
            
            # Verify tqdm was used
            mock_tqdm.assert_called_once()
            assert mock_tqdm.call_args[1]['total'] == 5
            
            # Verify progress was updated - only once for a single batch
            assert mock_progress.update.call_count == 1
            
            # Verify progress was closed
            mock_progress.close.assert_called_once()
    
    def test_process_batch_multiple_batches(self):
        """Test processing multiple batches."""
        # Create a larger list of items
        items = list(range(25))  # 25 items
        
        # Create processor with small batch size
        processor = BatchProcessor(batch_size=6, show_progress=False)
        
        # Define simple process function
        def process_func(item):
            return item * 2
        
        # Use spy on _process_concurrent to track batch sizes
        original_method = processor._process_concurrent
        batch_sizes = []
        
        def spy_process_concurrent(batch_items, *args, **kwargs):
            batch_sizes.append(len(batch_items))
            return original_method(batch_items, *args, **kwargs)
        
        processor._process_concurrent = spy_process_concurrent
        
        # Process all items
        results = processor.process_batch(items, process_func)
        
        # Verify results - ensure all items are processed (order might vary due to concurrent execution)
        assert sorted(results) == sorted([i * 2 for i in items])
        
        # Verify batch sizes
        assert batch_sizes == [6, 6, 6, 6, 1]  # 4 full batches of 6 + 1 remaining
    
    def test_process_batch_with_error(self):
        """Test handling of errors during batch processing."""
        # Test data - item 3 will cause an error
        items = [1, 2, 3, 4, 5]
        
        # Create processor
        processor = BatchProcessor(show_progress=False)
        
        # Define process function with error for item 3
        def process_func(item):
            if item == 3:
                raise ValueError("Error processing item 3")
            return item * 2
        
        # Process batch
        results = processor.process_batch(items, process_func)
        
        # Verify results - should include all successful items (order might vary)
        assert sorted(results) == [2, 4, 8, 10]
        
        # Item 3 should be missing due to error
        assert 6 not in results
    
    def test_real_concurrent_execution(self):
        """Test that processing actually runs concurrently."""
        # Create a processor with 3 workers
        processor = BatchProcessor(max_workers=3, show_progress=False)
        
        # Create a list of items that will sleep
        items = list(range(6))  # 6 items
        
        # Define a process function that sleeps
        def slow_process(item):
            time.sleep(0.1)  # Sleep for 100ms
            return item * 2
        
        # Measure time to process all items
        start_time = time.time()
        results = processor.process_batch(items, slow_process)
        end_time = time.time()
        
        # Verify results - sort them since concurrent execution may return items in different order
        assert sorted(results) == sorted([i * 2 for i in items])
        
        # Calculate expected time
        # With sequential processing: 6 items * 0.1s = 0.6s
        # With 3 workers in parallel: ~0.2s (2 batches of 3 items each)
        # Add some buffer for test environment variability
        execution_time = end_time - start_time
        
        # Should be closer to parallel time than sequential time
        assert execution_time < 0.5, "Execution time suggests processing was not concurrent"
