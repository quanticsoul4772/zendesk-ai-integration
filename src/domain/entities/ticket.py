"""
Ticket Entity

This module defines the Ticket entity for representing Zendesk tickets.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Ticket:
    """
    Entity representing a Zendesk ticket.
    
    This entity contains ticket data retrieved from the Zendesk API.
    """
    
    id: int
    """Zendesk ticket ID."""
    
    subject: str
    """Subject of the ticket."""
    
    description: Optional[str] = None
    """Description or first comment of the ticket."""
    
    comments: List[Dict[str, Any]] = field(default_factory=list)
    """List of all comments on the ticket."""
    
    status: str = "new"
    """
    Status of the ticket.
    Typical values: 'new', 'open', 'pending', 'hold', 'solved', 'closed'.
    """
    
    priority: Optional[str] = None
    """
    Priority of the ticket.
    Typical values: 'low', 'normal', 'high', 'urgent'.
    """
    
    tags: List[str] = field(default_factory=list)
    """Tags applied to the ticket."""
    
    created_at: Optional[datetime] = None
    """Timestamp when the ticket was created."""
    
    updated_at: Optional[datetime] = None
    """Timestamp when the ticket was last updated."""
    
    requester_id: Optional[int] = None
    """ID of the requester (customer)."""
    
    assignee_id: Optional[int] = None
    """ID of the assignee (agent)."""
    
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    """Custom fields on the ticket."""
    
    source_view_id: Optional[int] = None
    """ID of the view this ticket was retrieved from (if applicable)."""
    
    source_view_name: Optional[str] = None
    """Name of the view this ticket was retrieved from (if applicable)."""
    
    @classmethod
    def from_zendesk_ticket(cls, zendesk_ticket) -> 'Ticket':
        """
        Create a Ticket entity from a Zendesk API ticket object.
        
        Args:
            zendesk_ticket: Zendesk API ticket object
            
        Returns:
            Ticket entity
        """
        # Extract basic ticket data
        ticket = cls(
            id=zendesk_ticket.id,
            subject=zendesk_ticket.subject or "No Subject"
        )
        
        # Extract optional fields
        if hasattr(zendesk_ticket, 'description'):
            ticket.description = zendesk_ticket.description
        
        if hasattr(zendesk_ticket, 'status'):
            ticket.status = zendesk_ticket.status
        
        if hasattr(zendesk_ticket, 'priority'):
            ticket.priority = zendesk_ticket.priority
        
        if hasattr(zendesk_ticket, 'tags'):
            ticket.tags = list(zendesk_ticket.tags) if zendesk_ticket.tags else []
        
        if hasattr(zendesk_ticket, 'created_at'):
            ticket.created_at = zendesk_ticket.created_at
        
        if hasattr(zendesk_ticket, 'updated_at'):
            ticket.updated_at = zendesk_ticket.updated_at
        
        if hasattr(zendesk_ticket, 'requester_id'):
            ticket.requester_id = zendesk_ticket.requester_id
        
        if hasattr(zendesk_ticket, 'assignee_id'):
            ticket.assignee_id = zendesk_ticket.assignee_id
        
        # Extract comments
        if hasattr(zendesk_ticket, 'comments'):
            ticket.comments = [
                {
                    'id': comment.id,
                    'body': comment.body,
                    'author_id': comment.author_id,
                    'created_at': comment.created_at,
                    'public': comment.public
                }
                for comment in zendesk_ticket.comments
            ]
        # For first comment/description if comments not available
        elif hasattr(zendesk_ticket, 'description') and zendesk_ticket.description:
            ticket.comments = [
                {
                    'id': 0,  # Placeholder ID
                    'body': zendesk_ticket.description,
                    'author_id': ticket.requester_id,
                    'created_at': ticket.created_at,
                    'public': True
                }
            ]
        
        # Extract custom fields
        if hasattr(zendesk_ticket, 'custom_fields'):
            ticket.custom_fields = {}
            try:
                # Try handling custom fields as dictionaries with value attribute
                for field in zendesk_ticket.custom_fields:
                    if hasattr(field, 'id') and hasattr(field, 'value'):
                        if field.value is not None:
                            ticket.custom_fields[field.id] = field.value
            except AttributeError:
                # Handle case where custom_fields might be a different structure
                try:
                    # Try as a dictionary itself
                    if isinstance(zendesk_ticket.custom_fields, dict):
                        ticket.custom_fields = {k: v for k, v in zendesk_ticket.custom_fields.items() if v is not None}
                    # Handle ProxyDict case
                    elif hasattr(zendesk_ticket.custom_fields, 'items') and callable(getattr(zendesk_ticket.custom_fields, 'items')):
                        for k, v in zendesk_ticket.custom_fields.items():
                            if v is not None:
                                ticket.custom_fields[k] = v
                except Exception as e:
                    # If all else fails, log and continue without custom fields
                    import logging
                    logging.getLogger(__name__).warning(f"Could not process custom fields: {e}")
        
        # Extract source view info if available
        if hasattr(zendesk_ticket, 'source_view_id'):
            ticket.source_view_id = zendesk_ticket.source_view_id
        
        if hasattr(zendesk_ticket, 'source_view_name'):
            ticket.source_view_name = zendesk_ticket.source_view_name
        
        return ticket
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the ticket
        """
        return {
            'id': self.id,
            'subject': self.subject,
            'description': self.description,
            'comments': self.comments,
            'status': self.status,
            'priority': self.priority,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'requester_id': self.requester_id,
            'assignee_id': self.assignee_id,
            'custom_fields': self.custom_fields,
            'source_view_id': self.source_view_id,
            'source_view_name': self.source_view_name
        }
    
    @property
    def full_content(self) -> str:
        """
        Get the full content of the ticket, including subject, description, and comments.
        
        Returns:
            Concatenated ticket content
        """
        content = f"Subject: {self.subject}\n\n"
        
        if self.description:
            content += f"Description:\n{self.description}\n\n"
        
        if self.comments:
            content += "Comments:\n"
            for i, comment in enumerate(self.comments):
                content += f"Comment {i+1} ({'Public' if comment.get('public', True) else 'Private'}):\n"
                content += f"{comment.get('body', '')}\n\n"
        
        return content
