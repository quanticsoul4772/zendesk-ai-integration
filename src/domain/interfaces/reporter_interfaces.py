"""
Reporter Interfaces

This module defines interfaces for reporters that generate reports based on ticket data.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis


class Reporter(ABC):
    """Base interface for all reporters."""

    @abstractmethod
    def generate_report(self, data: Any, **kwargs) -> str:
        """
        Generate a report.

        Args:
            data: Data to include in the report
            **kwargs: Additional arguments

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


class SentimentReporter(Reporter):
    """Interface for sentiment analysis reporters."""

    @abstractmethod
    def generate_report(self, analyses: List[TicketAnalysis], **kwargs) -> str:
        """
        Generate a sentiment analysis report.

        Args:
            analyses: List of ticket analyses to include in the report
            **kwargs: Additional arguments

        Returns:
            Report text
        """
        pass

    @abstractmethod
    def calculate_sentiment_distribution(self, analyses: List[TicketAnalysis]) -> Dict[str, int]:
        """
        Calculate sentiment distribution.

        Args:
            analyses: List of ticket analyses

        Returns:
            Dictionary mapping sentiment polarities to counts
        """
        pass

    @abstractmethod
    def calculate_priority_distribution(self, analyses: List[TicketAnalysis]) -> Dict[int, int]:
        """
        Calculate priority distribution.

        Args:
            analyses: List of ticket analyses

        Returns:
            Dictionary mapping priority scores to counts
        """
        pass

    @abstractmethod
    def calculate_business_impact_count(self, analyses: List[TicketAnalysis]) -> int:
        """
        Calculate the number of tickets with business impact.

        Args:
            analyses: List of ticket analyses

        Returns:
            Count of tickets with business impact
        """
        pass


class HardwareReporter(Reporter):
    """Interface for hardware component reporters."""

    @abstractmethod
    def generate_report(self, tickets: List[Ticket], **kwargs) -> str:
        """
        Generate a hardware component report.

        Args:
            tickets: List of tickets to include in the report
            **kwargs: Additional arguments

        Returns:
            Report text
        """
        pass

    @abstractmethod
    def generate_multi_view_report(self, tickets: List[Ticket], view_map: Dict[int, str]) -> str:
        """
        Generate a multi-view hardware component report.

        Args:
            tickets: List of tickets to include in the report
            view_map: Dictionary mapping view IDs to view names

        Returns:
            Report text
        """
        pass

    @abstractmethod
    def calculate_component_distribution(self, tickets: List[Ticket]) -> Dict[str, int]:
        """
        Calculate component distribution.

        Args:
            tickets: List of tickets

        Returns:
            Dictionary mapping component types to counts
        """
        pass


class PendingReporter(Reporter):
    """Interface for pending ticket reporters."""

    @abstractmethod
    def generate_report(self, tickets: List[Ticket], **kwargs) -> str:
        """
        Generate a pending ticket report.

        Args:
            tickets: List of tickets to include in the report
            **kwargs: Additional arguments

        Returns:
            Report text
        """
        pass

    @abstractmethod
    def generate_multi_view_report(self, tickets_by_view: Dict[str, List[Ticket]], **kwargs) -> str:
        """
        Generate a multi-view pending ticket report.

        Args:
            tickets_by_view: Dictionary mapping view names to lists of tickets
            **kwargs: Additional arguments

        Returns:
            Report text
        """
        pass

    @abstractmethod
    def calculate_age_distribution(self, tickets: List[Ticket]) -> Dict[str, int]:
        """
        Calculate age distribution of pending tickets.

        Args:
            tickets: List of tickets

        Returns:
            Dictionary mapping age ranges to counts
        """
        pass
