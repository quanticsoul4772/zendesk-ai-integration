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

# Try to import psutil, but don't fail if it's not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    pytest.skip("psutil not available, skipping performance tests", allow_module_level=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import modules to test
from src.modules.batch_processor import BatchProcessor
from src.modules.cache_manager import ZendeskCache
from src.application.services.ticket_analysis_service import TicketAnalysisService
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository
# from src.infrastructure.compatibility import DBRepository
# Import the correct class name
# from src.infrastructure.compatibility import AIAnalyzer

# Mark tests that require psutil
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
        # Skip if psutil is not available
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
            
        cache = analyzer_system["cache"]
        db_repo = analyzer_system["db_repo"]
        analyzer = analyzer_system["analyzer"]
        batch_processor = analyzer_system["batch_processor"]
        
        # Only run a minimal configuration for faster tests
        configuration = {"workers": 2, "batch_size": 5}
        
        # Configure the batch processor
        batch_processor.max_workers = configuration["workers"]
        batch_processor.batch_size = configuration["batch_size"]
        
        # Clear the cache before each run
        cache.clear_all()
        
        # Reset mock counters
        analyzer.analyze_ticket.reset_mock()
        db_repo.save_analysis.reset_mock()
        
        # Use only a small subset of tickets for faster testing
        test_tickets = mock_tickets[:10]
        
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
        processed_results = batch_processor.process_batch(test_tickets, process_ticket)
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        tickets_per_second = len(processed_results) / total_time
        
        # Verify results are returned
        assert len(processed_results) > 0, "Batch processing should return results"
        
        # Track API calls and DB writes
        api_calls = analyzer.analyze_ticket.call_count
        db_writes = db_repo.save_analysis.call_count
        
        # Run the process again - should use cache
        analyzer.analyze_ticket.reset_mock()
        db_repo.save_analysis.reset_mock()
        
        start_time_cached = time.time()
        processed_results_cached = batch_processor.process_batch(test_tickets, process_ticket)
        end_time_cached = time.time()
        
        # Calculate cache metrics
        total_time_cached = end_time_cached - start_time_cached
        api_calls_second_run = analyzer.analyze_ticket.call_count
        
        # Calculate cache hit ratio
        cache_hit_ratio = 1.0 - (api_calls_second_run / len(test_tickets))
        
        # Compare first and second runs
        assert cache_hit_ratio > 0.9, "Cache hit ratio should be at least 90%"
        assert total_time_cached < total_time, "Cached run should be faster"
