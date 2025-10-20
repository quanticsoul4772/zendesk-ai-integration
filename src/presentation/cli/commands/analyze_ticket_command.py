"""
Analyze Ticket Command

This module defines the AnalyzeTicketCommand class for analyzing tickets.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class AnalyzeTicketCommand(Command):
    """Command for analyzing tickets."""

    @property
    def description(self) -> str:
        """Get the command description."""
        return "Analyze tickets using AI and return analysis results"

    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        # Add ticket ID as positional argument (optional)
        parser.add_argument(
            "ticket_id",
            nargs="?",
            type=int,
            help="ID of the ticket to analyze"
        )

        # Add options for what to do with analysis results
        parser.add_argument(
            "--add-comment",
            action="store_true",
            help="Add the analysis as a private comment to the ticket"
        )

        parser.add_argument(
            "--add-tags",
            action="store_true",
            help="Add tags based on the analysis to the ticket"
        )

        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )

        # Add options for finding tickets to analyze
        parser.add_argument(
            "--ticket-query",
            help="Zendesk search query to find tickets to analyze"
        )

        parser.add_argument(
            "--view-id",
            type=int,
            help="ID of the view to analyze tickets from"
        )

        parser.add_argument(
            "--view-name",
            help="Name of the view to analyze tickets from"
        )

        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days back to analyze tickets (default: 7)"
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of tickets to analyze"
        )

        # Add flags for controlling analysis behavior
        parser.add_argument(
            "--reanalyze",
            action="store_true",
            help="Reanalyze tickets that have already been analyzed"
        )

        parser.add_argument(
            "--use-openai",
            action="store_true",
            help="Use OpenAI instead of Claude for analysis (default is Claude)"
        )

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing analyze command with args: {args}")

        # Get required services and use cases
        try:
            from src.application.use_cases.analyze_ticket_use_case import (
                AnalyzeTicketUseCase,
            )
            analyze_ticket_use_case = self.dependency_container.resolve("analyze_ticket_use_case")
        except KeyError:
            logger.error("Could not resolve analyze_ticket_use_case, trying by class name")
            # Try to get it by class name
            analyze_ticket_use_case = self.dependency_container.resolve(AnalyzeTicketUseCase)

        # Configure AI service based on arguments
        self._configure_ai_service(args)

        # Determine what to analyze
        if args.get("ticket_id"):
            # Analyze a specific ticket
            return self._analyze_specific_ticket(args, analyze_ticket_use_case)
        elif args.get("view_id"):
            # Analyze all tickets in a view by ID
            return self._analyze_view(args, analyze_ticket_use_case)
        elif args.get("view_name"):
            # Analyze all tickets in a view by name
            return self._analyze_view_by_name(args, analyze_ticket_use_case)
        elif args.get("ticket_query"):
            # Analyze tickets matching a query
            return self._analyze_tickets_by_query(args, analyze_ticket_use_case)
        elif args.get("reanalyze"):
            # Reanalyze existing analyses
            return self._reanalyze_tickets(args, analyze_ticket_use_case)
        else:
            # No target specified
            logger.error("No tickets specified for analysis")
            print("Error: You must specify tickets to analyze using one of:")
            print("  - A specific ticket ID")
            print("  - A view ID (--view-id)")
            print("  - A view name (--view-name)")
            print("  - A ticket query (--ticket-query)")
            print("  - The reanalyze flag (--reanalyze)")
            return {"success": False, "error": "No tickets specified for analysis"}

    def _configure_ai_service(self, args: Dict[str, Any]) -> None:
        """
        Configure which AI service to use.

        Args:
            args: Command-line arguments
        """
        # By default, use Claude unless OpenAI is explicitly requested
        use_openai = args.get("use_openai", False)

        try:
            # Get the required services using their interface types
            from src.domain.interfaces.ai_service_interfaces import AIService
            from src.domain.interfaces.service_interfaces import TicketAnalysisService

            ticket_analysis_service = self.dependency_container.resolve(TicketAnalysisService)

            if use_openai:
                # Use OpenAI
                openai_service = self.dependency_container.resolve(AIService, "openai")
                ticket_analysis_service.ai_service = openai_service
                logger.info("Using OpenAI for analysis")
            else:
                # Use Claude (default)
                claude_service = self.dependency_container.resolve(AIService, "claude")
                ticket_analysis_service.ai_service = claude_service
                logger.info("Using Claude for analysis")
        except Exception as e:
            logger.error(f"Error configuring AI service: {e}")
            raise

    def _validate_ticket_id(self, ticket_id: int) -> bool:
        """
        Validate if a ticket ID appears to be in the correct format.

        Args:
            ticket_id: ID to validate

        Returns:
            True if ID format is valid, False otherwise
        """
        # Basic validation - Zendesk ticket IDs are typically integers
        # and usually not more than 10 digits
        str_id = str(ticket_id)
        if not str_id.isdigit():
            return False

        # Most Zendesk ticket IDs are within a reasonable length range
        # This is a heuristic and might need adjustment based on your instance
        if len(str_id) > 12:
            logger.warning(f"Ticket ID {ticket_id} is unusually long")

        return True

    def _analyze_specific_ticket(self, args: Dict[str, Any], analyze_ticket_use_case) -> Dict[str, Any]:
        """
        Analyze a specific ticket.

        Args:
            args: Command-line arguments
            analyze_ticket_use_case: Use case for analyzing tickets

        Returns:
            Analysis results
        """
        ticket_id = args.get("ticket_id")
        add_comment = args.get("add_comment", False)
        add_tags = args.get("add_tags", False)
        output_format = args.get("format", "text")

        # Validate ticket ID format
        if not self._validate_ticket_id(ticket_id):
            error_msg = f"Invalid ticket ID format: {ticket_id}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return {"success": False, "error": error_msg, "ticket_id": ticket_id}

        logger.info(f"Analyzing ticket {ticket_id}")

        try:
            # Execute the use case
            analysis = analyze_ticket_use_case.analyze_ticket(
                ticket_id=ticket_id,
                add_comment=add_comment,
                add_tags=add_tags
            )

            # Format and display results
            if output_format == "json":
                import json
                result_json = json.dumps(analysis.to_dict(), indent=2)
                print(result_json)
            else:
                # Text format (default)
                print(f"Analysis completed for ticket {ticket_id}")
                print(f"Subject: {analysis.subject}")
                print(f"Sentiment: {analysis.sentiment}")
                print(f"Category: {analysis.category}")
                print(f"Priority: {analysis.priority}")

                # Check for the component information and display it properly
                if hasattr(analysis, 'component') and analysis.component:
                    print(f"Component: {analysis.component}")

                if hasattr(analysis, 'business_impact') and analysis.business_impact:
                    print(f"Business impact: {analysis.business_impact}")

                if add_comment:
                    print(f"Added comment to ticket: Yes")

                if add_tags:
                    print(f"Added tags to ticket: {', '.join(analysis.tags) if hasattr(analysis, 'tags') and analysis.tags else 'None'}")

            return {
                "success": True,
                "ticket_id": ticket_id,
                "analysis": analysis.to_dict(),
                "add_comment": add_comment,
                "add_tags": add_tags
            }

        except Exception as e:
            logger.exception(f"Error analyzing ticket {ticket_id}: {e}")
            print(f"Error analyzing ticket {ticket_id}: {e}")
            return {"success": False, "error": str(e), "ticket_id": ticket_id}

    def _analyze_view(self, args: Dict[str, Any], analyze_ticket_use_case) -> Dict[str, Any]:
        """
        Analyze all tickets in a view.

        Args:
            args: Command-line arguments
            analyze_ticket_use_case: Use case for analyzing tickets

        Returns:
            Analysis results
        """
        view_id = args.get("view_id")
        limit = args.get("limit")
        add_comment = args.get("add_comment", False)
        add_tags = args.get("add_tags", False)
        output_format = args.get("format", "text")

        logger.info(f"Analyzing tickets in view {view_id} (limit: {limit})")

        try:
            # Execute the use case
            analyses = analyze_ticket_use_case.analyze_view(
                view_id=view_id,
                limit=limit,
                add_comment=add_comment,
                add_tags=add_tags
            )

            # Format and display results
            if output_format == "json":
                import json
                result_json = json.dumps([a.to_dict() for a in analyses], indent=2)
                print(result_json)
            else:
                # Text format (default)
                print(f"Analyzed {len(analyses)} tickets in view {view_id}")

                # Print distribution of sentiments
                sentiment_counts = {}
                for analysis in analyses:
                    sentiment = analysis.sentiment
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

                print("\nSentiment distribution:")
                for sentiment, count in sentiment_counts.items():
                    print(f"  {sentiment}: {count}")

                # Print distribution of categories
                category_counts = {}
                for analysis in analyses:
                    category = analysis.category
                    category_counts[category] = category_counts.get(category, 0) + 1

                print("\nCategory distribution:")
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category}: {count}")

                # Print distribution of priorities
                priority_counts = {}
                for analysis in analyses:
                    priority = analysis.priority
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                print("\nPriority distribution:")
                for priority, count in sorted(priority_counts.items(), key=lambda x: x[0], reverse=True):
                    print(f"  {priority}: {count}")

                if add_comment:
                    print(f"\nAdded comments to tickets: Yes")

                if add_tags:
                    print(f"\nAdded tags to tickets: Yes")

            return {
                "success": True,
                "view_id": view_id,
                "analyses_count": len(analyses),
                "sentiment_distribution": sentiment_counts,
                "add_comment": add_comment,
                "add_tags": add_tags
            }

        except Exception as e:
            logger.exception(f"Error analyzing view {view_id}: {e}")
            print(f"Error analyzing view {view_id}: {e}")
            return {"success": False, "error": str(e), "view_id": view_id}

    def _analyze_view_by_name(self, args: Dict[str, Any], analyze_ticket_use_case) -> Dict[str, Any]:
        """
        Analyze all tickets in a view by name.

        Args:
            args: Command-line arguments
            analyze_ticket_use_case: Use case for analyzing tickets

        Returns:
            Analysis results
        """
        view_name = args.get("view_name")
        limit = args.get("limit")
        add_comment = args.get("add_comment", False)
        add_tags = args.get("add_tags", False)
        output_format = args.get("format", "text")

        logger.info(f"Analyzing tickets in view '{view_name}' (limit: {limit})")

        try:
            # Execute the use case
            analyses = analyze_ticket_use_case.analyze_view_by_name(
                view_name=view_name,
                limit=limit,
                add_comment=add_comment,
                add_tags=add_tags
            )

            # Format and display results
            if output_format == "json":
                import json
                result_json = json.dumps([a.to_dict() for a in analyses], indent=2)
                print(result_json)
            else:
                # Text format (default)
                print(f"Analyzed {len(analyses)} tickets in view '{view_name}'")

                # Print distribution of sentiments
                sentiment_counts = {}
                for analysis in analyses:
                    sentiment = analysis.sentiment
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

                print("\nSentiment distribution:")
                for sentiment, count in sentiment_counts.items():
                    print(f"  {sentiment}: {count}")

                # Print distribution of categories
                category_counts = {}
                for analysis in analyses:
                    category = analysis.category
                    category_counts[category] = category_counts.get(category, 0) + 1

                print("\nCategory distribution:")
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category}: {count}")

                # Print distribution of priorities
                priority_counts = {}
                for analysis in analyses:
                    priority = analysis.priority
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                print("\nPriority distribution:")
                for priority, count in sorted(priority_counts.items(), key=lambda x: x[0], reverse=True):
                    print(f"  {priority}: {count}")

                if add_comment:
                    print(f"\nAdded comments to tickets: Yes")

                if add_tags:
                    print(f"\nAdded tags to tickets: Yes")

            return {
                "success": True,
                "view_name": view_name,
                "analyses_count": len(analyses),
                "sentiment_distribution": sentiment_counts,
                "add_comment": add_comment,
                "add_tags": add_tags
            }

        except Exception as e:
            logger.exception(f"Error analyzing view '{view_name}': {e}")
            print(f"Error analyzing view '{view_name}': {e}")
            return {"success": False, "error": str(e), "view_name": view_name}

    def _analyze_tickets_by_query(self, args: Dict[str, Any], analyze_ticket_use_case) -> Dict[str, Any]:
        """
        Analyze tickets matching a query.

        Args:
            args: Command-line arguments
            analyze_ticket_use_case: Use case for analyzing tickets

        Returns:
            Analysis results
        """
        ticket_query = args.get("ticket_query")
        limit = args.get("limit")
        add_comment = args.get("add_comment", False)
        add_tags = args.get("add_tags", False)
        output_format = args.get("format", "text")

        logger.info(f"Analyzing tickets matching query '{ticket_query}' (limit: {limit})")

        try:
            # Execute the use case
            analyses = analyze_ticket_use_case.analyze_tickets_by_query(
                query=ticket_query,
                limit=limit,
                add_comment=add_comment,
                add_tags=add_tags
            )

            # Format and display results
            if output_format == "json":
                import json
                result_json = json.dumps([a.to_dict() for a in analyses], indent=2)
                print(result_json)
            else:
                # Text format (default)
                print(f"Analyzed {len(analyses)} tickets matching query '{ticket_query}'")

                # Print distribution of sentiments
                sentiment_counts = {}
                for analysis in analyses:
                    sentiment = analysis.sentiment
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

                print("\nSentiment distribution:")
                for sentiment, count in sentiment_counts.items():
                    print(f"  {sentiment}: {count}")

                # Print distribution of categories
                category_counts = {}
                for analysis in analyses:
                    category = analysis.category
                    category_counts[category] = category_counts.get(category, 0) + 1

                print("\nCategory distribution:")
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category}: {count}")

                # Print distribution of priorities
                priority_counts = {}
                for analysis in analyses:
                    priority = analysis.priority
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                print("\nPriority distribution:")
                for priority, count in sorted(priority_counts.items(), key=lambda x: x[0], reverse=True):
                    print(f"  {priority}: {count}")

                if add_comment:
                    print(f"\nAdded comments to tickets: Yes")

                if add_tags:
                    print(f"\nAdded tags to tickets: Yes")

            return {
                "success": True,
                "ticket_query": ticket_query,
                "analyses_count": len(analyses),
                "sentiment_distribution": sentiment_counts,
                "add_comment": add_comment,
                "add_tags": add_tags
            }

        except Exception as e:
            logger.exception(f"Error analyzing tickets matching query '{ticket_query}': {e}")
            print(f"Error analyzing tickets matching query '{ticket_query}': {e}")
            return {"success": False, "error": str(e), "ticket_query": ticket_query}

    def _reanalyze_tickets(self, args: Dict[str, Any], analyze_ticket_use_case) -> Dict[str, Any]:
        """
        Reanalyze existing analyses.

        Args:
            args: Command-line arguments
            analyze_ticket_use_case: Use case for analyzing tickets

        Returns:
            Analysis results
        """
        days = args.get("days", 7)
        limit = args.get("limit")
        add_comment = args.get("add_comment", False)
        add_tags = args.get("add_tags", False)
        output_format = args.get("format", "text")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Reanalyzing tickets from the last {days} days (limit: {limit})")

        try:
            # Execute the use case
            analyses = analyze_ticket_use_case.reanalyze_tickets(
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                add_comment=add_comment,
                add_tags=add_tags
            )

            # Format and display results
            if output_format == "json":
                import json
                result_json = json.dumps([a.to_dict() for a in analyses], indent=2)
                print(result_json)
            else:
                # Text format (default)
                print(f"Reanalyzed {len(analyses)} tickets from the last {days} days")

                # Print distribution of sentiments
                sentiment_counts = {}
                for analysis in analyses:
                    sentiment = analysis.sentiment
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

                print("\nSentiment distribution:")
                for sentiment, count in sentiment_counts.items():
                    print(f"  {sentiment}: {count}")

                # Print distribution of categories
                category_counts = {}
                for analysis in analyses:
                    category = analysis.category
                    category_counts[category] = category_counts.get(category, 0) + 1

                print("\nCategory distribution:")
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category}: {count}")

                # Print distribution of priorities
                priority_counts = {}
                for analysis in analyses:
                    priority = analysis.priority
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                print("\nPriority distribution:")
                for priority, count in sorted(priority_counts.items(), key=lambda x: x[0], reverse=True):
                    print(f"  {priority}: {count}")

                if add_comment:
                    print(f"\nAdded comments to tickets: Yes")

                if add_tags:
                    print(f"\nAdded tags to tickets: Yes")

            return {
                "success": True,
                "days": days,
                "analyses_count": len(analyses),
                "sentiment_distribution": sentiment_counts,
                "add_comment": add_comment,
                "add_tags": add_tags
            }

        except Exception as e:
            logger.exception(f"Error reanalyzing tickets: {e}")
            print(f"Error reanalyzing tickets: {e}")
            return {"success": False, "error": str(e), "days": days}
