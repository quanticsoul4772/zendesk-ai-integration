"""
AI Analyzer Adapter

This module provides an adapter that presents an AIAnalyzer interface
but uses the new AIService implementations internally.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from src.domain.interfaces.ai_service_interfaces import AIService
from src.infrastructure.external_services.claude_service import ClaudeService
from src.infrastructure.external_services.openai_service import OpenAIService
from src.application.services.ticket_analysis_service import TicketAnalysisService

# Set up logging
logger = logging.getLogger(__name__)


class AIAnalyzerAdapter:
    """
    Adapter that presents an AIAnalyzer interface but uses AIService implementations internally.
    
    This adapter helps with the transition from the legacy AIAnalyzer to the
    new AIService implementations.
    """
    
    def __init__(self, ticket_analysis_service=None, claude_service=None, openai_service=None):
        """
        Initialize the adapter.
        
        Args:
            ticket_analysis_service: Optional TicketAnalysisService instance
            claude_service: Optional ClaudeService instance
            openai_service: Optional OpenAIService instance
        """
        self._claude_service = claude_service or ClaudeService()
        self._openai_service = openai_service or OpenAIService()
        self._ticket_analysis_service = ticket_analysis_service or TicketAnalysisService(
            ai_service=self._openai_service
        )
        
        # For backward compatibility, expose the batch processor attribute
        # that legacy code might expect
        self.batch_processor = self._ticket_analysis_service.batch_processor
        
        logger.debug("AIAnalyzerAdapter initialized - using AIService implementations internally")
    
    def analyze_ticket(self, ticket, use_claude=False):
        """
        Analyze a single ticket.
        
        Args:
            ticket: The ticket to analyze
            use_claude: Whether to use Claude instead of OpenAI
            
        Returns:
            Analysis result
        """
        logger.debug(f"AIAnalyzerAdapter.analyze_ticket called for ticket {ticket.id}, use_claude={use_claude}")
        
        if use_claude:
            self._ticket_analysis_service.ai_service = self._claude_service
        else:
            self._ticket_analysis_service.ai_service = self._openai_service
        
        return self._ticket_analysis_service.analyze_ticket(ticket)
    
    def analyze_tickets_batch(self, tickets, use_claude=False):
        """
        Analyze a batch of tickets.
        
        Args:
            tickets: List of tickets to analyze
            use_claude: Whether to use Claude instead of OpenAI
            
        Returns:
            List of analysis results
        """
        logger.debug(f"AIAnalyzerAdapter.analyze_tickets_batch called with {len(tickets)} tickets, use_claude={use_claude}")
        
        if use_claude:
            self._ticket_analysis_service.ai_service = self._claude_service
        else:
            self._ticket_analysis_service.ai_service = self._openai_service
        
        return self._ticket_analysis_service.analyze_tickets_batch(tickets)
    
    def get_sentiment(self, text):
        """
        Get sentiment analysis for text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result
        """
        logger.debug("AIAnalyzerAdapter.get_sentiment called")
        
        # Use OpenAI by default for sentiment
        self._ticket_analysis_service.ai_service = self._openai_service
        
        return self._ticket_analysis_service.get_sentiment(text)
    
    def get_enhanced_sentiment(self, text):
        """
        Get enhanced sentiment analysis for text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Enhanced sentiment analysis result
        """
        logger.debug("AIAnalyzerAdapter.get_enhanced_sentiment called")
        
        # Use Claude for enhanced sentiment
        self._ticket_analysis_service.ai_service = self._claude_service
        
        return self._ticket_analysis_service.get_enhanced_sentiment(text)
    
    def extract_hardware_components(self, text):
        """
        Extract hardware components from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of hardware components
        """
        logger.debug("AIAnalyzerAdapter.extract_hardware_components called")
        
        return self._ticket_analysis_service.extract_hardware_components(text)
    
    def categorize_ticket(self, ticket):
        """
        Categorize a ticket.
        
        Args:
            ticket: The ticket to categorize
            
        Returns:
            Category information
        """
        logger.debug(f"AIAnalyzerAdapter.categorize_ticket called for ticket {ticket.id}")
        
        return self._ticket_analysis_service.categorize_ticket(ticket)
