"""
System Performance Tests (Fixed)

End-to-end performance tests that correctly detect psutil and run with proper imports.
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

# Skip the entire module if psutil is not available
try:
    import psutil
except ImportError:
    pytest.skip("psutil not available, skipping performance tests", allow_module_level=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import modules to test
from src.modules.batch_processor import BatchProcessor
from src.modules.cache_manager import ZendeskCache
from src.modules.db_repository import DBRepository
from src.modules.ai_analyzer import AIAnalyzer

@pytest.mark.integration
class TestSystemPerformanceFixed:
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
            {"workers": 4, "batch_size": 10}
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
            
            # Run the batch process with a small number of tickets for testing
            test_tickets = mock_tickets[:10]
            
            # Run the batch process
            start_time = time.time()
            processed_results = batch_processor.process_batch(test_tickets, process_ticket)
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
        
        # Run the batch process again (now with cache hits)
        start_time = time.time()
        processed_results = batch_processor.process_batch(test_tickets, process_ticket)
        end_time = time.time()
        
        # Calculate cache performance metrics
        total_time_cached = end_time - start_time
        tickets_per_second_cached = len(processed_results) / total_time_cached
        api_calls_second_run = analyzer.analyze_ticket.call_count
        db_writes_second_run = db_repo.save_analysis.call_count
        
        # Calculate cache effectiveness
        cache_hit_ratio = 1.0 - (api_calls_second_run / len(test_tickets))
        
        # Compare speeds
        if total_time_cached > 0:
            speed_improvement = best_config[1]["total_time"] / total_time_cached
        else:
            speed_improvement = float('inf')
        
        # Print results of cached run
        print(f"\nRunning second pass with populated cache using best configuration: {best_config_key}")
        print(f"  Total processing time with cache: {total_time_cached:.2f} seconds")
        print(f"  Tickets processed per second with cache: {tickets_per_second_cached:.2f}")
        print(f"  API calls made: {api_calls_second_run}")
        print(f"  Database writes: {db_writes_second_run}")
        print(f"  Cache hit ratio: {cache_hit_ratio:.2%}")
        print(f"  Speed improvement with cache: {speed_improvement:.2f}x")
        
        # Assert that caching provides benefits
        assert cache_hit_ratio > 0.9, "Cache hit ratio should be at least 90%"
        assert speed_improvement > 1.5, "Caching should provide at least 50% speed improvement"
