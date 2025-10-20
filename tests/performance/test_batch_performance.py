"""
Performance Tests for Batch Processor

Tests the performance of the batch processor with different configurations.
"""

# SKIPPED: This test file tests modules that were removed during clean architecture refactoring.
# Reason: Tests BatchProcessor module that was removed during refactoring

import pytest
pytestmark = pytest.mark.skip(reason="Tests BatchProcessor module that was removed during refactoring")


import pytest
import time
import statistics
from unittest.mock import MagicMock
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import module to test
# from src.modules.batch_processor import BatchProcessor


@pytest.mark.serial
class TestBatchPerformance:
    """Performance tests for batch processing."""
    
    @pytest.fixture
    def large_dataset(self, size=100):
        """Fixture to generate a large test dataset."""
        # Create a list of mock items
        items = [MagicMock() for _ in range(size)]
        for i, item in enumerate(items):
            item.id = i
            item.content = f"Test content {i}"
        return items
    
    def process_function(self, item):
        """Function to process a single item with simulated work."""
        # Simulate some work being done
        time.sleep(0.01)  # Small delay to simulate processing
        return {"id": item.id, "result": f"Processed {item.content}"}
    
    @pytest.mark.parametrize("max_workers", [1, 2, 5, 10])
    @pytest.mark.parametrize("batch_size", [10, 20, 50])
    def test_batch_processor_performance(self, large_dataset, max_workers, batch_size):
        """Test batch processor performance with different configurations."""
        # Initialize batch processor with test configuration
        processor = BatchProcessor(
            max_workers=max_workers,
            batch_size=batch_size,
            show_progress=False  # Disable progress bar for tests
        )
        
        # Run processing and measure time
        start_time = time.time()
        results = processor.process_batch(large_dataset, self.process_function)
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        
        # Basic assertions
        assert len(results) == len(large_dataset)
        
        # Print performance statistics
        items_per_second = len(large_dataset) / processing_time
        print(f"\nPerformance with {max_workers} workers, batch size {batch_size}:")
        print(f"  Total time: {processing_time:.2f} seconds")
        print(f"  Items per second: {items_per_second:.2f}")
    
    def test_batch_sizes_comparison(self, large_dataset):
        """Compare performance with different batch sizes."""
        batch_sizes = [1, 5, 10, 25, 50, 100]
        times = []
        
        for batch_size in batch_sizes:
            # Initialize batch processor
            processor = BatchProcessor(
                max_workers=5,  # Fixed number of workers
                batch_size=batch_size,
                show_progress=False
            )
            
            # Run processing and measure time
            start_time = time.time()
            results = processor.process_batch(large_dataset, self.process_function)
            end_time = time.time()
            
            # Store processing time
            times.append(end_time - start_time)
            
            # Basic assertions
            assert len(results) == len(large_dataset)
        
        # Print comparison results
        print("\nBatch Size Comparison:")
        for i, batch_size in enumerate(batch_sizes):
            print(f"  Batch size {batch_size}: {times[i]:.2f} seconds")
    
    def test_workers_comparison(self, large_dataset):
        """Compare performance with different numbers of workers."""
        worker_counts = [1, 2, 4, 8, 16, 32]
        times = []
        
        for workers in worker_counts:
            # Initialize batch processor
            processor = BatchProcessor(
                max_workers=workers,
                batch_size=20,  # Fixed batch size
                show_progress=False
            )
            
            # Run processing and measure time
            start_time = time.time()
            results = processor.process_batch(large_dataset, self.process_function)
            end_time = time.time()
            
            # Store processing time
            times.append(end_time - start_time)
            
            # Basic assertions
            assert len(results) == len(large_dataset)
        
        # Print comparison results
        print("\nWorker Count Comparison:")
        for i, workers in enumerate(worker_counts):
            print(f"  Workers {workers}: {times[i]:.2f} seconds")
    
    def test_error_handling_performance(self, large_dataset):
        """Test performance with error handling."""
        # Define a function that sometimes raises exceptions
        def process_with_errors(item):
            if item.id % 10 == 0:  # 10% of items will fail
                raise ValueError(f"Simulated error for item {item.id}")
            time.sleep(0.01)  # Small delay to simulate processing
            return {"id": item.id, "result": f"Processed {item.content}"}
        
        # Initialize batch processor
        processor = BatchProcessor(
            max_workers=5,
            batch_size=20,
            show_progress=False
        )
        
        # Run processing and measure time
        start_time = time.time()
        results = processor.process_batch(large_dataset, process_with_errors)
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        
        # Assertions - should have 90% of results
        assert len(results) == len(large_dataset) * 0.9
        
        # Print performance statistics
        items_per_second = len(results) / processing_time
        print(f"\nPerformance with error handling:")
        print(f"  Total time: {processing_time:.2f} seconds")
        print(f"  Items per second: {items_per_second:.2f}")
        print(f"  Success rate: {len(results)/len(large_dataset):.1%}")
