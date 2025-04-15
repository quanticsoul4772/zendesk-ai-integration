"""
Ticket DTO

This module defines the TicketDTO (Data Transfer Object) for transferring ticket data
between layers of the application.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket import Ticket


@dataclass
class TicketDTO:
    """Data Transfer Object for Ticket entity."""
    
    id: int
    subject: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    requester_id: Optional[int] = None
    assignee_id: Optional[int] = None
    source_view_id: Optional[int] = None
    source_view_name: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_entity(cls, entity: Ticket) -> 'TicketDTO':
        """
        Create a TicketDTO from a Ticket entity.
        
        Args:
            entity: Ticket entity
            
        Returns:
            TicketDTO instance
        """
        return cls(
            id=entity.id,
            subject=entity.subject,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            tags=entity.tags.copy() if entity.tags else [],
            priority=entity.priority,
            requester_id=entity.requester_id,
            assignee_id=entity.assignee_id,
            source_view_id=entity.source_view_id,
            source_view_name=entity.source_view_name,
            custom_fields=entity.custom_fields.copy() if entity.custom_fields else {}
        )
    
    def to_entity(self) -> Ticket:
        """
        Convert to a Ticket entity.
        
        Returns:
            Ticket entity
        """
        return Ticket(
            id=self.id,
            subject=self.subject,
            description=self.description,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tags=self.tags.copy() if self.tags else [],
            priority=self.priority,
            requester_id=self.requester_id,
            assignee_id=self.assignee_id,
            source_view_id=self.source_view_id,
            source_view_name=self.source_view_name,
            custom_fields=self.custom_fields.copy() if self.custom_fields else {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary.
        
        Returns:
            Dictionary representation
        """
        # Convert to dict using dataclasses.asdict
        result = asdict(self)
        
        # Handle datetime objects
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        result['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        
        return result
