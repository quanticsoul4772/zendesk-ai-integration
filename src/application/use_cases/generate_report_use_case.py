"""
Generate Report Use Case

This module provides a use case for generating reports.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.application.dtos.report_dto import ReportDTO
from src.domain.exceptions import EntityNotFoundError
from src.domain.interfaces.service_interfaces import ReportingService

# Set up logging
logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """
    Use case for generating reports.

    This use case coordinates the process of generating various reports.
    """

    def __init__(self, reporting_service: ReportingService):
        """
        Initialize the use case.

        Args:
            reporting_service: Service for generating reports
        """
        self.reporting_service = reporting_service

    def execute(
        self,
        report_type: str,
        time_period: Optional[str] = None,
        view_id: Optional[int] = None,
        view_name: Optional[str] = None,
        view_ids: Optional[List[int]] = None,
        limit: Optional[int] = None,
        save_to_file: bool = False,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the use case.

        Args:
            report_type: Type of report to generate ('sentiment', 'hardware', 'pending')
            time_period: Time period for sentiment reports ('day', 'week', 'month', 'year')
            view_id: Optional view ID to filter by
            view_name: Optional view name for pending reports
            view_ids: Optional list of view IDs for multi-view reports
            limit: Maximum number of tickets to include
            save_to_file: Whether to save the report to a file
            filename: Optional filename for the report

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing generate report use case for report type: {report_type}")

        try:
            report = None

            # Generate the appropriate report based on the report type
            if report_type == "sentiment":
                if not time_period:
                    time_period = "week"
                report = self.reporting_service.generate_sentiment_report(time_period, view_id)
            elif report_type == "hardware":
                report = self.reporting_service.generate_hardware_report(view_id, limit)
            elif report_type == "pending":
                if not view_name:
                    return {
                        "success": False,
                        "error": "View name is required for pending reports",
                        "report_type": report_type
                    }
                report = self.reporting_service.generate_pending_report(view_name, limit)
            elif report_type == "multi_view":
                if not view_ids:
                    return {
                        "success": False,
                        "error": "View IDs are required for multi-view reports",
                        "report_type": report_type
                    }
                # Multi-view reports require a sub-report type
                sub_report_type = time_period or "sentiment"
                report = self.reporting_service.generate_multi_view_report(view_ids, sub_report_type, limit)
            else:
                return {
                    "success": False,
                    "error": f"Unknown report type: {report_type}",
                    "report_type": report_type
                }

            # Create DTO for the report
            report_dto = ReportDTO(
                report_type=report_type,
                content=report,
                time_period=time_period,
                view_id=view_id,
                view_name=view_name,
                view_ids=view_ids,
                limit=limit
            )

            # Save to file if requested
            file_path = None
            if save_to_file:
                file_path = self.reporting_service.save_report(report, filename)

            logger.info(f"Successfully generated {report_type} report")

            # Return success result
            result = {
                "success": True,
                "report_type": report_type,
                "report": report_dto.to_dict()
            }

            if file_path:
                result["file_path"] = file_path

            return result
        except EntityNotFoundError as e:
            logger.error(f"Entity not found: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "report_type": report_type
            }
        except Exception as e:
            logger.exception(f"Unexpected error generating {report_type} report: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "report_type": report_type
            }

    # ====== ADDED METHODS TO BRIDGE COMMAND HANDLER TO REPORTING SERVICE ======

    def generate_sentiment_report(
        self,
        view_id: Optional[int] = None,
        view_name: Optional[str] = None,
        days: int = 7,
        enhanced: bool = False,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a sentiment analysis report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_id: Optional view ID to filter by
            view_name: Optional view name
            days: Number of days to include
            enhanced: Whether to use enhanced format
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report as string
        """
        logger.info(f"Generating sentiment report: view_id={view_id}, days={days}, enhanced={enhanced}")

        # Convert days to time period
        time_period = "week"  # Default
        if days == 1:
            time_period = "day"
        elif days <= 7:
            time_period = "week"
        elif days <= 30:
            time_period = "month"
        elif days > 30:
            time_period = "year"

        # If view_name is provided but view_id is not, try to get view_id from view_name
        if view_name and not view_id:
            # We would need to get the view ID from the name
            # This requires view repository, which might not be available here
            # For now, just log a warning
            logger.warning(f"View name provided without view ID: {view_name}")

        return self.reporting_service.generate_sentiment_report(time_period, view_id)

    def generate_hardware_report(
        self,
        view_id: Optional[int] = None,
        view_name: Optional[str] = None,
        days: int = 7,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a hardware components report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_id: Optional view ID to filter by
            view_name: Optional view name
            days: Number of days to include (not used for hardware reports)
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report as string
        """
        logger.info(f"Generating hardware report: view_id={view_id}, days={days}, format={format_type}")

        # If view_name is provided but view_id is not, try to get view_id from view_name
        if view_name and not view_id:
            # We would need to get the view ID from the name
            # This requires view repository, which might not be available here
            # For now, just log a warning
            logger.warning(f"View name provided without view ID: {view_name}")

        return self.reporting_service.generate_hardware_report(view_id, limit, format_type=format_type)

    def generate_pending_report(
        self,
        view_id: Optional[int] = None,
        view_name: Optional[str] = None,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a pending tickets report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_id: Optional view ID to filter by
            view_name: Optional view name
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report as string
        """
        logger.info(f"Generating pending report: view_id={view_id}, view_name={view_name}, format={format_type}")

        # For pending reports, view_name is required by the reporting service
        if not view_name and view_id:
            # We need the view name, but only have the view ID
            # Ideally, we would get the view name from the view ID
            # For now, use a default name based on the ID
            view_name = f"View {view_id}"
            logger.warning(f"Using default view name '{view_name}' for view ID {view_id}")

        if not view_name:
            # This shouldn't happen if the command handler is validating properly
            logger.error("No view name or view ID provided for pending report")
            raise ValueError("View name is required for pending reports")

        return self.reporting_service.generate_pending_report(view_name, limit)

    def generate_multi_view_sentiment_report(
        self,
        view_ids: Optional[List[int]] = None,
        view_names: Optional[List[str]] = None,
        days: int = 7,
        enhanced: bool = False,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a multi-view sentiment report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_ids: List of view IDs to include
            view_names: List of view names to include
            days: Number of days to include
            enhanced: Whether to use enhanced format
            format_type: Output format
            limit: Maximum number of tickets per view

        Returns:
            Generated report as string
        """
        logger.info(f"Generating multi-view sentiment report: view_ids={view_ids}, view_names={view_names}, days={days}")

        if not view_ids and not view_names:
            logger.error("No view IDs or view names provided for multi-view report")
            raise ValueError("Either view IDs or view names are required for multi-view reports")

        # If we only have view names, try to convert them to view IDs
        converted_view_ids = None
        if not view_ids and view_names:
            from src.domain.interfaces.repository_interfaces import ViewRepository
            from src.infrastructure.service_provider import ServiceProvider

            try:
                # Get the view repository from the service provider
                service_provider = ServiceProvider()
                view_repository = service_provider.get_view_repository()

                # Convert view names to view IDs
                converted_view_ids = []
                for view_name in view_names:
                    view = view_repository.get_view_by_name(view_name)
                    if view:
                        converted_view_ids.append(view['id'])
                        logger.info(f"Converted view name '{view_name}' to ID {view['id']}")
                    else:
                        logger.warning(f"Could not find view with name '{view_name}'")

                if not converted_view_ids:
                    logger.error("Could not convert any view names to IDs")
                    raise ValueError("Could not find any views with the specified names")

                # Use the converted view IDs
                view_ids = converted_view_ids
                logger.info(f"Using converted view IDs: {view_ids}")
            except Exception as e:
                logger.error(f"Error converting view names to IDs: {e}")
                raise ValueError(f"Error converting view names to IDs: {e}")

        return self.reporting_service.generate_multi_view_report(view_ids, "sentiment", limit)

    def generate_multi_view_hardware_report(
        self,
        view_ids: Optional[List[int]] = None,
        view_names: Optional[List[str]] = None,
        days: int = 7,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a multi-view hardware report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_ids: List of view IDs to include
            view_names: List of view names to include
            days: Number of days to include (not used for hardware reports)
            format_type: Output format
            limit: Maximum number of tickets per view

        Returns:
            Generated report as string
        """
        logger.info(f"Generating multi-view hardware report: view_ids={view_ids}, view_names={view_names}")

        if not view_ids and not view_names:
            logger.error("No view IDs or view names provided for multi-view report")
            raise ValueError("Either view IDs or view names are required for multi-view reports")

        # If we only have view names, try to convert them to view IDs
        if not view_ids and view_names:
            from src.domain.interfaces.repository_interfaces import ViewRepository
            from src.infrastructure.service_provider import ServiceProvider

            try:
                # Get the view repository from the service provider
                service_provider = ServiceProvider()
                view_repository = service_provider.get_view_repository()

                # Convert view names to view IDs
                converted_view_ids = []
                for view_name in view_names:
                    view = view_repository.get_view_by_name(view_name)
                    if view:
                        converted_view_ids.append(view['id'])
                        logger.info(f"Converted view name '{view_name}' to ID {view['id']}")
                    else:
                        logger.warning(f"Could not find view with name '{view_name}'")

                if not converted_view_ids:
                    logger.error("Could not convert any view names to IDs")
                    raise ValueError("Could not find any views with the specified names")

                # Use the converted view IDs
                view_ids = converted_view_ids
                logger.info(f"Using converted view IDs: {view_ids}")
            except Exception as e:
                logger.error(f"Error converting view names to IDs: {e}")
                raise ValueError(f"Error converting view names to IDs: {e}")

        return self.reporting_service.generate_multi_view_report(view_ids, "hardware", limit, format_type=format_type)

    def generate_multi_view_pending_report(
        self,
        view_ids: Optional[List[int]] = None,
        view_names: Optional[List[str]] = None,
        format_type: str = "text",
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a multi-view pending report.

        This method acts as a bridge between the command handler and the reporting service.

        Args:
            view_ids: List of view IDs to include
            view_names: List of view names to include
            format_type: Output format
            limit: Maximum number of tickets per view

        Returns:
            Generated report as string
        """
        logger.info(f"Generating multi-view pending report: view_ids={view_ids}, view_names={view_names}")

        if not view_ids and not view_names:
            logger.error("No view IDs or view names provided for multi-view report")
            raise ValueError("Either view IDs or view names are required for multi-view reports")

        # If we only have view names, try to convert them to view IDs
        if not view_ids and view_names:
            from src.domain.interfaces.repository_interfaces import ViewRepository
            from src.infrastructure.service_provider import ServiceProvider

            try:
                # Get the view repository from the service provider
                service_provider = ServiceProvider()
                view_repository = service_provider.get_view_repository()

                # Convert view names to view IDs
                converted_view_ids = []
                for view_name in view_names:
                    view = view_repository.get_view_by_name(view_name)
                    if view:
                        converted_view_ids.append(view['id'])
                        logger.info(f"Converted view name '{view_name}' to ID {view['id']}")
                    else:
                        logger.warning(f"Could not find view with name '{view_name}'")

                if not converted_view_ids:
                    logger.error("Could not convert any view names to IDs")
                    raise ValueError("Could not find any views with the specified names")

                # Use the converted view IDs
                view_ids = converted_view_ids
                logger.info(f"Using converted view IDs: {view_ids}")
            except Exception as e:
                logger.error(f"Error converting view names to IDs: {e}")
                raise ValueError(f"Error converting view names to IDs: {e}")

        return self.reporting_service.generate_multi_view_report(view_ids, "pending", limit)
