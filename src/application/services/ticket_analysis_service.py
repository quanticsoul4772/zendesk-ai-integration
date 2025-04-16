"""
Ticket Analysis Service

This module provides the implementation of the TicketAnalysisService interface.
It orchestrates the analysis of tickets using the repository and AI service.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis, SentimentAnalysis
from src.domain.interfaces.repository_interfaces import TicketRepository, AnalysisRepository
from src.domain.interfaces.ai_service_interfaces import AIService, AIServiceError
from src.domain.interfaces.service_interfaces import TicketAnalysisService
from src.domain.exceptions import EntityNotFoundError, AIServiceError

# Set up logging
logger = logging.getLogger(__name__)


class TicketAnalysisServiceImpl(TicketAnalysisService):
    """
    Implementation of the TicketAnalysisService interface.
    
    This service orchestrates the analysis of tickets using the repository and AI service.
    """
    
    def __init__(
        self, 
        ticket_repository: TicketRepository,
        analysis_repository: AnalysisRepository,
        ai_service: AIService
    ):
        """
        Initialize the ticket analysis service.
        
        Args:
            ticket_repository: Repository for ticket data
            analysis_repository: Repository for analysis data
            ai_service: AI service for content analysis
        """
        self.ticket_repository = ticket_repository
        self.analysis_repository = analysis_repository
        self.ai_service = ai_service
    
    def analyze_ticket(self, ticket_id: int) -> TicketAnalysis:
        """
        Analyze a ticket by ID.
        
        Args:
            ticket_id: ID of the ticket to analyze
            
        Returns:
            Ticket analysis entity
            
        Raises:
            EntityNotFoundError: If ticket not found
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing ticket {ticket_id}")
        
        # Get the ticket
        ticket = self.ticket_repository.get_ticket(ticket_id)
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            raise EntityNotFoundError(f"Ticket {ticket_id} not found")
        
        # Analyze the ticket
        return self.analyze_ticket_content(ticket)
    
    def analyze_ticket_content(self, ticket: Ticket) -> TicketAnalysis:
        """
        Analyze a ticket's content.
        
        Args:
            ticket: Ticket entity to analyze
            
        Returns:
            Ticket analysis entity
            
        Raises:
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing content for ticket {ticket.id}")
        
        # Combine subject and description for analysis
        content = f"Subject: {ticket.subject}\n\nDescription: {ticket.description}"
        
        try:
            # Use the AI service to analyze the content
            analysis_result = self.ai_service.analyze_content(content)
            
            # Extract sentiment data
            sentiment_data = analysis_result.get("sentiment", {})
            sentiment = SentimentAnalysis(
                polarity=sentiment_data.get("polarity", "unknown"),
                urgency_level=sentiment_data.get("urgency_level", 1),
                frustration_level=sentiment_data.get("frustration_level", 1),
                emotions=sentiment_data.get("emotions", []),
                business_impact=sentiment_data.get("business_impact", {"detected": False})
            )
            
            # Create the analysis entity
            analysis = TicketAnalysis(
                ticket_id=str(ticket.id),
                subject=ticket.subject,
                category=analysis_result.get("category", "uncategorized"),
                component=analysis_result.get("component", "none"),
                priority=analysis_result.get("priority", "low"),
                sentiment=sentiment,
                timestamp=datetime.utcnow(),
                source_view_id=ticket.source_view_id,
                source_view_name=ticket.source_view_name,
                confidence=analysis_result.get("confidence", 0.0),
                raw_result=analysis_result
            )
            
            # Save the analysis to the repository
            self.analysis_repository.save(analysis)
            
            logger.info(f"Successfully analyzed ticket {ticket.id}")
            
            return analysis
        except AIServiceError as e:
            logger.error(f"AI service error analyzing ticket {ticket.id}: {str(e)}")
            
            # Create an analysis entity with error information
            sentiment = SentimentAnalysis(
                polarity="unknown",
                urgency_level=1,
                frustration_level=1,
                emotions=[],
                business_impact={"detected": False}
            )
            
            analysis = TicketAnalysis(
                ticket_id=str(ticket.id),
                subject=ticket.subject,
                category="uncategorized",
                component="none",
                priority="low",
                sentiment=sentiment,
                timestamp=datetime.utcnow(),
                source_view_id=ticket.source_view_id,
                source_view_name=ticket.source_view_name,
                confidence=0.0,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Still save the failed analysis for tracking
            self.analysis_repository.save(analysis)
            
            # Re-raise the exception
            raise
    
    def analyze_batch(self, ticket_ids: List[int]) -> List[TicketAnalysis]:
        """
        Analyze multiple tickets by ID.
        
        Args:
            ticket_ids: List of ticket IDs to analyze
            
        Returns:
            List of ticket analysis entities
        """
        logger.info(f"Analyzing batch of {len(ticket_ids)} tickets")
        
        analyses = []
        
        for ticket_id in ticket_ids:
            try:
                analysis = self.analyze_ticket(ticket_id)
                analyses.append(analysis)
            except EntityNotFoundError:
                logger.warning(f"Skipping ticket {ticket_id} - not found")
            except AIServiceError as e:
                logger.error(f"Error analyzing ticket {ticket_id}: {str(e)}")
                # Continue with the next ticket
        
        logger.info(f"Successfully analyzed {len(analyses)} tickets in batch")
        
        return analyses
    
    def analyze_view(self, view_id: int, limit: Optional[int] = None) -> List[TicketAnalysis]:
        """
        Analyze tickets from a view.
        
        Args:
            view_id: ID of the view
            limit: Maximum number of tickets to analyze
            
        Returns:
            List of ticket analysis entities
        """
        logger.info(f"Analyzing tickets from view {view_id}")
        
        # Get tickets from the view
        tickets = self.ticket_repository.get_tickets_from_view(view_id, limit)
        
        logger.info(f"Found {len(tickets)} tickets in view {view_id}")
        
        analyses = []
        
        for ticket in tickets:
            try:
                analysis = self.analyze_ticket_content(ticket)
                analyses.append(analysis)
            except AIServiceError as e:
                logger.error(f"Error analyzing ticket {ticket.id}: {str(e)}")
                # Continue with the next ticket
        
        logger.info(f"Successfully analyzed {len(analyses)} tickets from view {view_id}")
        
        return analyses
    
    def get_analysis_history(self, ticket_id: int) -> List[TicketAnalysis]:
        """
        Get analysis history for a ticket.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            List of ticket analysis entities in chronological order
        """
        logger.info(f"Getting analysis history for ticket {ticket_id}")
        
        # Implement this when we have a way to get analysis history from the repository
        # For now, just return the latest analysis
        latest_analysis = self.analysis_repository.get_by_ticket_id(str(ticket_id))
        
        return [latest_analysis] if latest_analysis else []
    
    def get_sentiment_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get sentiment statistics for a time period.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            Dictionary with sentiment statistics
        """
        logger.info(f"Getting sentiment statistics from {start_date} to {end_date}")
        
        # Get all analyses in the time period
        analyses = self.analysis_repository.find_between_dates(start_date, end_date)
        
        if not analyses:
            return {
                "count": 0,
                "time_period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        
        # Count sentiment polarities
        polarity_counts = {"positive": 0, "negative": 0, "neutral": 0, "unknown": 0}
        urgency_levels = []
        frustration_levels = []
        priority_scores = []
        business_impact_count = 0
        
        for analysis in analyses:
            # Process sentiment polarity
            polarity = analysis.sentiment.polarity
            polarity_counts[polarity] = polarity_counts.get(polarity, 0) + 1
            
            # Collect metrics for averaging
            urgency_levels.append(analysis.sentiment.urgency_level)
            frustration_levels.append(analysis.sentiment.frustration_level)
            
            # Check for business impact
            if analysis.sentiment.business_impact.get("detected", False):
                business_impact_count += 1
            
            # Get priority score
            priority_scores.append(analysis.priority_score)
        
        # Calculate averages
        avg_urgency = sum(urgency_levels) / len(urgency_levels) if urgency_levels else 0
        avg_frustration = sum(frustration_levels) / len(frustration_levels) if frustration_levels else 0
        avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 0
        
        # Create statistics result
        return {
            "count": len(analyses),
            "time_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "sentiment_distribution": polarity_counts,
            "average_urgency": avg_urgency,
            "average_frustration": avg_frustration,
            "average_priority": avg_priority,
            "business_impact_count": business_impact_count,
            "business_impact_percentage": (business_impact_count / len(analyses)) * 100 if analyses else 0
        }
