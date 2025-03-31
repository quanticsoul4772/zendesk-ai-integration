"""
Unit tests for the BatchProcessor module.
"""

import pytest
import time
import logging
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the module to test
from src.modules.batch_processor import BatchProcessor

# Set up logging
logger = logging.getLogger(__name__)

def test_batch_processor_init():
    """Test that BatchProcessor initializes correctly with default and custom values."""
    # Test with defaults
    processor = BatchProcessor()
    assert processor.max_workers == 5
    assert processor.batch_size == 10
    assert processor.show_progress is True
    
    # Test with custom values
    processor = BatchProcessor(max_workers=3, batch_size=5, show_progress=False)
    assert processor.max_workers == 3
    assert processor.batch_size == 5
    assert processor.show_progress is False

def test_empty_batch():
    """Test that processing an empty batch returns an empty list."""
    processor = BatchProcessor()
    results = processor.process_batch([], lambda x: x)
    assert results == []

def test_simple_batch_processing():
    """Test basic batch processing with a simple function."""
    processor = BatchProcessor(show_progress=False)
    
    # Simple function that just returns the input squared
    def square(x):
        return x * x
    
    items = [1, 2, 3, 4, 5]
    results = processor.process_batch(items, square)
    
    # Verify results
    assert len(results) == 5
    assert sorted(results) == [1, 4, 9, 16, 25]

def test_batch_with_delay():
    """Test batch processing with a delayed function to verify concurrent execution."""
    # Use a smaller batch size and more workers for this test
    processor = BatchProcessor(max_workers=4, batch_size=2, show_progress=False)
    
    # Function with a delay to simulate I/O or network operations
    def delayed_process(x):
        time.sleep(0.1)  # Add a small delay
        return x * 2
    
    items = list(range(8))  # 8 items total, should be 4 batches of 2
    
    # Time sequential processing
    start_time = time.time()
    sequential_results = [delayed_process(x) for x in items]
    sequential_duration = time.time() - start_time
    
    # Time concurrent processing
    start_time = time.time()
    concurrent_results = processor.process_batch(items, delayed_process)
    concurrent_duration = time.time() - start_time
    
    # Verify results are correct
    assert sorted(concurrent_results) == sorted(sequential_results)
    
    # Verify concurrent processing is faster
    # With 4 workers and 8 items that each take 0.1s, should be at least 2x faster
    assert concurrent_duration < sequential_duration / 1.5
    
    logger.info(f"Sequential: {sequential_duration:.2f}s, Concurrent: {concurrent_duration:.2f}s, "
               f"Speedup: {sequential_duration / concurrent_duration:.2f}x")

def test_error_handling():
    """Test that errors in individual items don't break the whole batch."""
    processor = BatchProcessor(show_progress=False)
    
    # Function that raises an exception for certain values
    def risky_function(x):
        if x % 2 == 0:  # Even numbers will raise an exception
            raise ValueError(f"Error processing {x}")
        return x * 10
    
    items = [1, 2, 3, 4, 5]
    results = processor.process_batch(items, risky_function)
    
    # Only odd numbers should be in the results
    assert sorted(results) == [10, 30, 50]

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
