"""
Ticket Priority Value Object

This module defines the TicketPriority value object, which represents the priority of a Zendesk ticket.
"""

from enum import Enum


class TicketPriority(str, Enum):
    """Represents the priority of a Zendesk ticket."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, priority_str: str) -> 'TicketPriority':
        """
        Create a TicketPriority from a string.
        
        Args:
            priority_str: String representation of the priority
            
        Returns:
            TicketPriority enum value
        """
        if not priority_str:
            return cls.UNKNOWN
            
        try:
            return cls(priority_str.lower())
        except ValueError:
            return cls.UNKNOWN
    
    def to_score(self) -> int:
        """
        Convert priority to a numeric score.
        
        Returns:
            Numeric score (1-10, with 10 being highest priority)
        """
        return {
            self.LOW: 3,
            self.MEDIUM: 5,
            self.HIGH: 7,
            self.URGENT: 9,
            self.UNKNOWN: 1
        }[self]
    
    @classmethod
    def from_score(cls, score: int) -> 'TicketPriority':
        """
        Create a TicketPriority from a numeric score.
        
        Args:
            score: Numeric priority score (1-10)
            
        Returns:
            TicketPriority enum value
        """
        if score >= 8:
            return cls.URGENT
        elif score >= 6:
            return cls.HIGH
        elif score >= 4:
            return cls.MEDIUM
        elif score >= 2:
            return cls.LOW
        else:
            return cls.UNKNOWN
