"""
AI Service Interfaces

This module defines interfaces for AI services used for ticket analysis.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class RateLimitError(AIServiceError):
    """Raised when rate limits are hit."""
    pass


class TokenLimitError(AIServiceError):
    """Raised when token limits are exceeded."""
    pass


class ContentFilterError(AIServiceError):
    """Raised when content violates usage policies."""
    pass


class AIService(ABC):
    """Interface for AI services."""

    @abstractmethod
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to determine sentiment, category, etc.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        pass

    @abstractmethod
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Analyze sentiment of content.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with sentiment analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        pass

    @abstractmethod
    def categorize_ticket(self, content: str) -> Dict[str, Any]:
        """
        Categorize a ticket based on its content.

        Args:
            content: The ticket content to categorize

        Returns:
            Dictionary with categorization results

        Raises:
            AIServiceError: If an error occurs during categorization
        """
        pass


class EnhancedAIService(AIService):
    """Interface for enhanced AI services with additional capabilities."""

    @abstractmethod
    def analyze_business_impact(self, content: str) -> Dict[str, Any]:
        """
        Analyze the business impact of the content.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with business impact analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        pass

    @abstractmethod
    def generate_response_suggestion(self, ticket_content: str) -> str:
        """
        Generate a suggested response for a ticket.

        Args:
            ticket_content: The ticket content

        Returns:
            Suggested response text

        Raises:
            AIServiceError: If an error occurs during generation
        """
        pass

    @abstractmethod
    def extract_ticket_data(self, content: str) -> Dict[str, Any]:
        """
        Extract structured data from ticket content.

        Args:
            content: The ticket content

        Returns:
            Dictionary with extracted data

        Raises:
            AIServiceError: If an error occurs during extraction
        """
        pass
