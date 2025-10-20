"""
Webhook Service

This module provides the implementation of the WebhookService interface.
It is responsible for handling webhook events from Zendesk.
"""

import logging
from typing import Dict, Any, Optional, List

from src.domain.interfaces.repository_interfaces import TicketRepository, AnalysisRepository
from src.domain.interfaces.service_interfaces import WebhookService, TicketAnalysisService
from src.domain.exceptions import EntityNotFoundError, AIServiceError

# Set up logging
logger = logging.getLogger(__name__)


class WebhookServiceImpl(WebhookService):
    """
    Implementation of the WebhookService interface.

    This service handles webhook events from Zendesk and triggers appropriate actions.
    """

    def __init__(
        self,
        ticket_repository: TicketRepository,
        analysis_repository: AnalysisRepository,
        ticket_analysis_service: TicketAnalysisService
    ):
        """
        Initialize the webhook service.

        Args:
            ticket_repository: Repository for ticket data
            analysis_repository: Repository for analysis data
            ticket_analysis_service: Service for ticket analysis
        """
        self.ticket_repository = ticket_repository
        self.analysis_repository = analysis_repository
        self.ticket_analysis_service = ticket_analysis_service
        self.add_comments = False

    def handle_ticket_created(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Handle a ticket created webhook event.

        Args:
            ticket_data: Webhook data for the created ticket

        Returns:
            Success indicator
        """
        logger.info(f"Handling ticket created event: {ticket_data.get('id')}")

        try:
            # Extract ticket ID
            ticket_id = ticket_data.get('id')

            if not ticket_id:
                logger.error("Missing ticket ID in webhook data")
                return False

            # Get the ticket from the repository
            ticket = self.ticket_repository.get_ticket(ticket_id)

            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return False

            # Analyze the ticket
            analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)

            # Add a private comment with the analysis results if enabled
            if self.add_comments:
                comment = self._generate_analysis_comment(analysis)
                self.ticket_repository.add_ticket_comment(ticket_id, comment, public=False)

            # Add tags based on analysis
            tags = self._generate_analysis_tags(analysis)
            self.ticket_repository.add_ticket_tags(ticket_id, tags)

            logger.info(f"Successfully processed ticket created event for ticket {ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error handling ticket created event: {str(e)}")
            return False

    def handle_ticket_updated(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Handle a ticket updated webhook event.

        Args:
            ticket_data: Webhook data for the updated ticket

        Returns:
            Success indicator
        """
        logger.info(f"Handling ticket updated event: {ticket_data.get('id')}")

        try:
            # Extract ticket ID
            ticket_id = ticket_data.get('id')

            if not ticket_id:
                logger.error("Missing ticket ID in webhook data")
                return False

            # Check if we need to reanalyze the ticket
            # For example, if the description or subject has changed
            if self._should_reanalyze_ticket(ticket_data):
                # Get the ticket from the repository
                ticket = self.ticket_repository.get_ticket(ticket_id)

                if not ticket:
                    logger.error(f"Ticket {ticket_id} not found")
                    return False

                # Analyze the ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)

                # Add a private comment with the analysis results if enabled
                if self.add_comments:
                    comment = self._generate_analysis_comment(analysis)
                    self.ticket_repository.add_ticket_comment(ticket_id, comment, public=False)

                # Add tags based on analysis
                tags = self._generate_analysis_tags(analysis)
                self.ticket_repository.add_ticket_tags(ticket_id, tags)

                logger.info(f"Successfully reanalyzed updated ticket {ticket_id}")
            else:
                logger.info(f"No reanalysis needed for ticket {ticket_id}")

            return True
        except Exception as e:
            logger.error(f"Error handling ticket updated event: {str(e)}")
            return False

    def handle_comment_created(self, comment_data: Dict[str, Any]) -> bool:
        """
        Handle a comment created webhook event.

        Args:
            comment_data: Webhook data for the created comment

        Returns:
            Success indicator
        """
        logger.info(f"Handling comment created event for ticket: {comment_data.get('ticket_id')}")

        try:
            # Extract ticket ID and comment data
            ticket_id = comment_data.get('ticket_id')
            comment_text = comment_data.get('body', '')
            is_public = comment_data.get('public', True)
            author_id = comment_data.get('author_id')

            if not ticket_id:
                logger.error("Missing ticket ID in webhook data")
                return False

            # We only care about public comments from end-users
            # The author_id check would need to be customized based on your Zendesk setup
            if is_public and self._is_end_user_comment(author_id):
                # Get the ticket from the repository
                ticket = self.ticket_repository.get_ticket(ticket_id)

                if not ticket:
                    logger.error(f"Ticket {ticket_id} not found")
                    return False

                # Analyze the comment text
                # For now, just reanalyze the whole ticket
                analysis = self.ticket_analysis_service.analyze_ticket_content(ticket)

                # Add a private comment with the analysis results if enabled
                if self.add_comments:
                    response_comment = self._generate_analysis_comment(analysis)
                    self.ticket_repository.add_ticket_comment(ticket_id, response_comment, public=False)

                # Add tags based on analysis
                tags = self._generate_analysis_tags(analysis)
                self.ticket_repository.add_ticket_tags(ticket_id, tags)

                logger.info(f"Successfully processed comment for ticket {ticket_id}")
            else:
                logger.info(f"Skipping non-public or non-end-user comment for ticket {ticket_id}")

            return True
        except Exception as e:
            logger.error(f"Error handling comment created event: {str(e)}")
            return False

    def set_comment_preference(self, add_comments: bool) -> None:
        """
        Set preference for adding comments to tickets.

        Args:
            add_comments: Whether to add comments with analysis results
        """
        self.add_comments = add_comments
        logger.info(f"Set add_comments preference to {add_comments}")

    # Helper methods

    def _generate_analysis_comment(self, analysis) -> str:
        """
        Generate a comment with analysis results.

        Args:
            analysis: Ticket analysis entity

        Returns:
            Comment text
        """
        comment = f"AI Analysis Results:\n\n"
        comment += f"Category: {analysis.category}\n"
        comment += f"Component: {analysis.component}\n"
        comment += f"Priority: {analysis.priority}\n"
        comment += f"Sentiment: {analysis.sentiment.polarity}\n"

        if analysis.sentiment.business_impact.get("detected", False):
            comment += f"\nBusiness Impact Detected!\n"
            impact_areas = analysis.sentiment.business_impact.get("impact_areas", [])
            severity = analysis.sentiment.business_impact.get("severity", 0)
            comment += f"Impact Areas: {', '.join(impact_areas)}\n"
            comment += f"Severity: {severity}/5\n"

        return comment

    def _generate_analysis_tags(self, analysis) -> List[str]:
        """
        Generate tags based on analysis results.

        Args:
            analysis: Ticket analysis entity

        Returns:
            List of tags
        """
        tags = []

        # Add sentiment tag
        tags.append(f"sentiment:{analysis.sentiment.polarity}")

        # Add category tag
        tags.append(f"category:{analysis.category}")

        # Add component tag if not 'none'
        if analysis.component != "none":
            tags.append(f"component:{analysis.component}")

        # Add priority tag
        tags.append(f"ai-priority:{analysis.priority}")

        # Add business impact tag if detected
        if analysis.sentiment.business_impact.get("detected", False):
            tags.append("business-impact")

        # Add high urgency tag if urgency level >= 4
        if analysis.sentiment.urgency_level >= 4:
            tags.append("high-urgency")

        # Add high frustration tag if frustration level >= 4
        if analysis.sentiment.frustration_level >= 4:
            tags.append("high-frustration")

        return tags

    def _should_reanalyze_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Determine if a ticket should be reanalyzed based on webhook data.

        Args:
            ticket_data: Webhook data for the updated ticket

        Returns:
            Whether the ticket should be reanalyzed
        """
        # Check if important fields have changed
        changes = ticket_data.get('changes', {})

        important_fields = ['subject', 'description', 'comment']

        for field in important_fields:
            if field in changes:
                return True

        return False

    def _is_end_user_comment(self, author_id: Optional[int]) -> bool:
        """
        Determine if a comment was made by an end-user.

        Args:
            author_id: ID of the comment author

        Returns:
            Whether the comment was made by an end-user
        """
        # This is a simplified check - in a real implementation,
        # you would check against known agent/admin IDs or user roles
        # For now, we'll assume any author with an ID is an end-user
        return author_id is not None
