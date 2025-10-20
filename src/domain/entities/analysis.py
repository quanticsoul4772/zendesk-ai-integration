"""
Analysis Entity

This module defines the Analysis entity for representing ticket analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Analysis:
    """
    Entity representing the analysis of a ticket.

    This entity contains the results of an AI analysis of a ticket,
    including sentiment, category, priority, and other attributes.
    """

    ticket_id: int
    """ID of the analyzed ticket."""

    subject: str
    """Subject of the analyzed ticket."""

    sentiment: str
    """
    Sentiment of the ticket.
    Typical values: 'Positive', 'Negative', 'Neutral', 'Very Positive', 'Very Negative'.
    """

    category: str
    """
    Category of the ticket.
    Examples: 'Technical Issue', 'Account Management', 'Billing Question', 'Feature Request'.
    """

    priority: str
    """
    Suggested priority for the ticket.
    Typical values: 'Low', 'Medium', 'High', 'Critical'.
    """

    hardware_components: List[str] = field(default_factory=list)
    """List of hardware components mentioned in the ticket."""

    business_impact: Optional[str] = None
    """Description of the business impact of the issue."""

    summary: Optional[str] = None
    """Brief summary of the ticket content."""

    status: str = "Completed"
    """Status of the analysis. Typical values: 'Pending', 'In Progress', 'Completed', 'Failed'."""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when the analysis was created."""

    updated_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when the analysis was last updated."""

    tags: List[str] = field(default_factory=list)
    """Tags generated from the analysis."""

    @classmethod
    def create(cls, ticket_id: int, subject: str, analysis_results: dict) -> 'Analysis':
        """
        Create an Analysis entity from analysis results.

        Args:
            ticket_id: ID of the analyzed ticket
            subject: Subject of the analyzed ticket
            analysis_results: Dictionary with analysis results

        Returns:
            Analysis entity
        """
        # Extract required fields
        sentiment = analysis_results.get('sentiment', 'Neutral')
        category = analysis_results.get('category', 'Uncategorized')
        priority = analysis_results.get('priority', 'Medium')

        # Create analysis entity
        analysis = cls(
            ticket_id=ticket_id,
            subject=subject,
            sentiment=sentiment,
            category=category,
            priority=priority
        )

        # Extract optional fields
        if 'hardware_components' in analysis_results:
            analysis.hardware_components = analysis_results['hardware_components']

        if 'business_impact' in analysis_results:
            analysis.business_impact = analysis_results['business_impact']

        if 'summary' in analysis_results:
            analysis.summary = analysis_results['summary']

        if 'tags' in analysis_results:
            analysis.tags = analysis_results['tags']

        return analysis

    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary representation of the analysis
        """
        return {
            'ticket_id': self.ticket_id,
            'subject': self.subject,
            'sentiment': self.sentiment,
            'category': self.category,
            'priority': self.priority,
            'hardware_components': self.hardware_components,
            'business_impact': self.business_impact,
            'summary': self.summary,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': self.tags
        }
