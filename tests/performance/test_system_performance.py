"""
System Performance Tests

End-to-end performance tests that measure the performance of the entire system
under realistic workloads. These tests combine components to measure real-world performance.
"""

import pytest
import time
import random
import sys
import os
import threading
import statistics
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid

# Attempt to import psutil, but gracefully handle if it's not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not installed. Memory usage tests will be skipped.")

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import modules to test
from src.modules.batch_processor import BatchProcessor
from src.modules.cache_manager import ZendeskCache
from src.modules.db_repository import DBRepository
# Import the correct class name
from src.modules.ai_analyzer import AIAnalyzer

# Mark the entire test class to be skipped if psutil is not available
pytestmark = pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not installed")


@pytest.mark.integration
class TestSystemPerformance:
    """End-to-end performance tests for the system."""
    
    @pytest.fixture
    def mock_tickets(self, num_tickets=100):
        """Create mock tickets for testing."""
        tickets = []
        for i in range(num_tickets):
            mock_ticket = MagicMock()
            mock_ticket.id = i
            mock_ticket.subject = f"Test Ticket {i}"
            mock_ticket.description = f"This is a test ticket {i} with some content to analyze."
            mock_ticket.status = random.choice(["new", "open", "pending", "solved", "closed"])
            mock_ticket.created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            mock_ticket.updated_at = datetime.utcnow() - timedelta(days=random.randint(0, 10))
            mock_ticket.priority = random.choice([None, "low", "normal", "high", "urgent"])
            mock_ticket.requester_id = random.randint(1000, 9999)
            
            # Add some variety to test different sentiment patterns
            sentiment_patterns = [
                "I'm having a problem with my GPU. It keeps crashing during rendering.",
                "My system is completely unusable. This is extremely frustrating!",
                "Thank you for your help. The solution worked perfectly!",
                "I'd like to request more information about your pricing.",
                "This has been going on for weeks and is affecting my business significantly.",
                "I can't access my account and I need it urgently for a client presentation tomorrow."
            ]
            
            mock_ticket.description += " " + random.choice(sentiment_patterns)
            tickets.append(mock_ticket)
        
        return tickets
    
    @pytest.fixture
    def analyzer_system(self):
        """Set up a complete analysis system with mocks."""
        # Create a cache instance
        cache = ZendeskCache()
        
        # Create a mocked DB repository
        with patch.object(DBRepository, '_connect'):
            db_repo = DBRepository()
            # Mock save_analysis method
            db_repo.save_analysis = MagicMock(return_value="test_id")
        
        # Create a mocked ticket analyzer
        with patch('src.modules.ai_analyzer.openai'), \
             patch('src.modules.ai_analyzer.anthropic'):
            analyzer = AIAnalyzer()
            
            # Mock the analyze_ticket method to return simulated results
            def mock_analyze(ticket):
                # Simulate API call delay
                time.sleep(0.05)
                
                # Generate a simulated analysis result
                result = {
                    "ticket_id": str(ticket.id),
                    "timestamp": datetime.utcnow(),
                    "sentiment": {
                        "polarity": random.choice(["positive", "negative", "neutral"]),
                        "urgency_level": random.randint(1, 10),
                        "frustration_level": random.randint(1, 10),
                        "business_impact": {
                            "detected": random.random() > 0.7
                        }
                    },
                    "category": random.choice([
                        "hardware_issue", "software_issue", "billing", "account", 
                        "service_disruption", "feature_request", "general_inquiry"
                    ]),
                    "priority_score": random.randint(1, 10)
                }
                return result
            
            analyzer.analyze_ticket = MagicMock(side_effect=mock_analyze)
        
        # Create a batch processor
        batch_processor = BatchProcessor(max_workers=8, batch_size=20)
        
        return {
            "cache": cache,
            "db_repo": db_repo,
            "analyzer": analyzer,
            "batch_processor": batch_processor
        }
    
    def test_end_to_end_processing(self, mock_tickets, analyzer_system):
        """Test end-to-end performance of the ticket analysis pipeline."""
        cache = analyzer_system["cache"]
        db_repo = analyzer_system["db_repo"]
        analyzer = analyzer_system["analyzer"]
        batch_processor = analyzer_system["batch_processor"]
        
        # Measure performance for different batch configurations
        configurations = [
            {"workers": 1, "batch_size": 10},
            {"workers": 4, "batch_size": 10},
            {"workers": 8, "batch_size": 10},
            {"workers": 4, "batch_size": 5},
            {"workers": 4, "batch_size": 20}
        ]
        
        results = {}
        
        for config in configurations:
            # Configure the batch processor
            batch_processor.max_workers = config["workers"]
            batch_processor.batch_size = config["batch_size"]
            
            # Clear the cache before each run
            cache.clear_all()
            
            # Reset mock counters
            analyzer.analyze_ticket.reset_mock()
            db_repo.save_analysis.reset_mock()
            
            # Define the processing function
            def process_ticket(ticket):
                # First check cache
                cache_key = f"ticket_analysis_{ticket.id}"
                cached_result = cache.get_tickets(cache_key)
                
                if cached_result:
                    return cached_result
                
                # If not in cache, analyze and store
                result = analyzer.analyze_ticket(ticket)
                
                # Save to database
                db_repo.save_analysis(result)
                
                # Update cache
                cache.set_tickets(cache_key, result)
                
                return result
            
            # Run the batch process
            start_time = time.time()
            processed_results = batch_processor.process_batch(mock_tickets, process_ticket)
            end_time = time.time()
            
            # Calculate performance metrics
            total_time = end_time - start_time
            tickets_per_second = len(processed_results) / total_time
            
            # Track API calls and DB writes
            api_calls = analyzer.analyze_ticket.call_count
            db_writes = db_repo.save_analysis.call_count
            
            # Store results
            config_key = f"Workers: {config['workers']}, Batch: {config['batch_size']}"
            results[config_key] = {
                "total_time": total_time,
                "tickets_per_second": tickets_per_second,
                "api_calls": api_calls,
                "db_writes": db_writes
            }
            
            # Print current configuration results
            print(f"\nConfiguration: {config_key}")
            print(f"  Total processing time: {total_time:.2f} seconds")
            print(f"  Tickets processed per second: {tickets_per_second:.2f}")
            print(f"  API calls made: {api_calls}")
            print(f"  Database writes: {db_writes}")
        
        # Run a second pass with cache populated
        # Pick the best configuration from the first run
        best_config = max(results.items(), key=lambda x: x[1]["tickets_per_second"])
        best_config_key = best_config[0]
        
        config = {
            "workers": int(best_config_key.split(",")[0].split(":")[1].strip()),
            "batch_size": int(best_config_key.split(",")[1].split(":")[1].strip())
        }
        
        # Configure the batch processor with the best config
        batch_processor.max_workers = config["workers"]
        batch_processor.batch_size = config["batch_size"]
        
        # Reset mock counters
        analyzer.analyze_ticket.reset_mock()
        db_repo.save_analysis.reset_mock()
        
        print(f"\nRunning second pass with populated cache using best configuration: {best_config_key}")
        
        # Run the batch process again (now with cache hits)
        start_time = time.time()
        processed_results = batch_processor.process_batch(mock_tickets, process_ticket)
        end_time = time.time()
        
        # Calculate cache performance metrics
        total_time_cached = end_time - start_time
        tickets_per_second_cached = len(processed_results) / total_time_cached
        api_calls_second_run = analyzer.analyze_ticket.call_count
        db_writes_second_run = db_repo.save_analysis.call_count
        
        # Calculate cache effectiveness
        cache_hit_ratio = 1.0 - (api_calls_second_run / len(mock_tickets))
        speed_improvement = (best_config[1]["total_time"] / total_time_cached) if total_time_cached > 0 else float('inf')
        
        print(f"  Total processing time with cache: {total_time_cached:.2f} seconds")
        print(f"  Tickets processed per second with cache: {tickets_per_second_cached:.2f}")
        print(f"  API calls made: {api_calls_second_run}")
        print(f"  Database writes: {db_writes_second_run}")
        print(f"  Cache hit ratio: {cache_hit_ratio:.2%}")
        print(f"  Speed improvement with cache: {speed_improvement:.2f}x")
        
        # Print comparison table of all configurations
        print("\nPerformance Comparison:")
        print(f"  Configuration               | Processing Time | Tickets/sec | API Calls | DB Writes")
        print(f"  -----------------------------|-----------------|-------------|-----------|----------")
        for config_key, metrics in results.items():
            print(f"  {config_key:<30} | {metrics['total_time']:.2f}s          | {metrics['tickets_per_second']:.2f}        | {metrics['api_calls']:<9} | {metrics['db_writes']:<9}")
        
        # Add the cache results
        cached_row = f"  {best_config_key} (cached) | {total_time_cached:.2f}s          | {tickets_per_second_cached:.2f}        | {api_calls_second_run:<9} | {db_writes_second_run:<9}"
        print(cached_row)
        
        # Make assertions about performance
        assert cache_hit_ratio > 0.9, "Cache hit ratio should be at least 90%"
        assert speed_improvement > 1.5, "Caching should provide at least 50% speed improvement"
        
    def test_system_scalability(self, analyzer_system):
        """Test how the system scales with increasing ticket load."""
        cache = analyzer_system["cache"]
        db_repo = analyzer_system["db_repo"]
        analyzer = analyzer_system["analyzer"]
        batch_processor = analyzer_system["batch_processor"]
        
        # Test with different ticket volumes
        ticket_volumes = [10, 50, 100, 200, 500]
        
        # Configure batch processor with a reasonable configuration
        batch_processor.max_workers = 8
        batch_processor.batch_size = 20
        
        results = {}
        
        for volume in ticket_volumes:
            # Clear cache and reset mocks
            cache.clear_all()
            analyzer.analyze_ticket.reset_mock()
            db_repo.save_analysis.reset_mock()
            
            # Generate tickets for this volume
            tickets = []
            for i in range(volume):
                mock_ticket = MagicMock()
                mock_ticket.id = i
                mock_ticket.subject = f"Test Ticket {i}"
                mock_ticket.description = f"This is a test ticket {i} with some content to analyze."
                mock_ticket.status = random.choice(["new", "open", "pending", "solved", "closed"])
                tickets.append(mock_ticket)
            
            # Define processing function
            def process_ticket(ticket):
                # Use cache key based on ticket ID
                cache_key = f"ticket_analysis_{ticket.id}"
                cached_result = cache.get_tickets(cache_key)
                
                if cached_result:
                    return cached_result
                
                # Analyze and store
                result = analyzer.analyze_ticket(ticket)
                db_repo.save_analysis(result)
                cache.set_tickets(cache_key, result)
                
                return result
            
            # Run the batch process
            start_time = time.time()
            processed_results = batch_processor.process_batch(tickets, process_ticket)
            end_time = time.time()
            
            # Calculate metrics
            total_time = end_time - start_time
            tickets_per_second = volume / total_time
            
            # Store results
            results[volume] = {
                "total_time": total_time,
                "tickets_per_second": tickets_per_second,
                "api_calls": analyzer.analyze_ticket.call_count,
                "db_writes": db_repo.save_analysis.call_count
            }
            
            print(f"\nTicket Volume: {volume}")
            print(f"  Total processing time: {total_time:.2f} seconds")
            print(f"  Tickets processed per second: {tickets_per_second:.2f}")
            print(f"  API calls made: {analyzer.analyze_ticket.call_count}")
            print(f"  Database writes: {db_repo.save_analysis.call_count}")
        
        # Print summary table
        print("\nScalability Results:")
        print(f"  Ticket Volume | Processing Time | Tickets/sec | Scaling Efficiency")
        print(f"  --------------|-----------------|-------------|-------------------")
        
        # Calculate baseline efficiency (tickets/second)
        baseline_efficiency = results[ticket_volumes[0]]["tickets_per_second"]
        
        for volume in ticket_volumes:
            metrics = results[volume]
            # Relative efficiency compared to baseline (smaller volumes should be more efficient)
            scaling_efficiency = metrics["tickets_per_second"] / baseline_efficiency
            
            print(f"  {volume:<14} | {metrics['total_time']:.2f}s          | {metrics['tickets_per_second']:.2f}        | {scaling_efficiency:.2f}x")
        
        # Calculate the ratio between largest and smallest throughput
        min_throughput = min(results.values(), key=lambda x: x["tickets_per_second"])["tickets_per_second"]
        max_throughput = max(results.values(), key=lambda x: x["tickets_per_second"])["tickets_per_second"]
        throughput_ratio = max_throughput / min_throughput if min_throughput > 0 else float('inf')
        
        print(f"\nThroughput ratio (max/min): {throughput_ratio:.2f}x")
        print("Note: Ideal scaling would maintain consistent throughput regardless of volume.")
        print("      Ratios closer to 1.0 indicate better scaling efficiency.")
        
        # Test if throughput remains reasonably consistent (within 3x degradation)
        assert throughput_ratio < 3.0, "Throughput should not degrade more than 3x across tested volumes"
        
    def test_extended_operation_performance(self, analyzer_system):
        """Test system performance over an extended period of continuous operation."""
        cache = analyzer_system["cache"]
        db_repo = analyzer_system["db_repo"]
        analyzer = analyzer_system["analyzer"]
        batch_processor = analyzer_system["batch_processor"]
        
        # Configure batch processor
        batch_processor.max_workers = 4
        batch_processor.batch_size = 10
        
        # We'll run multiple batches to simulate continuous operation
        num_batches = 5
        tickets_per_batch = 20
        
        # Track performance metrics across batches
        batch_times = []
        throughputs = []
        memory_usage = []
        
        # Generate a set of tickets that we'll reuse
        all_tickets = []
        for i in range(tickets_per_batch):
            mock_ticket = MagicMock()
            mock_ticket.id = i
            mock_ticket.subject = f"Test Ticket {i}"
            mock_ticket.description = f"This is a test ticket {i} with standard content."
            all_tickets.append(mock_ticket)
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            has_psutil = True
        except ImportError:
            has_psutil = False
            print("psutil not available, memory tracking disabled")
        
        # Define processing function
        def process_ticket(ticket):
            # Randomize ticket ID to simulate different tickets in each batch
            ticket_id = f"{ticket.id}_batch_{random.randint(1000, 9999)}"
            
            # Use cache key based on random ticket ID
            cache_key = f"ticket_analysis_{ticket_id}"
            
            # Always simulate a cache miss for this test
            # We want to test continuous API calls and DB writes
            
            # Analyze ticket
            result = analyzer.analyze_ticket(ticket)
            result["ticket_id"] = ticket_id
            
            # Save to database
            db_repo.save_analysis(result)
            
            return result
        
        print("\nExtended Operation Test - Multiple Batches")
        print(f"Running {num_batches} consecutive batches of {tickets_per_batch} tickets each")
        
        # Process multiple batches
        for batch_num in range(num_batches):
            print(f"\nBatch {batch_num + 1}/{num_batches}:")
            
            # Clear metrics for this batch
            analyzer.analyze_ticket.reset_mock()
            db_repo.save_analysis.reset_mock()
            
            # Measure memory before batch if available
            if has_psutil:
                memory_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Process this batch
            start_time = time.time()
            processed_results = batch_processor.process_batch(all_tickets, process_ticket)
            end_time = time.time()
            
            # Calculate metrics
            batch_time = end_time - start_time
            batch_times.append(batch_time)
            
            throughput = tickets_per_batch / batch_time
            throughputs.append(throughput)
            
            # Measure memory after batch if available
            if has_psutil:
                memory_after = process.memory_info().rss / (1024 * 1024)  # MB
                memory_usage.append(memory_after - memory_before)
                
                print(f"  Memory change: {memory_after - memory_before:.2f} MB")
            
            print(f"  Processing time: {batch_time:.2f} seconds")
            print(f"  Throughput: {throughput:.2f} tickets/second")
            print(f"  API calls: {analyzer.analyze_ticket.call_count}")
            print(f"  DB writes: {db_repo.save_analysis.call_count}")
            
            # Small delay between batches
            time.sleep(0.5)
        
        # Calculate trend statistics
        avg_time = statistics.mean(batch_times)
        min_time = min(batch_times)
        max_time = max(batch_times)
        
        avg_throughput = statistics.mean(throughputs)
        min_throughput = min(throughputs)
        max_throughput = max(throughputs)
        
        # Calculate if performance is degrading
        first_half_throughput = statistics.mean(throughputs[:len(throughputs)//2])
        second_half_throughput = statistics.mean(throughputs[len(throughputs)//2:])
        throughput_trend = (second_half_throughput / first_half_throughput) - 1.0  # negative means degrading
        
        # Print summary
        print("\nExtended Operation Performance Summary:")
        print(f"  Average batch time: {avg_time:.2f}s (min: {min_time:.2f}s, max: {max_time:.2f}s)")
        print(f"  Average throughput: {avg_throughput:.2f} tickets/s (min: {min_throughput:.2f}, max: {max_throughput:.2f})")
        print(f"  Throughput trend: {throughput_trend:.2%} ({'improving' if throughput_trend >= 0 else 'degrading'})")
        
        if has_psutil and memory_usage:
            total_memory_growth = sum(memory_usage)
            print(f"  Cumulative memory growth: {total_memory_growth:.2f} MB")
        
        # Assert that performance doesn't degrade significantly
        # Allow up to 25% degradation in throughput
        assert throughput_trend > -0.25, "Performance should not degrade more than 25% during extended operation"
        
        # If we have memory metrics, check for excessive memory growth
        if has_psutil and memory_usage:
            assert total_memory_growth < 100, "Memory growth should be less than 100MB during extended operation"
