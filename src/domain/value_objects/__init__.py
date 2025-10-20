"""
Value Objects Package

This package contains value objects for the Zendesk AI Integration application.
Value objects are immutable objects that represent concepts in the domain.
"""

from src.domain.value_objects.hardware_component import HardwareComponent
from src.domain.value_objects.sentiment_polarity import SentimentPolarity
from src.domain.value_objects.ticket_category import TicketCategory
from src.domain.value_objects.ticket_priority import TicketPriority
from src.domain.value_objects.ticket_status import TicketStatus

__all__ = [
    'TicketStatus',
    'TicketPriority',
    'SentimentPolarity',
    'TicketCategory',
    'HardwareComponent'
]
