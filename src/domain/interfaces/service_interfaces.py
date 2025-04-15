"""
Service Interfaces

This module defines interfaces for services that orchestrate business logic.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis


class TicketAnalysisService(ABC):
    """Interface for ticket analysis service."""
    
    @abstractmethod
    def analyze_ticket(self, ticket_id: int) -> TicketAnalysis:
        """
        Analyze a ticket by ID.
        
        Args:
            ticket_id: ID of the ticket to analyze
            
        Returns:
            Ticket analysis entity
            
        Raises:
            ValueError: If ticket not found
            AIServiceError: If analysis fails
        """
        pass
    
    @abstractmethod
    def analyze_ticket_content(self, ticket: Ticket) -> TicketAnalysis:
        """
        Analyze a ticket's content.
        
        Args:
            ticket: Ticket entity to analyze
            
        Returns:
            Ticket analysis entity
            
        Raises:
            AIServiceError: If analysis fails
        """
        pass
    
    @abstractmethod
    def analyze_batch(self, ticket_ids: List[int]) -> List[TicketAnalysis]:
        """
        Analyze multiple tickets by ID.
        
        Args:
            ticket_ids: List of ticket IDs to analyze
            
        Returns:
            List of ticket analysis entities
        """
        pass
    
    @abstractmethod
    def analyze_view(self, view_id: int, limit: Optional[int] = None) -> List[TicketAnalysis]:
        """
        Analyze tickets from a view.
        
        Args:
            view_id: ID of the view
            limit: Maximum number of tickets to analyze
            
        Returns:
            List of ticket analysis entities
        """
        pass
    
    @abstractmethod
    def get_analysis_history(self, ticket_id: int) -> List[TicketAnalysis]:
        """
        Get analysis history for a ticket.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            List of ticket analysis entities in chronological order
        """
        pass
    
    @abstractmethod
    def get_sentiment_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get sentiment statistics for a time period.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            Dictionary with sentiment statistics
        """
        pass


class ReportingService(ABC):
    """Interface for reporting service."""
    
    @abstractmethod
    def generate_sentiment_report(self, time_period: str = "week", view_id: Optional[int] = None) -> str:
        """
        Generate a sentiment analysis report.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            view_id: Optional view ID to filter by
            
        Returns:
            Report text
        """
        pass
    
    @abstractmethod
    def generate_hardware_report(self, view_id: Optional[int] = None, limit: Optional[int] = None) -> str:
        """
        Generate a hardware component report.
        
        Args:
            view_id: Optional view ID to filter by
            limit: Maximum number of tickets to include
            
        Returns:
            Report text
        """
        pass
    
    @abstractmethod
    def generate_pending_report(self, view_name: str, limit: Optional[int] = None) -> str:
        """
        Generate a pending ticket report.
        
        Args:
            view_name: Name of the pending view
            limit: Maximum number of tickets to include
            
        Returns:
            Report text
        """
        pass
    
    @abstractmethod
    def generate_multi_view_report(self, view_ids: List[int], report_type: str, limit: Optional[int] = None) -> str:
        """
        Generate a multi-view report.
        
        Args:
            view_ids: List of view IDs to include
            report_type: Type of report ('sentiment', 'hardware', 'pending')
            limit: Maximum number of tickets per view
            
        Returns:
            Report text
        """
        pass
    
    @abstractmethod
    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """
        Save a report to a file.
        
        Args:
            report: Report text
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to the saved report file
        """
        pass


class WebhookService(ABC):
    """Interface for webhook service."""
    
    @abstractmethod
    def handle_ticket_created(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Handle a ticket created webhook event.
        
        Args:
            ticket_data: Webhook data for the created ticket
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def handle_ticket_updated(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Handle a ticket updated webhook event.
        
        Args:
            ticket_data: Webhook data for the updated ticket
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def handle_comment_created(self, comment_data: Dict[str, Any]) -> bool:
        """
        Handle a comment created webhook event.
        
        Args:
            comment_data: Webhook data for the created comment
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def set_comment_preference(self, add_comments: bool) -> None:
        """
        Set preference for adding comments to tickets.
        
        Args:
            add_comments: Whether to add comments with analysis results
        """
        pass


class SchedulerService(ABC):
    """Interface for scheduler service."""
    
    @abstractmethod
    def schedule_task(self, task_name: str, interval_minutes: int, func: callable, *args, **kwargs) -> bool:
        """
        Schedule a task to run at regular intervals.
        
        Args:
            task_name: Name of the task
            interval_minutes: Interval in minutes
            func: Function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def remove_task(self, task_name: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_name: Name of the task to remove
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all scheduled tasks.
        
        Returns:
            List of task information
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the scheduler."""
        pass
