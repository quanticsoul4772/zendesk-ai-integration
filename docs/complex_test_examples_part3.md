# Complex Test Case Examples - Part 3: Advanced Testing Techniques

This document contains examples for testing with mocked time, complex data transformations, and random data generators in the Zendesk AI Integration project.

## Table of Contents

1. [Testing with Mocked Time](#testing-with-mocked-time)
2. [Testing Complex Data Transformations](#testing-complex-data-transformations)
3. [Testing with Random Data Generators](#testing-with-random-data-generators)
4. [Conclusion](#conclusion)

[Return to Index](complex_test_examples_index.md)

## Testing with Mocked Time

Testing time-dependent functionality without waiting for real time to pass:

```python
# tests/unit/test_mocked_time.py
import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from freezegun import freeze_time

from src.ticket_analyzer import TicketAnalyzer
from src.cache_manager import ZendeskCache

class TestWithMockedTime:
    """Tests that use mocked time to verify time-dependent behavior."""
    
    def test_cache_expiration_with_mocked_time(self):
        """Test that cached items expire after TTL without waiting real time."""
        # Arrange
        ttl_seconds = 60
        cache = ZendeskCache(ttl=ttl_seconds)
        
        test_key = "test_key"
        test_value = "test_value"
        
        # Mock the time module
        with patch('src.cache_manager.time') as mock_time:
            # Set initial time
            current_time = 1000000
            mock_time.time.return_value = current_time
            
            # Store item in cache
            cache.set(test_key, test_value)
            
            # Verify item exists in cache
            assert cache.get(test_key) == test_value
            
            # Advance time by half TTL - should still be in cache
            current_time += ttl_seconds / 2
            mock_time.time.return_value = current_time
            
            assert cache.get(test_key) == test_value
            
            # Advance time beyond TTL - should be expired
            current_time += ttl_seconds
            mock_time.time.return_value = current_time
            
            assert cache.get(test_key) is None, "Cache item should have expired"
    
    @freeze_time("2025-03-15 12:00:00")
    def test_ticket_age_calculation(self):
        """Test ticket age calculation using freeze_time."""
        # Arrange
        analyzer = TicketAnalyzer()
        
        # Create ticket with creation date in the past
        ticket = MagicMock()
        ticket.created_at = datetime(2025, 3, 10, 8, 30, 0)  # 5 days and 3.5 hours ago
        
        # Act
        age_in_days = analyzer.calculate_ticket_age_days(ticket)
        
        # Assert
        assert age_in_days == 5
    
    def test_scheduled_task_execution(self):
        """Test scheduled task execution with time advancement."""
        # Arrange
        with patch('src.scheduler.time') as mock_time:
            from src.scheduler import TaskScheduler
            
            # Configure initial time
            start_time = 1000000
            mock_time.time.return_value = start_time
            
            # Create mock task function
            task_func = MagicMock()
            
            # Create scheduler and add task to run every 60 seconds
            scheduler = TaskScheduler()
            scheduler.schedule_task(task_func, interval_seconds=60)
            
            # Start scheduler (in real code this might be on a separate thread)
            scheduler.start()
            
            # Verify task hasn't run yet
            task_func.assert_not_called()
            
            # Advance time by 30 seconds - still shouldn't run
            mock_time.time.return_value = start_time + 30
            scheduler.check_and_run_tasks()
            task_func.assert_not_called()
            
            # Advance time by 40 more seconds (70 total) - should run once
            mock_time.time.return_value = start_time + 70
            scheduler.check_and_run_tasks()
            task_func.assert_called_once()
            
            # Advance time by 50 more seconds (120 total) - should run again
            mock_time.time.return_value = start_time + 120
            scheduler.check_and_run_tasks()
            assert task_func.call_count == 2
            
            # Clean up
            scheduler.stop()
```

## Testing Complex Data Transformations

Testing complex data transformations between different formats and systems:

```python
# tests/unit/test_data_transformations.py
import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from src.data_transformer import DataTransformer
from src.report_generator import ReportGenerator

class TestComplexDataTransformations:
    """Tests for complex data transformation scenarios."""
    
    @pytest.fixture
    def sample_ticket_data(self):
        """Create sample ticket data for testing."""
        return [
            {
                "id": "1",
                "subject": "GPU issue",
                "description": "My GPU is not working",
                "created_at": "2025-01-15T08:30:00Z",
                "updated_at": "2025-01-15T09:45:00Z",
                "status": "open",
                "priority": "high",
                "tags": ["hardware", "gpu", "urgent"]
            },
            {
                "id": "2",
                "subject": "Software activation",
                "description": "Cannot activate software license",
                "created_at": "2025-01-16T10:15:00Z",
                "updated_at": "2025-01-16T14:20:00Z",
                "status": "pending",
                "priority": "normal",
                "tags": ["software", "licensing"]
            }
        ]
    
    def test_merge_ticket_and_analysis_data(self, sample_ticket_data):
        """Test merging ticket and analysis data sets."""
        # Arrange
        transformer = DataTransformer()
        analysis_data = [
            {
                "ticket_id": "1",
                "sentiment": {"polarity": "negative", "urgency_level": 4},
                "category": "hardware_issue",
                "component": "gpu",
                "confidence": 0.92
            },
            {
                "ticket_id": "2",
                "sentiment": {"polarity": "neutral", "urgency_level": 2},
                "category": "software_issue",
                "component": "licensing",
                "confidence": 0.85
            }
        ]
        
        # Act
        merged_data = transformer.merge_ticket_and_analysis(
            tickets=sample_ticket_data,
            analyses=analysis_data
        )
        
        # Assert
        assert len(merged_data) == 2
        assert merged_data[0]["id"] == "1"
        assert merged_data[0]["sentiment"]["polarity"] == "negative"
        assert merged_data[0]["category"] == "hardware_issue"
    
    def test_transform_to_dataframe(self, sample_ticket_data):
        """Test transforming merged data to a pandas DataFrame."""
        # Arrange
        transformer = DataTransformer()
        analysis_data = [
            {
                "ticket_id": "1",
                "sentiment": {"polarity": "negative", "urgency_level": 4},
                "category": "hardware_issue"
            },
            {
                "ticket_id": "2",
                "sentiment": {"polarity": "neutral", "urgency_level": 2},
                "category": "software_issue"
            }
        ]
        
        # Merge the data first
        merged_data = transformer.merge_ticket_and_analysis(
            tickets=sample_ticket_data,
            analyses=analysis_data
        )
        
        # Act
        df = transformer.to_dataframe(merged_data)
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "sentiment_polarity" in df.columns
        assert df.loc[0, "sentiment_polarity"] == "negative"
    
    def test_pivot_table_creation(self, sample_ticket_data):
        """Test creating a pivot table from analyzed data."""
        # Arrange
        transformer = DataTransformer()
        report_gen = ReportGenerator()
        
        # Prepare DataFrame with analysis data
        analysis_data = [
            {
                "ticket_id": "1",
                "sentiment": {"polarity": "negative", "urgency_level": 4},
                "category": "hardware_issue",
                "component": "gpu"
            },
            {
                "ticket_id": "2",
                "sentiment": {"polarity": "neutral", "urgency_level": 2},
                "category": "software_issue",
                "component": "licensing"
            }
        ]
        
        # Merge and transform to DataFrame
        merged_data = transformer.merge_ticket_and_analysis(
            tickets=sample_ticket_data,
            analyses=analysis_data
        )
        df = transformer.to_dataframe(merged_data)
        
        # Act
        pivot = report_gen.create_category_sentiment_pivot(df)
        
        # Assert
        assert isinstance(pivot, pd.DataFrame)
        assert pivot.index.names[0] == "sentiment_polarity"
        assert pivot.index.names[1] == "category"
        
        # Verify pivot table contains expected values
        assert pivot.loc[("negative", "hardware_issue")].iloc[0] == 1
        assert pivot.loc[("neutral", "software_issue")].iloc[0] == 1
    
    def test_flatten_json_for_analysis(self):
        """Test handling complex nested JSON structures."""
        # Arrange
        transformer = DataTransformer()
        
        # Complex nested JSON from Claude API response
        complex_json = {
            "result": {
                "sentiment_analysis": {
                    "overall": {
                        "polarity": "negative",
                        "confidence": 0.87,
                        "emotional_indicators": [
                            {"emotion": "frustration", "score": 0.75},
                            {"emotion": "anger", "score": 0.43}
                        ]
                    }
                },
                "categorization": {
                    "primary_category": "product_quality",
                    "secondary_category": "customer_support"
                }
            }
        }
        
        # Act
        flattened = transformer.flatten_json_for_analysis(complex_json)
        
        # Assert
        assert isinstance(flattened, dict)
        assert flattened["sentiment_polarity"] == "negative"
        assert flattened["primary_category"] == "product_quality"
        assert flattened["top_emotion"] == "frustration"
        assert flattened["top_emotion_score"] == 0.75
```

## Testing with Random Data Generators

Testing with a variety of randomly generated test data:

```python
# tests/unit/test_random_data.py
import pytest
import random
import string
import uuid
from datetime import datetime, timedelta
import faker
from unittest.mock import patch, MagicMock

from src.ticket_analyzer import TicketAnalyzer
from src.batch_processor import BatchProcessor

class TestWithRandomDataGenerators:
    """Tests using randomly generated data for comprehensive testing."""
    
    @pytest.fixture
    def fake(self):
        """Create a Faker instance for test data generation."""
        return faker.Faker()
    
    def generate_random_ticket(self, fake):
        """Generate a random ticket with realistic data."""
        categories = ["hardware", "software", "billing", "general", "returns"]
        statuses = ["new", "open", "pending", "solved", "closed"]
        priorities = ["low", "normal", "high", "urgent"]
        
        created_at = fake.date_time_between(start_date="-30d", end_date="now")
        
        return {
            "id": str(uuid.uuid4()),
            "subject": fake.sentence(),
            "description": fake.paragraph(nb_sentences=5),
            "created_at": created_at.isoformat(),
            "updated_at": (created_at + timedelta(hours=random.randint(1, 48))).isoformat(),
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "category": random.choice(categories),
            "tags": [fake.word() for _ in range(random.randint(0, 5))]
        }
    
    def test_ticket_analysis_with_random_data(self, fake):
        """Test ticket analysis with a variety of randomly generated tickets."""
        # Arrange
        analyzer = TicketAnalyzer()
        
        # Generate 20 random tickets
        random_tickets = [self.generate_random_ticket(fake) for _ in range(20)]
        
        # Mock the AI service to return appropriate responses
        with patch('src.ticket_analyzer.ClaudeService') as mock_claude:
            # Configure mock to return analysis based on ticket content
            def mock_analyze(content):
                # Generate plausible analysis based on content
                if "hardware" in content.lower():
                    category = "hardware_issue"
                    component = "general_hardware"
                else:
                    category = "general_inquiry"
                    component = "information"
                
                # Randomize sentiment
                sentiment = random.choice(["positive", "neutral", "negative"])
                
                return {
                    "sentiment": {
                        "polarity": sentiment,
                        "urgency_level": random.randint(1, 5),
                        "frustration_level": random.randint(0, 5)
                    },
                    "category": category,
                    "component": component,
                    "confidence": random.uniform(0.7, 0.98)
                }
            
            mock_claude.return_value.analyze_content.side_effect = mock_analyze
            
            # Act - Analyze all random tickets
            results = []
            for ticket in random_tickets:
                result = analyzer.analyze_ticket(ticket)
                results.append(result)
            
            # Assert
            # All tickets should get analysis results
            assert len(results) == 20
            
            # Check for expected structure in all results
            for result in results:
                assert "sentiment" in result
                assert "category" in result
                assert "component" in result
                assert "confidence" in result
    
    def test_fuzzing_ticket_parser(self, fake):
        """Test ticket parser with randomly fuzzed input data."""
        # Arrange
        from src.ticket_parser import TicketParser
        parser = TicketParser()
        
        # Generate 100 fuzzed tickets to test edge cases
        test_count = 100
        parsed_count = 0
        
        # Generate and test randomly fuzzed tickets
        for _ in range(test_count):
            # Start with valid ticket structure
            ticket = self.generate_random_ticket(fake)
            
            # Apply random fuzzing operations
            if random.random() > 0.7:
                # Remove random fields
                keys = list(ticket.keys())
                for _ in range(random.randint(1, 3)):
                    if keys and random.random() > 0.5:
                        key = random.choice(keys)
                        keys.remove(key)
                        del ticket[key]
            
            if random.random() > 0.7:
                # Add malformed data
                ticket[fake.word()] = None if random.random() > 0.5 else ""
            
            # Act - Try to parse the fuzzed ticket
            try:
                parsed_ticket = parser.parse(ticket)
                parsed_count += 1
            except Exception:
                # Expected some to fail
                pass
        
        # Assert
        # Should successfully parse at least 60% of fuzzed tickets
        success_rate = parsed_count / test_count
        assert success_rate >= 0.6, f"Parser only handled {success_rate*100:.1f}% of fuzzed inputs"
```

## Conclusion

This document has presented a variety of complex testing scenarios and techniques for the Zendesk AI Integration project. The examples provided demonstrate how to effectively test:

- Asynchronous and concurrent processing
- Rate limiting and retry logic
- Cache invalidation mechanisms
- Parallel processing performance and error handling
- Error propagation across component boundaries
- Database transaction atomicity and rollback behavior
- Long-running processes with timeouts and checkpoints
- Race conditions in multi-threaded code
- Time-dependent functionality through time mocking
- Complex data transformations and analysis
- System robustness through randomized and fuzzed inputs

By implementing these testing patterns, the Zendesk AI Integration project can achieve higher reliability, better performance, and more robust error handling. The test examples in this document supplement the main testing documentation and provide concrete implementation guidance for developers extending or maintaining the system.

For additional information on testing strategies and implementation, refer to:
- [TESTING.md](../TESTING.md): Main testing documentation and strategy
- [Test Optimization Guidelines](./test_optimization_guidelines.md): Performance optimization for tests
- [Official pytest Documentation](https://docs.pytest.org/): Reference for pytest features
