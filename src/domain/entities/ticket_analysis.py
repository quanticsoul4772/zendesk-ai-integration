"""
Ticket Analysis Entity

This module defines the TicketAnalysis entity, which represents the result
of analyzing a Zendesk ticket with AI.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class SentimentAnalysis:
    """Represents the sentiment analysis of a ticket's content."""
    polarity: str  # positive, negative, neutral, unknown
    urgency_level: int = 1  # 1-5 scale
    frustration_level: int = 1  # 1-5 scale
    emotions: List[str] = field(default_factory=list)
    business_impact: Dict[str, Any] = field(default_factory=lambda: {
        "detected": False,
        "impact_areas": [],
        "severity": 0
    })


@dataclass
class TicketAnalysis:
    """Represents the analysis of a Zendesk ticket."""
    ticket_id: str
    subject: str
    category: str
    component: str
    priority: str
    sentiment: SentimentAnalysis
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_view_id: Optional[int] = None
    source_view_name: Optional[str] = None
    confidence: float = 0.0
    raw_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    @property
    def priority_score(self) -> int:
        """
        Calculate a priority score based on sentiment and priority.
        
        Returns:
            An integer score from 1-10, with 10 being highest priority
        """
        # Base score from priority
        base_score = {
            "high": 7,
            "medium": 5,
            "low": 3
        }.get(self.priority.lower(), 3)
        
        # Adjust based on sentiment
        sentiment_adjustment = 0
        
        # Adjust based on polarity
        if self.sentiment.polarity == "negative":
            sentiment_adjustment += 1
        elif self.sentiment.polarity == "positive":
            sentiment_adjustment -= 1
            
        # Adjust based on urgency and frustration
        sentiment_adjustment += (self.sentiment.urgency_level - 3) / 2
        sentiment_adjustment += (self.sentiment.frustration_level - 3) / 2
        
        # Adjust based on business impact
        if self.sentiment.business_impact.get("detected", False):
            sentiment_adjustment += self.sentiment.business_impact.get("severity", 0) / 2
            
        # Calculate final score
        score = int(min(10, max(1, base_score + sentiment_adjustment)))
        return score
        
    @property
    def has_business_impact(self) -> bool:
        """
        Check if this ticket has business impact.
        
        Returns:
            Boolean indicating if business impact was detected
        """
        return self.sentiment.business_impact.get("detected", False)
