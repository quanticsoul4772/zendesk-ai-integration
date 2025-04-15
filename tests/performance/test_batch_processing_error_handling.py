"""
Performance Tests for Batch Processor Error Handling

Tests the performance of the batch processor under various error scenarios.
Focuses on how errors affect performance and how the system handles load.
"""

import pytest
import time
import random
import statistics
from unittest.mock import MagicMock
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import module to test
from src.modules.batch_processor import BatchProcessor


class TestBatchProcessorErrorHandling:
    """Performance tests for batch processing with error handling."""
    
    @pytest.fixture
    def large_dataset(self, size=200):
        """Fixture to generate a large test dataset."""
        # Create a list of mock items
        items = [MagicMock() for _ in range(size)]
        for i, item in enumerate(items):
            item.id = i
            item.content = f"Test content {i}"
        return items
    
    def test_error_rate_performance(self, large_dataset):
        """Test how different error rates affect batch processor performance."""
        error_rates = [0, 0.1, 0.25, 0.5, 0.75, 0.9]
        times = []
        throughputs = []
        success_rates = []
        
        # Fixed configuration for comparison
        max_workers = 8
        batch_size = 20
        
        for error_rate in error_rates:
            # Define a function with controlled error rate
            def process_with_errors(item):
                # Simulate error based on error rate
                if random.random() < error_rate:
                    raise ValueError(f"Simulated error for item {item.id}")
                # Simulate processing time
                time.sleep(0.01)
                return {"id": item.id, "result": f"Processed {item.content}"}
            
            # Initialize batch processor
            processor = BatchProcessor(
                max_workers=max_workers,
                batch_size=batch_size,
                show_progress=False
            )
            
            # Run processing and measure time
            start_time = time.time()
            results = processor.process_batch(large_dataset, process_with_errors)
            end_time = time.time()
            
            # Calculate metrics
            processing_time = end_time - start_time
            times.append(processing_time)
            throughput = len(results) / processing_time
            throughputs.append(throughput)
            success_rate = len(results) / len(large_dataset)
            success_rates.append(success_rate)
            
            # Print statistics
            print(f"\nPerformance with {error_rate:.0%} error rate:")
            print(f"  Total time: {processing_time:.2f} seconds")
            print(f"  Throughput: {throughput:.2f} items/second")
            print(f"  Expected success rate: {(1-error_rate):.1%}")
            print(f"  Actual success rate: {success_rate:.1%}")
        
        # Verify expected success rates match actual ones within an acceptable margin
        for i, error_rate in enumerate(error_rates):
            expected_success = 1 - error_rate
            # Allow for a larger variance due to randomness
            # For the 75% error rate, allow an even greater variance
            tolerance = 0.15 if error_rate == 0.75 else 0.1
            assert abs(success_rates[i] - expected_success) < tolerance, \
                f"Success rate mismatch for {error_rate:.0%} error rate: expected {expected_success:.2f}, got {success_rates[i]:.2f}"
        
        # Print comparative analysis
        print("\nError Rate Impact Analysis:")
        print(f"  Error Rate | Processing Time | Throughput | Success Rate")
        print(f"  -----------|-----------------|------------|-------------")
        for i, rate in enumerate(error_rates):
            print(f"  {rate:.0%}        | {times[i]:.2f}s           | {throughputs[i]:.2f}/s      | {success_rates[i]:.1%}")
    
    def test_error_recovery_performance(self, large_dataset):
        """Test performance with error recovery logic in place."""
        
        # Define a retry-capable processing function
        def process_with_retries(item, max_retries=2):
            retries = 0
            # Items with certain IDs will cause errors initially but succeed on retry
            will_fail_once = item.id % 10 == 0
            will_fail_always = item.id % 20 == 0
            
            while retries <= max_retries:
                try:
                    # Will fail on first attempt for some IDs
                    if will_fail_once and retries == 0:
                        raise ValueError(f"Simulated recoverable error for item {item.id}")
                    
                    # Will always fail for some IDs
                    if will_fail_always:
                        raise ValueError(f"Simulated permanent error for item {item.id}")
                    
                    # Simulate processing time (longer for retried items)
                    time.sleep(0.01 * (1 + retries * 0.5))
                    return {"id": item.id, "result": f"Processed {item.content}", "retries": retries}
                
                except ValueError:
                    # Increment retry count
                    retries += 1
                    # If we've exceeded max retries, re-raise the exception
                    if retries > max_retries:
                        raise
                    # Exponential backoff for retries
                    time.sleep(0.01 * retries)
        
        # Initialize batch processor
        processor = BatchProcessor(
            max_workers=8,
            batch_size=20,
            show_progress=False
        )
        
        # Run processing and measure time
        start_time = time.time()
        results = processor.process_batch(large_dataset, process_with_retries)
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        
        # Analyze retry statistics
        retry_counts = [r.get("retries", 0) for r in results if isinstance(r, dict) and "retries" in r]
        success_with_retry = sum(1 for r in retry_counts if r > 0)
        max_observed_retries = max(retry_counts) if retry_counts else 0
        
        # Calculate expected outcomes
        expected_first_attempt_failures = len(large_dataset) // 10  # every 10th item fails once
        expected_permanent_failures = len(large_dataset) // 20  # every 20th item always fails
        expected_success_with_retry = expected_first_attempt_failures - expected_permanent_failures
        expected_total_success = len(large_dataset) - expected_permanent_failures
        
        # Print statistics
        print(f"\nPerformance with error recovery (max retries = 2):")
        print(f"  Total time: {processing_time:.2f} seconds")
        print(f"  Items per second: {len(results)/processing_time:.2f}")
        print(f"  Success rate: {len(results)/len(large_dataset):.1%}")
        print(f"  Items that succeeded after retry: {success_with_retry} of {expected_success_with_retry} expected")
        print(f"  Maximum observed retries: {max_observed_retries}")
        
        # Assertions
        assert len(results) == expected_total_success, "Unexpected number of successful results"
        assert success_with_retry == expected_success_with_retry, "Unexpected number of success-after-retry results"
    
    def test_error_profiling(self, large_dataset):
        """Test and profile different types of errors and their performance impacts."""
        error_types = [
            ("Fast Failure", lambda item: raise_fast_error(item)),
            ("Slow Failure", lambda item: raise_slow_error(item)),
            ("Random Timeout", lambda item: random_timeout_error(item)),
            ("Mixed Errors", lambda item: mixed_error_types(item))
        ]
        
        times = []
        throughputs = []
        error_counts = []
        
        # Error simulation functions
        def raise_fast_error(item):
            if item.id % 4 == 0:  # 25% of items
                raise ValueError(f"Fast error for item {item.id}")
            time.sleep(0.01)
            return {"id": item.id, "result": "Success"}
        
        def raise_slow_error(item):
            if item.id % 4 == 0:  # 25% of items
                time.sleep(0.05)  # Slow error takes 5x longer
                raise ValueError(f"Slow error for item {item.id}")
            time.sleep(0.01)
            return {"id": item.id, "result": "Success"}
        
        def random_timeout_error(item):
            if item.id % 4 == 0:  # 25% of items
                # Random timeout between 0.01-0.1 seconds
                timeout = random.uniform(0.01, 0.1)
                time.sleep(timeout)
                raise TimeoutError(f"Timeout error after {timeout:.2f}s for item {item.id}")
            time.sleep(0.01)
            return {"id": item.id, "result": "Success"}
        
        def mixed_error_types(item):
            if item.id % 10 == 0:
                time.sleep(0.05)
                raise ValueError(f"Value error for item {item.id}")
            elif item.id % 10 == 5:
                time.sleep(0.02)
                raise KeyError(f"Key error for item {item.id}")
            elif item.id % 20 == 3:
                time.sleep(0.01)
                raise TimeoutError(f"Timeout for item {item.id}")
            time.sleep(0.01)
            return {"id": item.id, "result": "Success"}
        
        # Test each error type
        for error_name, error_func in error_types:
            # Initialize processor
            processor = BatchProcessor(
                max_workers=8,
                batch_size=20,
                show_progress=False
            )
            
            # Run processing and measure time
            start_time = time.time()
            results = processor.process_batch(large_dataset, error_func)
            end_time = time.time()
            
            # Calculate metrics
            processing_time = end_time - start_time
            times.append(processing_time)
            throughput = len(results) / processing_time
            throughputs.append(throughput)
            error_count = len(large_dataset) - len(results)
            error_counts.append(error_count)
            
            # Print statistics
            print(f"\nPerformance with {error_name}:")
            print(f"  Total time: {processing_time:.2f} seconds")
            print(f"  Throughput: {throughput:.2f} items/second")
            print(f"  Errors: {error_count} ({error_count/len(large_dataset):.1%})")
        
        # Print comparative analysis
        print("\nError Type Impact Analysis:")
        print(f"  Error Type       | Processing Time | Throughput | Error Count")
        print(f"  -----------------|-----------------|------------|------------")
        for i, error_name in enumerate([et[0] for et in error_types]):
            print(f"  {error_name:<17} | {times[i]:.2f}s           | {throughputs[i]:.2f}/s      | {error_counts[i]}")
        
        # Verify slow errors take longer than fast errors
        # Index 0 is Fast Failure, Index 1 is Slow Failure
        assert times[1] > times[0], "Slow errors should take longer than fast errors"
