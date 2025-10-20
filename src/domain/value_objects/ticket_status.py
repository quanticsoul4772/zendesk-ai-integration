"""
Ticket Status Value Object

This module defines the TicketStatus value object, which represents the status of a Zendesk ticket.
"""

from enum import Enum, auto


class TicketStatus(str, Enum):
    """Represents the status of a Zendesk ticket."""
    OPEN = "open"
    NEW = "new"
    PENDING = "pending"
    SOLVED = "solved"
    CLOSED = "closed"
    ALL = "all"  # Special value for filtering

    @classmethod
    def from_string(cls, status_str: str) -> 'TicketStatus':
        """
        Create a TicketStatus from a string.

        Args:
            status_str: String representation of the status

        Returns:
            TicketStatus enum value

        Raises:
            ValueError: If the status string is invalid
        """
        try:
            return cls(status_str.lower())
        except ValueError:
            raise ValueError(f"Invalid ticket status: {status_str}")

    @classmethod
    def active_statuses(cls) -> list['TicketStatus']:
        """
        Get a list of active ticket statuses.

        Returns:
            List of active ticket statuses (OPEN, NEW, PENDING)
        """
        return [cls.OPEN, cls.NEW, cls.PENDING]

    @classmethod
    def closed_statuses(cls) -> list['TicketStatus']:
        """
        Get a list of closed ticket statuses.

        Returns:
            List of closed ticket statuses (SOLVED, CLOSED)
        """
        return [cls.SOLVED, cls.CLOSED]

    def is_active(self) -> bool:
        """
        Check if the ticket status is active.

        Returns:
            True if the status is active, False otherwise
        """
        return self in self.active_statuses()

    def is_closed(self) -> bool:
        """
        Check if the ticket status is closed.

        Returns:
            True if the status is closed, False otherwise
        """
        return self in self.closed_statuses()
