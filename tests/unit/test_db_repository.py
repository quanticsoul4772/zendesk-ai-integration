"""
Unit Tests for Database Repository Module

Tests the functionality of the db_repository.py module.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import sys
from datetime import datetime, timedelta
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository

# Import module to test
# from src.infrastructure.compatibility import DBRepository


class TestDBRepository:
    """Test suite for Database Repository functionality."""
    
    def test_connection_initialization(self, mock_mongodb):
        """Test database connection initialization."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Create repository instance
        repo = DBRepository()
        
        # Assert connection was established
        mock_client_class.assert_called_once()
        
        # Assert database and collection are set
        assert repo.db == mock_db
        assert repo.collection == mock_collection
        
        # Assert indexes were checked
        mock_collection.index_information.assert_called_once()
    
    def test_ensure_indexes(self, mock_mongodb):
        """Test index creation functionality."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Configure mock to return empty index information (no indexes exist)
        mock_collection.index_information.return_value = {}
        
        # Create repository instance
        repo = DBRepository()
        
        # Assert that indexes were created
        assert mock_collection.create_index.call_count == 2
        
        # Verify the right indexes were created
        index_calls = [call([("ticket_id", 1)], background=True), 
                       call([("timestamp", 1)], background=True)]
        mock_collection.create_index.assert_has_calls(index_calls, any_order=True)
    
    def test_save_analysis_success(self, mock_mongodb):
        """Test successful analysis data saving."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Configure mock to return a successful insert result
        inserted_id = "mock_id_12345"
        mock_collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)
        
        # Create repository instance
        repo = DBRepository()
        
        # Test data
        analysis_data = {
            "ticket_id": "12345",
            "sentiment": "negative",
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.9
        }
        
        # Call the function being tested
        result = repo.save_analysis(analysis_data)
        
        # Assertions
        assert result == inserted_id
        
        # Verify insert_one was called with the right data
        mock_collection.insert_one.assert_called_once()
        
        # Verify timestamp was added if not provided
        insert_data = mock_collection.insert_one.call_args[0][0]
        assert "timestamp" in insert_data
        assert isinstance(insert_data["timestamp"], datetime)
    
    def test_save_analysis_with_retry(self, mock_mongodb):
        """Test retry logic for failed database operations."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Configure mock to fail once, then succeed
        mock_collection.insert_one.side_effect = [
            Exception("Connection timeout"),
            MagicMock(inserted_id="mock_id_after_retry")
        ]
        
        # Create repository instance
        repo = DBRepository()
        
        # Test data
        analysis_data = {"ticket_id": "12345"}
        
        # Call the function being tested
        result = repo.save_analysis(analysis_data)
        
        # Assertions
        assert result == "mock_id_after_retry"
        assert mock_collection.insert_one.call_count == 2
    
    def test_save_analysis_max_retries_exceeded(self, mock_mongodb):
        """Test behavior when max retries are exceeded."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Configure mock to always fail with connection errors
        mock_collection.insert_one.side_effect = Exception("Connection timeout")
        
        # Create repository instance
        repo = DBRepository()
        
        # Test data
        analysis_data = {"ticket_id": "12345"}
        
        # Call the function being tested with a low max_retries value
        result = repo.save_analysis(analysis_data, max_retries=2)
        
        # Assertions
        assert result is None
        assert mock_collection.insert_one.call_count == 2
    
    def test_find_analyses_since(self, mock_mongodb):
        """Test finding analyses since a cutoff date."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Test data
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        expected_results = [
            {"ticket_id": "12345", "timestamp": datetime.utcnow()},
            {"ticket_id": "12346", "timestamp": datetime.utcnow()}
        ]
        
        # Configure mock to return expected results
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter(expected_results)
        mock_collection.find.return_value = mock_cursor
        
        # Create repository instance
        repo = DBRepository()
        
        # Call the function being tested
        results = repo.find_analyses_since(cutoff_date)
        
        # Assertions
        assert results == expected_results
        
        # Verify find was called with the right query
        mock_collection.find.assert_called_once()
        query = mock_collection.find.call_args[0][0]
        assert "timestamp" in query
        assert "$gte" in query["timestamp"]
        assert query["timestamp"]["$gte"] == cutoff_date
    
    def test_find_analyses_between(self, mock_mongodb):
        """Test finding analyses between two dates."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Test data
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        expected_results = [
            {"ticket_id": "12345", "timestamp": datetime.utcnow() - timedelta(days=5)},
            {"ticket_id": "12346", "timestamp": datetime.utcnow() - timedelta(days=3)}
        ]
        
        # Configure mock to return expected results
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter(expected_results)
        mock_collection.find.return_value = mock_cursor
        
        # Create repository instance
        repo = DBRepository()
        
        # Call the function being tested
        results = repo.find_analyses_between(start_date, end_date)
        
        # Assertions
        assert results == expected_results
        
        # Verify find was called with the right query
        mock_collection.find.assert_called_once()
        query = mock_collection.find.call_args[0][0]
        assert "timestamp" in query
        assert "$gte" in query["timestamp"]
        assert "$lte" in query["timestamp"]
        assert query["timestamp"]["$gte"] == start_date
        assert query["timestamp"]["$lte"] == end_date
    
    def test_find_high_priority_analyses(self, mock_mongodb):
        """Test finding high priority analyses."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Test data
        threshold = 7
        expected_results = [
            {"ticket_id": "12345", "priority_score": 8},
            {"ticket_id": "12346", "priority_score": 9}
        ]
        
        # Configure mock to return expected results
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter(expected_results)
        mock_collection.find.return_value = mock_cursor
        
        # Create repository instance
        repo = DBRepository()
        
        # Call the function being tested
        results = repo.find_high_priority_analyses(threshold)
        
        # Assertions
        assert results == expected_results
        
        # Verify find was called with the right query
        mock_collection.find.assert_called_once()
        query = mock_collection.find.call_args[0][0]
        assert "priority_score" in query
        assert "$gte" in query["priority_score"]
        assert query["priority_score"]["$gte"] == threshold
    
    def test_get_analysis_by_ticket_id(self, mock_mongodb):
        """Test getting analysis by ticket ID."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        
        # Test data
        ticket_id = "12345"
        expected_result = {
            "ticket_id": ticket_id,
            "sentiment": "negative",
            "category": "hardware_issue",
            "timestamp": datetime.utcnow()
        }
        
        # Configure mock to return expected result
        mock_collection.find_one.return_value = expected_result
        
        # Create repository instance
        repo = DBRepository()
        
        # Call the function being tested
        result = repo.get_analysis_by_ticket_id(ticket_id)
        
        # Assertions
        assert result == expected_result
        
        # Verify find_one was called with the right query
        mock_collection.find_one.assert_called_once()
        args = mock_collection.find_one.call_args
        query = args[0][0]
        sort = args[1].get("sort")
        
        assert query == {"ticket_id": ticket_id}
        assert sort == [("timestamp", -1)]  # Should sort by timestamp descending
    
    def test_close_connection(self, mock_mongodb):
        """Test closing the database connection."""
        mock_client_class, mock_db, mock_collection = mock_mongodb
        mock_client = mock_client_class.return_value
        
        # Create repository instance
        repo = DBRepository()
        
        # Call the function being tested
        repo.close()
        
        # Verify client.close was called
        mock_client.close.assert_called_once()
        
        # Verify client is set to None
        assert repo.client is None