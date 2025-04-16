"""
Analyze Ticket Use Case

This module provides a use case for analyzing a ticket.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from src.domain.interfaces.service_interfaces import TicketAnalysisService
from src.domain.interfaces.repository_interfaces import TicketRepository, ViewRepository
from src.domain.exceptions import EntityNotFoundError, AIServiceError
from src.domain.entities.analysis import Analysis

from src.application.dtos.ticket_dto import TicketDTO
from src.application.dtos.analysis_dto import AnalysisDTO

# Set up logging
logger = logging.getLogger(__name__)


class AnalyzeTicketUseCase:
    """
    Use case for analyzing a ticket.
    
    This use case coordinates the process of retrieving a ticket and analyzing it.
    """
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        ticket_analysis_service: TicketAnalysisService
    ):
        """
        Initialize the use case.
        
        Args:
            ticket_repository: Repository for ticket data
            ticket_analysis_service: Service for ticket analysis
        """
        self.ticket_repository = ticket_repository
        self.ticket_analysis_service = ticket_analysis_service
    
    def execute(self, ticket_id: int) -> Dict[str, Any]:
        """
        Execute the use case for a single ticket.
        
        Args:
            ticket_id: ID of the ticket to analyze
            
        Returns:
            Dictionary with execution results
            
        Raises:
            EntityNotFoundError: If ticket not found
            AIServiceError: If analysis fails
        """
        logger.info(f"Executing analyze ticket use case for ticket {ticket_id}")
        
        try:
            # Get the ticket from the repository
            ticket = self.ticket_repository.get_ticket(ticket_id)
            
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return {
                    "success": False,
                    "error": f"Ticket {ticket_id} not found",
                    "ticket_id": ticket_id
                }
            
            # Convert to DTO for logging
            ticket_dto = TicketDTO.from_entity(ticket)
            logger.debug(f"Retrieved ticket: {ticket_dto.to_dict()}")
            
            # Analyze the ticket
            analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
            
            # Convert to DTO for response
            analysis_dto = AnalysisDTO.from_entity(analysis)
            
            logger.info(f"Successfully analyzed ticket {ticket_id}")
            
            # Return success result
            return {
                "success": True,
                "ticket_id": ticket_id,
                "analysis": analysis_dto.to_dict()
            }
        except EntityNotFoundError as e:
            logger.error(f"Entity not found: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ticket_id": ticket_id
            }
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}")
            return {
                "success": False,
                "error": f"AI service error: {str(e)}",
                "ticket_id": ticket_id
            }
        except Exception as e:
            logger.exception(f"Unexpected error analyzing ticket {ticket_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "ticket_id": ticket_id
            }
    
    def analyze_ticket(self, 
                      ticket_id: int, 
                      add_comment: bool = False, 
                      add_tags: bool = False) -> AnalysisDTO:
        """
        Analyze a single ticket by ID.
        
        Args:
            ticket_id: ID of the ticket to analyze
            add_comment: Whether to add a comment to the ticket with analysis results
            add_tags: Whether to add tags to the ticket based on analysis
            
        Returns:
            Analysis DTO with results
            
        Raises:
            EntityNotFoundError: If ticket not found
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing ticket {ticket_id} (add_comment={add_comment}, add_tags={add_tags})")
        
        try:
            # Get the ticket
            ticket = self.ticket_repository.get_ticket(ticket_id)
            
            if not ticket:
                raise EntityNotFoundError(f"Ticket {ticket_id} not found")
        except EntityNotFoundError as e:
            # Re-raise with more helpful message
            logger.error(f"Could not find ticket {ticket_id}. Please verify the ID is correct.")
            raise EntityNotFoundError(f"Could not find ticket {ticket_id}. Please verify the ID is correct and belongs to your Zendesk instance.")
        
        # Analyze the ticket
        analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
        
        # Add comment if requested
        if add_comment:
            comment = self._generate_comment_from_analysis(analysis)
            self.ticket_repository.add_ticket_comment(ticket_id, comment, False)
        
        # Add tags if requested
        if add_tags:
            tags = self._generate_tags_from_analysis(analysis)
            self.ticket_repository.add_ticket_tags(ticket_id, tags)
        
        # Convert to DTO
        analysis_dto = AnalysisDTO.from_entity(analysis)
        
        return analysis_dto
    
    def analyze_view(self, 
                    view_id: int, 
                    limit: Optional[int] = None, 
                    add_comment: bool = False, 
                    add_tags: bool = False) -> List[AnalysisDTO]:
        """
        Analyze all tickets in a view.
        
        Args:
            view_id: ID of the view to analyze tickets from
            limit: Maximum number of tickets to analyze
            add_comment: Whether to add comments to tickets with analysis results
            add_tags: Whether to add tags to tickets based on analysis
            
        Returns:
            List of Analysis DTOs with results
            
        Raises:
            EntityNotFoundError: If view not found
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing tickets in view {view_id} (limit={limit}, add_comment={add_comment}, add_tags={add_tags})")
        
        # Get the tickets from the view
        tickets = self.ticket_repository.get_tickets_from_view(view_id, limit)
        
        if not tickets:
            logger.warning(f"No tickets found in view {view_id}")
            return []
        
        logger.info(f"Retrieved {len(tickets)} tickets from view {view_id}")
        
        # Analyze each ticket
        analyses = []
        for ticket in tickets:
            try:
                # Analyze the ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
                
                # Add comment if requested
                if add_comment:
                    comment = self._generate_comment_from_analysis(analysis)
                    self.ticket_repository.add_ticket_comment(ticket.id, comment, False)
                
                # Add tags if requested
                if add_tags:
                    tags = self._generate_tags_from_analysis(analysis)
                    self.ticket_repository.add_ticket_tags(ticket.id, tags)
                
                # Convert to DTO and add to list
                analysis_dto = AnalysisDTO.from_entity(analysis)
                analyses.append(analysis_dto)
                
                logger.info(f"Successfully analyzed ticket {ticket.id} from view {view_id}")
            except Exception as e:
                logger.error(f"Error analyzing ticket {ticket.id} from view {view_id}: {e}")
                # Continue with next ticket
        
        logger.info(f"Completed analysis of {len(analyses)} tickets from view {view_id}")
        
        return analyses
    
    def analyze_view_by_name(self, 
                            view_name: str, 
                            limit: Optional[int] = None, 
                            add_comment: bool = False, 
                            add_tags: bool = False) -> List[AnalysisDTO]:
        """
        Analyze all tickets in a view by name.
        
        Args:
            view_name: Name of the view to analyze tickets from
            limit: Maximum number of tickets to analyze
            add_comment: Whether to add comments to tickets with analysis results
            add_tags: Whether to add tags to tickets based on analysis
            
        Returns:
            List of Analysis DTOs with results
            
        Raises:
            EntityNotFoundError: If view not found
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing tickets in view '{view_name}' (limit={limit}, add_comment={add_comment}, add_tags={add_tags})")
        
        # Get the tickets from the view by name
        tickets = self.ticket_repository.get_tickets_from_view_name(view_name, limit)
        
        if not tickets:
            logger.warning(f"No tickets found in view '{view_name}'")
            return []
        
        logger.info(f"Retrieved {len(tickets)} tickets from view '{view_name}'")
        
        # Analyze each ticket
        analyses = []
        for ticket in tickets:
            try:
                # Analyze the ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
                
                # Add comment if requested
                if add_comment:
                    comment = self._generate_comment_from_analysis(analysis)
                    self.ticket_repository.add_ticket_comment(ticket.id, comment, False)
                
                # Add tags if requested
                if add_tags:
                    tags = self._generate_tags_from_analysis(analysis)
                    self.ticket_repository.add_ticket_tags(ticket.id, tags)
                
                # Convert to DTO and add to list
                analysis_dto = AnalysisDTO.from_entity(analysis)
                analyses.append(analysis_dto)
                
                logger.info(f"Successfully analyzed ticket {ticket.id} from view '{view_name}'")
            except Exception as e:
                logger.error(f"Error analyzing ticket {ticket.id} from view '{view_name}': {e}")
                # Continue with next ticket
        
        logger.info(f"Completed analysis of {len(analyses)} tickets from view '{view_name}'")
        
        return analyses
    
    def analyze_tickets_by_query(self, 
                                query: str, 
                                limit: Optional[int] = None, 
                                add_comment: bool = False, 
                                add_tags: bool = False) -> List[AnalysisDTO]:
        """
        Analyze tickets matching a query.
        
        Args:
            query: Zendesk search query to find tickets
            limit: Maximum number of tickets to analyze
            add_comment: Whether to add comments to tickets with analysis results
            add_tags: Whether to add tags to tickets based on analysis
            
        Returns:
            List of Analysis DTOs with results
            
        Raises:
            AIServiceError: If analysis fails
        """
        logger.info(f"Analyzing tickets matching query '{query}' (limit={limit}, add_comment={add_comment}, add_tags={add_tags})")
        
        # Get tickets matching the query (to be implemented in repository)
        # For now, use a general query method like get_tickets()
        tickets = self.ticket_repository.get_tickets("all", limit)
        
        # Filter tickets based on query (simple implementation)
        # In a real implementation, the query would be passed to the Zendesk API
        filtered_tickets = []
        for ticket in tickets:
            # Simple string matching on subject and description
            query_lower = query.lower()
            if (ticket.subject and query_lower in ticket.subject.lower()) or \
               (ticket.description and query_lower in ticket.description.lower()):
                filtered_tickets.append(ticket)
            
            # Stop if we've reached the limit
            if limit and len(filtered_tickets) >= limit:
                break
        
        if not filtered_tickets:
            logger.warning(f"No tickets found matching query '{query}'")
            return []
        
        logger.info(f"Retrieved {len(filtered_tickets)} tickets matching query '{query}'")
        
        # Analyze each ticket
        analyses = []
        for ticket in filtered_tickets:
            try:
                # Analyze the ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
                
                # Add comment if requested
                if add_comment:
                    comment = self._generate_comment_from_analysis(analysis)
                    self.ticket_repository.add_ticket_comment(ticket.id, comment, False)
                
                # Add tags if requested
                if add_tags:
                    tags = self._generate_tags_from_analysis(analysis)
                    self.ticket_repository.add_ticket_tags(ticket.id, tags)
                
                # Convert to DTO and add to list
                analysis_dto = AnalysisDTO.from_entity(analysis)
                analyses.append(analysis_dto)
                
                logger.info(f"Successfully analyzed ticket {ticket.id} matching query '{query}'")
            except Exception as e:
                logger.error(f"Error analyzing ticket {ticket.id} matching query '{query}': {e}")
                # Continue with next ticket
        
        logger.info(f"Completed analysis of {len(analyses)} tickets matching query '{query}'")
        
        return analyses
    
    def reanalyze_tickets(self, 
                         start_date: datetime, 
                         end_date: datetime,
                         limit: Optional[int] = None, 
                         add_comment: bool = False, 
                         add_tags: bool = False) -> List[AnalysisDTO]:
        """
        Reanalyze tickets that have already been analyzed.
        
        Args:
            start_date: Start date for ticket selection
            end_date: End date for ticket selection
            limit: Maximum number of tickets to analyze
            add_comment: Whether to add comments to tickets with analysis results
            add_tags: Whether to add tags to tickets based on analysis
            
        Returns:
            List of Analysis DTOs with results
            
        Raises:
            AIServiceError: If analysis fails
        """
        logger.info(f"Reanalyzing tickets from {start_date} to {end_date} (limit={limit}, add_comment={add_comment}, add_tags={add_tags})")
        
        # This method would typically get tickets from an analysis repository
        # For now, just get recent tickets from the ticket repository
        tickets = self.ticket_repository.get_tickets("all", limit)
        
        # Filter by date range (assuming tickets have a created_at field)
        filtered_tickets = []
        for ticket in tickets:
            if hasattr(ticket, 'created_at') and ticket.created_at:
                if start_date <= ticket.created_at <= end_date:
                    filtered_tickets.append(ticket)
            
            # Stop if we've reached the limit
            if limit and len(filtered_tickets) >= limit:
                break
        
        if not filtered_tickets:
            logger.warning(f"No tickets found in date range {start_date} to {end_date}")
            return []
        
        logger.info(f"Retrieved {len(filtered_tickets)} tickets for reanalysis")
        
        # Analyze each ticket
        analyses = []
        for ticket in filtered_tickets:
            try:
                # Analyze the ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)
                
                # Add comment if requested
                if add_comment:
                    comment = self._generate_comment_from_analysis(analysis)
                    self.ticket_repository.add_ticket_comment(ticket.id, comment, False)
                
                # Add tags if requested
                if add_tags:
                    tags = self._generate_tags_from_analysis(analysis)
                    self.ticket_repository.add_ticket_tags(ticket.id, tags)
                
                # Convert to DTO and add to list
                analysis_dto = AnalysisDTO.from_entity(analysis)
                analyses.append(analysis_dto)
                
                logger.info(f"Successfully reanalyzed ticket {ticket.id}")
            except Exception as e:
                logger.error(f"Error reanalyzing ticket {ticket.id}: {e}")
                # Continue with next ticket
        
        logger.info(f"Completed reanalysis of {len(analyses)} tickets")
        
        return analyses
    
    def _generate_comment_from_analysis(self, analysis: Analysis) -> str:
        """
        Generate a comment from an analysis.
        
        Args:
            analysis: Analysis entity
            
        Returns:
            Comment text
        """
        comment = "## AI Analysis Results\n\n"
        
        # Add sentiment
        comment += f"**Sentiment**: {analysis.sentiment}\n\n"
        
        # Add category
        comment += f"**Category**: {analysis.category}\n\n"
        
        # Add priority
        comment += f"**Suggested Priority**: {analysis.priority}\n\n"
        
        # Add hardware components if present
        if hasattr(analysis, 'hardware_components') and analysis.hardware_components:
            comment += f"**Hardware Components**: {', '.join(analysis.hardware_components)}\n\n"
        
        # Add business impact if present
        if hasattr(analysis, 'business_impact') and analysis.business_impact:
            comment += f"**Business Impact**: {analysis.business_impact}\n\n"
        
        # Add summary if present
        if hasattr(analysis, 'summary') and analysis.summary:
            comment += f"**Summary**: {analysis.summary}\n\n"
        
        comment += "---\n"
        comment += "This analysis was generated automatically by the AI Integration system."
        
        return comment
    
    def _generate_tags_from_analysis(self, analysis: Analysis) -> List[str]:
        """
        Generate tags from an analysis.
        
        Args:
            analysis: Analysis entity
            
        Returns:
            List of tags
        """
        tags = []
        
        # Add sentiment tag
        tags.append(f"sentiment:{analysis.sentiment.lower()}")
        
        # Add category tag
        tags.append(f"category:{analysis.category.lower().replace(' ', '_')}")
        
        # Add priority tag
        tags.append(f"priority:{analysis.priority.lower()}")
        
        # Add hardware component tags if present
        if hasattr(analysis, 'hardware_components') and analysis.hardware_components:
            for component in analysis.hardware_components:
                tags.append(f"hardware:{component.lower().replace(' ', '_')}")
        
        # Add ai-analyzed tag
        tags.append("ai-analyzed")
        
        return tags
