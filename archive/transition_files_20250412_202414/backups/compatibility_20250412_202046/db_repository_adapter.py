"""
DB Repository Adapter

This module provides an adapter that presents a DBRepository interface
but uses the new MongoDBRepository implementation internally.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from src.domain.interfaces.repository_interfaces import AnalysisRepository
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository

# Set up logging
logger = logging.getLogger(__name__)


class DBRepositoryAdapter:
    """
    Adapter that presents a DBRepository interface but uses MongoDBRepository internally.
    
    This adapter helps with the transition from the legacy DBRepository to the
    new MongoDBRepository implementation.
    """
    
    def __init__(self, repository=None):
        """
        Initialize the adapter.
        
        Args:
            repository: Optional MongoDBRepository instance (will create one if not provided)
        """
        self._repository = repository or MongoDBRepository()
        
        # For backward compatibility, expose the collection directly
        self.collection = self._repository.collection
        
        # For backward compatibility, expose the client
        self.client = self._repository.client
        
        # For backward compatibility, expose the database
        self.db = self._repository.db
        
        logger.debug("DBRepositoryAdapter initialized - using MongoDBRepository internally")
    
    def save_analysis(self, analysis, max_retries=3):
        """
        Save an analysis to the database.
        
        Args:
            analysis: Analysis data to save
            max_retries: Maximum number of retry attempts
            
        Returns:
            ID of the saved document
        """
        logger.debug(f"DBRepositoryAdapter.save_analysis called for ticket {analysis.get('ticket_id')}")
        
        return self._repository.save_analysis(analysis, max_retries)
    
    def get_analysis_by_ticket_id(self, ticket_id):
        """
        Get an analysis by ticket ID.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Analysis data or None if not found
        """
        logger.debug(f"DBRepositoryAdapter.get_analysis_by_ticket_id called for ticket {ticket_id}")
        
        return self._repository.get_analysis_by_ticket_id(ticket_id)
    
    def find_analyses_by_ticket_ids(self, ticket_ids):
        """
        Find analyses by a list of ticket IDs.
        
        Args:
            ticket_ids: List of ticket IDs
            
        Returns:
            List of analyses
        """
        logger.debug(f"DBRepositoryAdapter.find_analyses_by_ticket_ids called with {len(ticket_ids)} IDs")
        
        return self._repository.find_analyses_by_ticket_ids(ticket_ids)
    
    def find_analyses_for_view(self, view_id, days=None):
        """
        Find analyses for tickets in a specific view.
        
        Args:
            view_id: ID of the view
            days: Optional number of days to look back
            
        Returns:
            List of analyses
        """
        logger.debug(f"DBRepositoryAdapter.find_analyses_for_view called for view {view_id}, days={days}")
        
        return self._repository.find_analyses_for_view(view_id, days)
    
    def find_analyses_since(self, since_date):
        """
        Find analyses created since a specific date.
        
        Args:
            since_date: Date to look back from
            
        Returns:
            List of analyses
        """
        logger.debug(f"DBRepositoryAdapter.find_analyses_since called with date {since_date}")
        
        return self._repository.find_analyses_since(since_date)
    
    def find_analyses_between(self, start_date, end_date):
        """
        Find analyses created between two dates.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of analyses
        """
        logger.debug(f"DBRepositoryAdapter.find_analyses_between called with dates {start_date} to {end_date}")
        
        return self._repository.find_analyses_between(start_date, end_date)
    
    def update_analysis(self, analysis):
        """
        Update an existing analysis.
        
        Args:
            analysis: Updated analysis data
            
        Returns:
            Success indicator
        """
        logger.debug(f"DBRepositoryAdapter.update_analysis called for ticket {analysis.get('ticket_id')}")
        
        return self._repository.update_analysis(analysis)
    
    def delete_analysis(self, ticket_id):
        """
        Delete an analysis by ticket ID.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Success indicator
        """
        logger.debug(f"DBRepositoryAdapter.delete_analysis called for ticket {ticket_id}")
        
        return self._repository.delete_analysis(ticket_id)
    
    def ensure_indexes(self):
        """
        Ensure all required indexes exist.
        
        Returns:
            Success indicator
        """
        logger.debug("DBRepositoryAdapter.ensure_indexes called")
        
        return self._repository.ensure_indexes()
