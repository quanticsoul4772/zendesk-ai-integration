"""
Analysis DTO

This module defines the AnalysisDTO (Data Transfer Object) for transferring ticket analysis data
between layers of the application.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket_analysis import TicketAnalysis, SentimentAnalysis


class SentimentAnalysisDTO:
    """Data Transfer Object for SentimentAnalysis value object."""

    def __init__(self, polarity: str, urgency_level: int = 1, frustration_level: int = 1,
                emotions: List[str] = None, business_impact: Dict[str, Any] = None):
        self.polarity = polarity
        self.urgency_level = urgency_level
        self.frustration_level = frustration_level
        self.emotions = emotions or []
        self.business_impact = business_impact or {
            "detected": False,
            "impact_areas": [],
            "severity": 0
        }

    def __hash__(self):
        # Make this object hashable so it can be used as a dictionary key
        return hash(self.polarity)

    def __eq__(self, other):
        # For comparison, just check if the polarity is the same
        if isinstance(other, SentimentAnalysisDTO):
            return self.polarity == other.polarity
        # Allow comparing with strings directly
        elif isinstance(other, str):
            return self.polarity == other
        return False

    def __str__(self):
        # String representation is the polarity
        return self.polarity

    @classmethod
    def from_entity(cls, entity: SentimentAnalysis) -> 'SentimentAnalysisDTO':
        """
        Create a SentimentAnalysisDTO from a SentimentAnalysis entity.

        Args:
            entity: SentimentAnalysis entity

        Returns:
            SentimentAnalysisDTO instance
        """
        return cls(
            polarity=entity.polarity,
            urgency_level=entity.urgency_level,
            frustration_level=entity.frustration_level,
            emotions=entity.emotions.copy() if entity.emotions else [],
            business_impact=entity.business_impact.copy() if entity.business_impact else {"detected": False}
        )

    def to_entity(self) -> SentimentAnalysis:
        """
        Convert to a SentimentAnalysis entity.

        Returns:
            SentimentAnalysis entity
        """
        return SentimentAnalysis(
            polarity=self.polarity,
            urgency_level=self.urgency_level,
            frustration_level=self.frustration_level,
            emotions=self.emotions.copy() if self.emotions else [],
            business_impact=self.business_impact.copy() if self.business_impact else {"detected": False}
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "polarity": self.polarity,
            "urgency_level": self.urgency_level,
            "frustration_level": self.frustration_level,
            "emotions": self.emotions.copy() if self.emotions else [],
            "business_impact": self.business_impact.copy() if self.business_impact else {"detected": False}
        }


@dataclass
class AnalysisDTO:
    """Data Transfer Object for TicketAnalysis entity."""

    ticket_id: str
    subject: str
    category: str
    component: str
    priority: str
    sentiment: SentimentAnalysisDTO
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_view_id: Optional[int] = None
    source_view_name: Optional[str] = None
    confidence: float = 0.0
    raw_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    priority_score: int = 0

    @classmethod
    def from_entity(cls, entity: TicketAnalysis) -> 'AnalysisDTO':
        """
        Create an AnalysisDTO from a TicketAnalysis entity.

        Args:
            entity: TicketAnalysis entity

        Returns:
            AnalysisDTO instance
        """
        sentiment_dto = SentimentAnalysisDTO.from_entity(entity.sentiment)

        return cls(
            ticket_id=entity.ticket_id,
            subject=entity.subject,
            category=entity.category,
            component=entity.component,
            priority=entity.priority,
            sentiment=sentiment_dto,
            timestamp=entity.timestamp,
            source_view_id=entity.source_view_id,
            source_view_name=entity.source_view_name,
            confidence=entity.confidence,
            raw_result=entity.raw_result.copy() if entity.raw_result else None,
            error=entity.error,
            error_type=entity.error_type,
            priority_score=entity.priority_score
        )

    def to_entity(self) -> TicketAnalysis:
        """
        Convert to a TicketAnalysis entity.

        Returns:
            TicketAnalysis entity
        """
        sentiment = self.sentiment.to_entity()

        return TicketAnalysis(
            ticket_id=self.ticket_id,
            subject=self.subject,
            category=self.category,
            component=self.component,
            priority=self.priority,
            sentiment=sentiment,
            timestamp=self.timestamp,
            source_view_id=self.source_view_id,
            source_view_name=self.source_view_name,
            confidence=self.confidence,
            raw_result=self.raw_result.copy() if self.raw_result else None,
            error=self.error,
            error_type=self.error_type
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary.

        Returns:
            Dictionary representation
        """
        # Convert to dict using dataclasses.asdict
        result = asdict(self)

        # Handle SentimentAnalysisDTO
        result['sentiment'] = self.sentiment.to_dict()

        # Handle datetime objects
        result['timestamp'] = self.timestamp.isoformat() if self.timestamp else None

        return result
