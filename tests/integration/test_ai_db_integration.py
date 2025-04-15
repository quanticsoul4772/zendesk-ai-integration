"""
Integration Tests for AI and Database Components

Tests the integration between AI analyzers and database repository components.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
from src.application.services.ticket_analysis_service import TicketAnalysisService
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the components to test
# from src.infrastructure.compatibility import AIAnalyzer
# from src.infrastructure.compatibility import DBRepository


class TestAIDBIntegration:
    """Test suite for AI and Database integration."""
    
    @pytest.fixture
    def mock_claude_service(self):
        """Fixture for mocked Claude API."""
        with patch('src.claude_service.call_claude_with_retries') as mock_call:
            mock_call.return_value = {
                "sentiment": {
                    "polarity": "negative",
                    "urgency_level": 4,
                    "frustration_level": 3,
                    "business_impact": {"detected": True, "description": "Production impact"}
                },
                "category": "hardware_issue",
                "component": "gpu",
                "confidence": 0.9
            }
            yield mock_call
    
    @pytest.fixture
    def mock_mongodb(self):
        """Fixture for mocked MongoDB client."""
        with patch('pymongo.MongoClient') as mock_client:
            # Configure mock collection
            mock_collection = MagicMock()
            mock_db = MagicMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_client.return_value.__getitem__.return_value = mock_db
            
            # Configure insert_one to return an ID
            mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id_12345")
            
            yield mock_client, mock_db, mock_collection
    
    @pytest.fixture
    def mock_ticket(self):
        """Create a mock Zendesk ticket for testing."""
        ticket = MagicMock()
        ticket.id = "12345"
        ticket.subject = "Test GPU Issue"
        ticket.description = "My GPU keeps crashing during rendering jobs."
        ticket.status = "open"
        return ticket
    
    @pytest.fixture
    def ai_analyzer(self, mock_claude_service):
        """Create an AI analyzer instance with mocked services."""
        return AIAnalyzer()
    
    @pytest.fixture
    def db_repository(self, mock_mongodb):
        """Create a DBRepository instance with mocked MongoDB."""
        return DBRepository()
    
    def test_analyze_and_save(self, ai_analyzer, db_repository, mock_ticket):
        """Test analyzing a ticket and saving results to the database."""
        # Analyze the ticket
        analysis_result = ai_analyzer.analyze_ticket(
            ticket_id=mock_ticket.id,
            subject=mock_ticket.subject,
            description=mock_ticket.description,
            use_claude=True
        )
        
        # Verify analysis result has expected fields
        assert analysis_result["ticket_id"] == mock_ticket.id
        assert analysis_result["subject"] == mock_ticket.subject
        assert "sentiment" in analysis_result
        assert "priority_score" in analysis_result
        
        # Save to database
        doc_id = db_repository.save_analysis(analysis_result)
        
        # Verify save operation
        assert doc_id is not None
        assert doc_id == "mock_id_12345"
        
        # Verify insert_one was called with the right data
        mock_collection = db_repository.collection
        mock_collection.insert_one.assert_called_once()
        
        # Check the data that was inserted
        inserted_data = mock_collection.insert_one.call_args[0][0]
        assert inserted_data["ticket_id"] == mock_ticket.id
        assert inserted_data["subject"] == mock_ticket.subject
        assert "sentiment" in inserted_data
        assert "timestamp" in inserted_data
    
    def test_retrieve_analyses(self, ai_analyzer, db_repository, mock_ticket):
        """Test retrieving analyses from the database."""
        # Configure mock to return test data
        test_analyses = [
            {
                "ticket_id": "12345",
                "subject": "Test Subject",
                "sentiment": {"polarity": "negative"},
                "priority_score": 8,
                "timestamp": datetime.utcnow()
            }
        ]
        db_repository.collection.find.return_value = test_analyses
        
        # Define a cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        # Retrieve analyses
        results = db_repository.find_analyses_since(cutoff_date)
        
        # Verify results
        assert results == test_analyses
        
        # Verify find was called with correct parameters
        db_repository.collection.find.assert_called_once()
        query = db_repository.collection.find.call_args[0][0]
        assert "timestamp" in query
        assert "$gte" in query["timestamp"]
        assert query["timestamp"]["$gte"] == cutoff_date
    
    def test_batch_analyze_and_save(self, ai_analyzer, db_repository):
        """Test batch analyzing multiple tickets and saving all results."""
        # Create test tickets
        test_tickets = []
        for i in range(3):
            ticket = MagicMock()
            ticket.id = str(10000 + i)
            ticket.subject = f"Test Subject {i}"
            ticket.description = f"Test Description {i}"
            test_tickets.append(ticket)
        
        # Configure batch processor in ai_analyzer to use only one worker for predictability
        ai_analyzer.batch_processor.max_workers = 1
        
        # Analyze all tickets in batch
        analysis_results = ai_analyzer.analyze_tickets_batch(test_tickets, use_claude=True)
        
        # Verify results
        assert len(analysis_results) == 3
        for i, result in enumerate(analysis_results):
            assert result["ticket_id"] == test_tickets[i].id
            assert result["subject"] == test_tickets[i].subject
        
        # Save all results to database
        for result in analysis_results:
            db_repository.save_analysis(result)
        
        # Verify save operations
        assert db_repository.collection.insert_one.call_count == 3
    
    def test_error_handling(self, ai_analyzer, db_repository, mock_ticket):
        """Test error handling during analysis and database operations."""
        # Configure mock to raise an exception
        db_repository.collection.insert_one.side_effect = Exception("Database connection error")
        
        # Analyze ticket
        analysis_result = ai_analyzer.analyze_ticket(
            ticket_id=mock_ticket.id,
            subject=mock_ticket.subject,
            description=mock_ticket.description,
            use_claude=True
        )
        
        # Try to save (this should handle the error)
        doc_id = db_repository.save_analysis(analysis_result, max_retries=2)
        
        # Verify outcome
        assert doc_id is None  # Should return None on failure
        assert db_repository.collection.insert_one.call_count == 2  # Should try twice
    
    def test_retrieve_by_ticket_id(self, ai_analyzer, db_repository, mock_ticket):
        """Test retrieving analysis by ticket ID."""
        # Configure mock to return test data
        test_analysis = {
            "ticket_id": mock_ticket.id,
            "subject": mock_ticket.subject,
            "sentiment": {"polarity": "negative"},
            "priority_score": 8,
            "timestamp": datetime.utcnow()
        }
        db_repository.collection.find_one.return_value = test_analysis
        
        # Retrieve analysis
        result = db_repository.get_analysis_by_ticket_id(mock_ticket.id)
        
        # Verify result
        assert result == test_analysis
        
        # Verify find_one was called with correct parameters
        db_repository.collection.find_one.assert_called_once()
        query = db_repository.collection.find_one.call_args[0][0]
        assert query == {"ticket_id": mock_ticket.id}
