"""
Repository Interfaces

This module defines interfaces for repositories that handle data persistence.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis


class TicketRepository(ABC):
    """Interface for ticket repository."""

    @abstractmethod
    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """
        Get a ticket by ID.

        Args:
            ticket_id: ID of the ticket to fetch

        Returns:
            Ticket entity or None if not found
        """
        pass

    @abstractmethod
    def get_tickets(self, status: str = "open", limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets with the specified status.

        Args:
            status: Ticket status (open, new, pending, solved, closed, all)
            limit: Maximum number of tickets to fetch

        Returns:
            List of ticket entities
        """
        pass

    @abstractmethod
    def get_tickets_from_view(self, view_id: int, limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from a specific view.

        Args:
            view_id: ID of the view to fetch tickets from
            limit: Maximum number of tickets to fetch

        Returns:
            List of ticket entities
        """
        pass

    @abstractmethod
    def get_tickets_from_view_name(self, view_name: str, limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from a view by name.

        Args:
            view_name: Name of the view to fetch tickets from
            limit: Maximum number of tickets to fetch

        Returns:
            List of ticket entities
        """
        pass

    @abstractmethod
    def get_tickets_from_multiple_views(self, view_ids: List[int], limit: Optional[int] = None) -> List[Ticket]:
        """
        Get tickets from multiple views.

        Args:
            view_ids: List of view IDs to fetch tickets from
            limit: Maximum number of tickets per view

        Returns:
            List of ticket entities
        """
        pass

    @abstractmethod
    def add_ticket_tags(self, ticket_id: int, tags: List[str]) -> bool:
        """
        Add tags to a ticket.

        Args:
            ticket_id: ID of the ticket to update
            tags: List of tags to add

        Returns:
            Success indicator
        """
        pass

    @abstractmethod
    def add_ticket_comment(self, ticket_id: int, comment: str, public: bool = False) -> bool:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: ID of the ticket to update
            comment: Comment text
            public: Whether the comment should be public

        Returns:
            Success indicator
        """
        pass


class AnalysisRepository(ABC):
    """Interface for ticket analysis repository."""

    @abstractmethod
    def save(self, analysis: TicketAnalysis) -> str:
        """
        Save a ticket analysis.

        Args:
            analysis: Ticket analysis to save

        Returns:
            ID of the saved analysis
        """
        pass

    @abstractmethod
    def get_by_ticket_id(self, ticket_id: str) -> Optional[TicketAnalysis]:
        """
        Get the most recent analysis for a ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            Most recent ticket analysis or None if not found
        """
        pass

    @abstractmethod
    def find_between_dates(self, start_date: datetime, end_date: datetime) -> List[TicketAnalysis]:
        """
        Find analyses between two dates.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of ticket analyses
        """
        pass

    @abstractmethod
    def find_by_category(self, category: str) -> List[TicketAnalysis]:
        """
        Find analyses by category.

        Args:
            category: Category to search for

        Returns:
            List of ticket analyses
        """
        pass

    @abstractmethod
    def find_high_priority(self, min_score: int = 7) -> List[TicketAnalysis]:
        """
        Find high priority analyses.

        Args:
            min_score: Minimum priority score to consider high priority

        Returns:
            List of high priority ticket analyses
        """
        pass

    @abstractmethod
    def find_with_business_impact(self) -> List[TicketAnalysis]:
        """
        Find analyses with business impact.

        Returns:
            List of ticket analyses with business impact
        """
        pass

    @abstractmethod
    def update(self, analysis: TicketAnalysis) -> bool:
        """
        Update an existing analysis.

        Args:
            analysis: Updated ticket analysis

        Returns:
            Success indicator
        """
        pass


class ViewRepository(ABC):
    """Interface for Zendesk view repository."""

    @abstractmethod
    def get_all_views(self) -> List[Dict[str, Any]]:
        """
        Get all available views.

        Returns:
            List of view objects
        """
        pass

    @abstractmethod
    def get_view_by_id(self, view_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a view by ID.

        Args:
            view_id: ID of the view to fetch

        Returns:
            View object or None if not found
        """
        pass

    @abstractmethod
    def get_view_by_name(self, view_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a view by name.

        Args:
            view_name: Name of the view to fetch

        Returns:
            View object or None if not found
        """
        pass

    @abstractmethod
    def get_view_names_by_ids(self, view_ids: List[int]) -> Dict[int, str]:
        """
        Get a mapping of view IDs to their names.

        Args:
            view_ids: List of view IDs

        Returns:
            Dictionary mapping view IDs to view names
        """
        pass
