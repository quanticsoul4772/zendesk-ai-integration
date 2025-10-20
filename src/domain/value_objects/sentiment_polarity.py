"""
Sentiment Polarity Value Object

This module defines the SentimentPolarity value object, which represents the polarity of sentiment analysis.
"""

from enum import Enum


class SentimentPolarity(str, Enum):
    """Represents the polarity of sentiment analysis."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, polarity_str: str) -> 'SentimentPolarity':
        """
        Create a SentimentPolarity from a string.

        Args:
            polarity_str: String representation of the polarity

        Returns:
            SentimentPolarity enum value
        """
        if not polarity_str:
            return cls.UNKNOWN

        normalized = polarity_str.lower().replace("_", " ").strip()

        if normalized in ("positive", "pos", "good"):
            return cls.POSITIVE
        elif normalized in ("negative", "neg", "bad"):
            return cls.NEGATIVE
        elif normalized in ("neutral", "neut"):
            return cls.NEUTRAL
        else:
            return cls.UNKNOWN

    def to_score(self) -> float:
        """
        Convert polarity to a numeric score.

        Returns:
            Numeric score (-1.0 to 1.0, with 1.0 being most positive)
        """
        return {
            self.POSITIVE: 1.0,
            self.NEGATIVE: -1.0,
            self.NEUTRAL: 0.0,
            self.UNKNOWN: 0.0
        }[self]

    @classmethod
    def from_score(cls, score: float) -> 'SentimentPolarity':
        """
        Create a SentimentPolarity from a numeric score.

        Args:
            score: Numeric sentiment score (-1.0 to 1.0)

        Returns:
            SentimentPolarity enum value
        """
        if score >= 0.3:
            return cls.POSITIVE
        elif score <= -0.3:
            return cls.NEGATIVE
        else:
            return cls.NEUTRAL

    def is_positive(self) -> bool:
        """
        Check if the sentiment polarity is positive.

        Returns:
            True if positive, False otherwise
        """
        return self == self.POSITIVE

    def is_negative(self) -> bool:
        """
        Check if the sentiment polarity is negative.

        Returns:
            True if negative, False otherwise
        """
        return self == self.NEGATIVE

    def is_neutral(self) -> bool:
        """
        Check if the sentiment polarity is neutral.

        Returns:
            True if neutral, False otherwise
        """
        return self == self.NEUTRAL
