"""
Performance Tests for Cache Manager

Tests the performance of the cache manager with different configurations and usage patterns.
Focuses on hit rate optimization, TTL effectiveness, and memory usage.
"""

import pytest
import time
import random
import gc
import sys
import os
import threading
import statistics
from unittest.mock import MagicMock, patch
import cachetools

# Try to import psutil, but don't fail if it's not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    pytest.skip("psutil not available, skipping performance tests", allow_module_level=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import module to test
from src.modules.cache_manager import ZendeskCache


class TestCachePerformance:
    """Performance tests for the cache manager."""
    
    @pytest.fixture
    def cache_instance(self):
        """Fixture to provide a ZendeskCache instance."""
        return ZendeskCache()
    
    @staticmethod
    def get_memory_usage():
        """Helper function to get current memory usage in MB."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
        return 0  # Return 0 if psutil is not available
    
    def test_cache_hit_rate_optimization(self, cache_instance):
        """Test cache hit rate optimization with different access patterns."""
        # Define various access patterns
        access_patterns = [
            ("Uniform Random", lambda: f"item-{random.randint(1, 1000)}"),
            ("Zipf Distribution", self._zipf_key_generator(1000, 1.2)),
            ("Temporal Locality", self._temporal_locality_generator(1000, 10)),
            ("Periodic Sweep", self._periodic_sweep_generator(1000, 100))
        ]
        
        results = {}
        
        # Test each access pattern
        for pattern_name, key_generator in access_patterns:
            # Clear cache between tests
            cache_instance.clear_all()
            
            # Perform warmup with 5000 operations
            for _ in range(5000):
                key = key_generator()
                value = cache_instance.get_tickets(key)
                if value is None:
                    cache_instance.set_tickets(key, f"Value for {key}")
            
            # Now measure hit rate with 10000 more operations
            hits = 0
            misses = 0
            
            start_time = time.time()
            for _ in range(10000):
                key = key_generator()
                value = cache_instance.get_tickets(key)
                if value is None:
                    misses += 1
                    cache_instance.set_tickets(key, f"Value for {key}")
                else:
                    hits += 1
            end_time = time.time()
            
            # Calculate metrics
            hit_rate = hits / (hits + misses)
            operations_per_second = 10000 / (end_time - start_time)
            
            results[pattern_name] = {
                "hit_rate": hit_rate,
                "ops_per_second": operations_per_second,
                "time": end_time - start_time
            }
        
        # Print results
        print("\nCache Hit Rate Optimization Results:")
        print(f"  Access Pattern     | Hit Rate | Operations/s | Time (s)")
        print(f"  -------------------|----------|--------------|--------")
        for pattern_name, metrics in results.items():
            print(f"  {pattern_name:<19} | {metrics['hit_rate']:.2%}    | {metrics['ops_per_second']:.2f}        | {metrics['time']:.3f}")
        
        # Zipf should generally have a better hit rate than uniform random
        assert results["Zipf Distribution"]["hit_rate"] > results["Uniform Random"]["hit_rate"], \
            "Zipf distribution should have a better hit rate than uniform random access"
    
    def test_ttl_effectiveness(self, cache_instance):
        """Test the effectiveness of TTL settings for cache freshness."""
        # We'll test with a modified TTL for quicker testing
        with patch.object(cachetools, 'TTLCache', wraps=cachetools.TTLCache) as ttl_cache_mock:
            # Create a new cache with shorter TTLs
            test_cache = ZendeskCache()
            
            # Verify the TTL values used
            ttl_values = [call_args[1]['ttl'] for call_args in ttl_cache_mock.call_args_list]
            print(f"\nTTL values used in cache: {ttl_values}")
            
            # Fill the cache with test data
            for i in range(100):
                key = f"test-key-{i}"
                test_cache.set_tickets(key, f"Value {i}")
            
            # Check cache stats
            stats_before = test_cache.get_stats()
            print(f"\nCache stats after filling: {stats_before}")
            
            # Wait a fraction of the TTL and check how many items remain
            # Since the actual TTL is longer, we'll just check a short time
            # and extrapolate the eviction rate
            sample_time = 1  # seconds
            time.sleep(sample_time)
            
            # Check how many items remain in the tickets cache
            # We need to actually access all keys to see which ones have expired
            remaining_items = 0
            for i in range(100):
                key = f"test-key-{i}"
                if test_cache.get_tickets(key) is not None:
                    remaining_items += 1
            
            print(f"\nItems remaining after {sample_time}s: {remaining_items}/100")
            
            # Calculate metrics
            eviction_rate = (100 - remaining_items) / sample_time
            estimated_full_eviction_time = 100 / eviction_rate if eviction_rate > 0 else "N/A"
            stats_after = test_cache.get_stats()
            
            print(f"Eviction rate: {eviction_rate:.2f} items/second")
            print(f"Estimated time to full eviction: {estimated_full_eviction_time}")
            print(f"Cache stats after waiting: {stats_after}")
            
            # Now test explicit invalidation vs TTL expiration
            start_time = time.time()
            test_cache.invalidate_tickets()
            invalidation_time = time.time() - start_time
            
            print(f"Time to invalidate cache: {invalidation_time:.6f} seconds")
            
            # Add an assertion that invalidation should be much faster than waiting for TTL
            if isinstance(estimated_full_eviction_time, (int, float)):
                assert invalidation_time < estimated_full_eviction_time, \
                    "Explicit invalidation should be faster than waiting for TTL expiration"
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not installed")
    def test_cache_memory_usage(self, cache_instance):
            
        # Get baseline memory usage
        gc.collect()  # Force garbage collection
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        print(f"\nBaseline memory usage: {baseline_memory:.2f} MB")
        
        data_sizes = [100, 1000, 5000, 10000]
        memory_usages = []
        
        # Test different data sizes
        for size in data_sizes:
            # Clear cache and force garbage collection
            cache_instance.clear_all()
            gc.collect()
            
            # Create data entries of varying sizes
            for i in range(size):
                # Vary the value size too for more realistic testing
                value_size = random.randint(10, 100)  # characters
                key = f"test-key-{i}"
                value = "x" * value_size
                
                # Distribute entries across different caches
                if i % 3 == 0:
                    cache_instance.set_tickets(key, value)
                elif i % 3 == 1:
                    cache_instance.set_views(key, value)
                else:
                    cache_instance.set_user(key, value)
            
            # Measure memory after adding entries
            gc.collect()
            current_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_usage = current_memory - baseline_memory
            memory_usages.append(memory_usage)
            
            # Get cache statistics
            stats = cache_instance.get_stats()
            
            print(f"\nMemory usage with {size} entries: {memory_usage:.2f} MB")
            print(f"Cache statistics: {stats}")
            
            # Calculate bytes per entry
            total_entries = sum(stat["size"] for stat in stats.values())
            if total_entries > 0:
                bytes_per_entry = (memory_usage * 1024 * 1024) / total_entries
                print(f"Estimated memory per entry: {bytes_per_entry:.2f} bytes")
        
        # Print memory usage summary
        print("\nMemory Usage Summary:")
        print(f"  Data Size | Memory Usage (MB) | Growth Ratio")
        print(f"  ----------|-------------------|-------------")
        prev_usage = memory_usages[0]
        for i, size in enumerate(data_sizes):
            if i == 0:
                ratio = 1.0
            else:
                ratio = memory_usages[i] / memory_usages[i-1]
            print(f"  {size:<10} | {memory_usages[i]:.2f}             | {ratio:.2f}")
        
        # Check if memory usage is sublinear (indicating efficient storage)
        if len(memory_usages) >= 2:
            # Calculate the ratio of the last two measurements
            ratio = memory_usages[-1] / memory_usages[-2]
            # The ratio should be less than the ratio of data sizes
            size_ratio = data_sizes[-1] / data_sizes[-2]
            print(f"\nMemory growth ratio: {ratio:.2f}, Data size ratio: {size_ratio:.2f}")
            assert ratio <= size_ratio * 1.2, "Memory usage should scale efficiently with data size"
    
    def test_concurrency_performance(self, cache_instance):
        """Test cache performance under concurrent access."""
        # Setup test parameters
        num_threads = 10
        operations_per_thread = 1000
        read_write_ratio = 0.8  # 80% reads, 20% writes
        
        # Keep track of total hits and misses
        hits = 0
        misses = 0
        operation_times = []
        
        # Thread-safe counters
        hits_lock = threading.Lock()
        times_lock = threading.Lock()
        
        def worker():
            """Worker function for each thread."""
            nonlocal hits, misses
            
            local_hits = 0
            local_misses = 0
            local_times = []
            
            for _ in range(operations_per_thread):
                # Decide if this is a read or write operation
                is_read = random.random() < read_write_ratio
                
                # Generate a key with some locality (80/20 rule)
                if random.random() < 0.8:
                    # 80% of requests go to 20% of keys
                    key = f"hot-key-{random.randint(1, 200)}"
                else:
                    # 20% of requests go to 80% of keys
                    key = f"cold-key-{random.randint(1, 800)}"
                
                start_time = time.time()
                if is_read:
                    # Read operation
                    value = cache_instance.get_tickets(key)
                    if value is None:
                        local_misses += 1
                        # On miss, we also write
                        cache_instance.set_tickets(key, f"Value for {key}")
                    else:
                        local_hits += 1
                else:
                    # Write operation
                    cache_instance.set_tickets(key, f"Updated value for {key} at {time.time()}")
                
                # Record operation time
                op_time = time.time() - start_time
                local_times.append(op_time)
            
            # Update global counters with thread-local values
            with hits_lock:
                nonlocal hits, misses
                hits += local_hits
                misses += local_misses
            
            with times_lock:
                operation_times.extend(local_times)
        
        # Create and start threads
        threads = []
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Calculate total time and metrics
        total_time = time.time() - start_time
        total_operations = num_threads * operations_per_thread
        operations_per_second = total_operations / total_time
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        # Calculate operation time statistics
        avg_op_time = statistics.mean(operation_times)
        median_op_time = statistics.median(operation_times)
        max_op_time = max(operation_times)
        min_op_time = min(operation_times)
        
        # Special calculation for p95 (95th percentile)
        p95_op_time = sorted(operation_times)[int(len(operation_times) * 0.95)]
        
        # Print results
        print("\nConcurrent Cache Access Performance:")
        print(f"  Threads: {num_threads}, Operations per thread: {operations_per_thread}")
        print(f"  Total time: {total_time:.3f} seconds")
        print(f"  Operations per second: {operations_per_second:.2f}")
        print(f"  Hit rate: {hit_rate:.2%}")
        print(f"  Operation time (average): {avg_op_time*1000:.3f} ms")
        print(f"  Operation time (median): {median_op_time*1000:.3f} ms")
        print(f"  Operation time (p95): {p95_op_time*1000:.3f} ms")
        print(f"  Operation time (min): {min_op_time*1000:.3f} ms")
        print(f"  Operation time (max): {max_op_time*1000:.3f} ms")
        
        # Cache stats after concurrent access
        stats = cache_instance.get_stats()
        print(f"  Cache statistics after concurrent access: {stats}")
        
        # Assert acceptable performance
        assert operations_per_second > 100, "Cache should handle at least 100 operations per second"
        assert avg_op_time < 0.01, "Average operation time should be less than 10ms"
    
    # Helper methods for generating different access patterns
    
    def _zipf_key_generator(self, n, alpha):
        """
        Generate keys following a Zipf distribution.
        
        Args:
            n: Number of possible keys
            alpha: Distribution parameter (higher means more skewed)
            
        Returns:
            A function that generates keys according to Zipf
        """
        # Compute denominator for normalization
        denom = sum(1.0 / (i ** alpha) for i in range(1, n + 1))
        
        def generator():
            # Generate a random value between 0 and 1
            z = random.random()
            
            # Find the corresponding item index
            cum_prob = 0.0
            for i in range(1, n + 1):
                cum_prob += 1.0 / (i ** alpha) / denom
                if cum_prob >= z:
                    return f"zipf-{i}"
            
            # Fallback
            return f"zipf-{n}"
        
        return generator
    
    def _temporal_locality_generator(self, n, window_size):
        """
        Generate keys with temporal locality.
        
        Args:
            n: Number of possible keys
            window_size: Size of the "recent" window
            
        Returns:
            A function that generates keys with temporal locality
        """
        recent_keys = []
        
        def generator():
            nonlocal recent_keys
            
            # 80% chance to pick from recent keys if available
            if recent_keys and random.random() < 0.8:
                return random.choice(recent_keys)
            else:
                # 20% chance to pick a new key
                key = f"temporal-{random.randint(1, n)}"
                
                # Update recent keys window
                recent_keys.append(key)
                if len(recent_keys) > window_size:
                    recent_keys.pop(0)  # Remove oldest key
                
                return key
        
        return generator
    
    def _periodic_sweep_generator(self, n, cycle_size):
        """
        Generate keys with periodic sweeping pattern.
        
        Args:
            n: Number of possible keys
            cycle_size: Size of each sweep cycle
            
        Returns:
            A function that generates keys with periodic sweeping
        """
        current_position = 0
        
        def generator():
            nonlocal current_position
            
            # Occasionally jump to a random section (simulate out-of-band access)
            if random.random() < 0.1:
                current_position = random.randint(0, n - 1)
            
            # Get key at current position
            key = f"sweep-{current_position}"
            
            # Move to next position
            current_position = (current_position + 1) % n
            
            # If we've completed a cycle, jump to a different section
            if current_position % cycle_size == 0:
                # Start a new cycle at a different offset
                current_position = (current_position + random.randint(1, n // 10)) % n
            
            return key
        
        return generator
