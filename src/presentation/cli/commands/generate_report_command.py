"""
Generate Report Command

This module defines the GenerateReportCommand class for generating reports.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class GenerateReportCommand(Command):
    """Command for generating reports."""

    @property
    def description(self) -> str:
        """Get the command description."""
        return "Generate various reports based on ticket analysis"

    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        parser.add_argument(
            "--type",
            choices=["sentiment", "enhanced-sentiment", "hardware", "pending", "multi-view"],
            default="sentiment",
            help="Type of report to generate (default: sentiment)"
        )

        # View selection options
        parser.add_argument(
            "--view-id",
            type=int,
            help="Zendesk view ID to generate report for"
        )

        parser.add_argument(
            "--view-name",
            help="Name of the view to include in the report"
        )

        parser.add_argument(
            "--view-ids",
            help="Comma-separated list of Zendesk view IDs"
        )

        parser.add_argument(
            "--view-names",
            help="Comma-separated list of view names"
        )

        # Time and limit options
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to include in the report (default: 7)"
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of tickets to include"
        )

        # Output options
        parser.add_argument(
            "--format",
            choices=["text", "html", "json", "csv"],
            default="text",
            help="Output format (default: text)"
        )

        parser.add_argument(
            "--output",
            help="Output file path (default: auto-generated)"
        )

        # Format options
        parser.add_argument(
            "--enhanced",
            action="store_true",
            help="Use enhanced report format with more details"
        )

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing report command with args: {args}")

        # Get required services
        generate_report_use_case = self.dependency_container.resolve('generate_report_use_case')

        # Extract arguments
        report_type = args.get("type", "sentiment")
        days = args.get("days", 7)
        format_type = args.get("format", "text")
        output_file = args.get("output")
        enhanced = args.get("enhanced", False)
        limit = args.get("limit")

        # Determine which views to include
        view_info = self._get_view_info(args)

        try:
            # Generate appropriate report based on type
            if report_type == "sentiment" or report_type == "enhanced-sentiment":
                report = self._generate_sentiment_report(
                    generate_report_use_case,
                    view_info,
                    days,
                    enhanced or report_type == "enhanced-sentiment",
                    format_type,
                    limit
                )
            elif report_type == "hardware":
                report = self._generate_hardware_report(
                    generate_report_use_case,
                    view_info,
                    days,
                    format_type,
                    limit
                )
            elif report_type == "pending":
                report = self._generate_pending_report(
                    generate_report_use_case,
                    view_info,
                    format_type,
                    limit
                )
            elif report_type == "multi-view":
                report = self._generate_multi_view_report(
                    generate_report_use_case,
                    view_info,
                    days,
                    enhanced,
                    format_type,
                    limit
                )
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            # Display the report if not saving to file
            if not output_file:
                print(report)

            # Determine output file path and save if specified
            if output_file:
                # Save report to file
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report)

                # Display success message
                print(f"Report generated and saved to: {os.path.abspath(output_file)}")
            else:
                # Generate default filename based on report type
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Use .txt extension for text format, otherwise use the format as extension
                file_extension = "txt" if format_type == "text" else format_type
                default_filename = f"{report_type}_report_{timestamp}.{file_extension}"

                # Save to reports directory
                reports_dir = "reports"
                os.makedirs(reports_dir, exist_ok=True)
                default_path = os.path.join(reports_dir, default_filename)

                # Save report to file
                with open(default_path, "w", encoding="utf-8") as f:
                    f.write(report)

                # Display success message
                print(f"Report generated and saved to: {os.path.abspath(default_path)}")
                output_file = default_path

            return {
                "success": True,
                "report_type": report_type,
                "output_file": os.path.abspath(output_file),
                "days": days,
                "view_info": view_info
            }

        except Exception as e:
            logger.exception(f"Error generating {report_type} report: {e}")
            print(f"Error generating {report_type} report: {e}")
            return {
                "success": False,
                "error": str(e),
                "report_type": report_type
            }

    def _get_view_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about which views to include in the report.

        Args:
            args: Command-line arguments

        Returns:
            Dictionary with view information
        """
        view_info = {}

        # Check for view ID
        if "view_id" in args and args["view_id"] is not None:
            view_info["view_id"] = args["view_id"]

        # Check for view name
        if "view_name" in args and args["view_name"] is not None:
            view_info["view_name"] = args["view_name"]

        # Check for multiple view IDs
        if "view_ids" in args and args["view_ids"] is not None:
            # Split comma-separated list
            view_ids = [int(vid.strip()) for vid in args["view_ids"].split(",") if vid.strip()]
            view_info["view_ids"] = view_ids

        # Check for multiple view names
        if "view_names" in args and args["view_names"] is not None:
            # Split comma-separated list
            view_names = [name.strip() for name in args["view_names"].split(",") if name.strip()]
            view_info["view_names"] = view_names

        return view_info

    def _generate_sentiment_report(
        self,
        generate_report_use_case,
        view_info: Dict[str, Any],
        days: int,
        enhanced: bool,
        format_type: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a sentiment analysis report.

        Args:
            generate_report_use_case: Use case for generating reports
            view_info: Information about which views to include
            days: Number of days to include
            enhanced: Whether to use enhanced format
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report
        """
        logger.info(f"Generating sentiment report: views={view_info}, days={days}, enhanced={enhanced}, format={format_type}")

        # Check if multi-view report is needed
        if "view_ids" in view_info or "view_names" in view_info:
            return generate_report_use_case.generate_multi_view_sentiment_report(
                view_ids=view_info.get("view_ids"),
                view_names=view_info.get("view_names"),
                days=days,
                enhanced=enhanced,
                format_type=format_type,
                limit=limit
            )

        # Single view report
        return generate_report_use_case.generate_sentiment_report(
            view_id=view_info.get("view_id"),
            view_name=view_info.get("view_name"),
            days=days,
            enhanced=enhanced,
            format_type=format_type,
            limit=limit
        )

    def _generate_hardware_report(
        self,
        generate_report_use_case,
        view_info: Dict[str, Any],
        days: int,
        format_type: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a hardware components report.

        Args:
            generate_report_use_case: Use case for generating reports
            view_info: Information about which views to include
            days: Number of days to include
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report
        """
        logger.info(f"Generating hardware report: views={view_info}, days={days}, format={format_type}")

        # Check if multi-view report is needed
        if "view_ids" in view_info or "view_names" in view_info:
            return generate_report_use_case.generate_multi_view_hardware_report(
                view_ids=view_info.get("view_ids"),
                view_names=view_info.get("view_names"),
                days=days,
                format_type=format_type,
                limit=limit
            )

        # Single view report
        return generate_report_use_case.generate_hardware_report(
            view_id=view_info.get("view_id"),
            view_name=view_info.get("view_name"),
            days=days,
            format_type=format_type,
            limit=limit
        )

    def _generate_pending_report(
        self,
        generate_report_use_case,
        view_info: Dict[str, Any],
        format_type: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a pending tickets report.

        Args:
            generate_report_use_case: Use case for generating reports
            view_info: Information about which views to include
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report
        """
        logger.info(f"Generating pending report: views={view_info}, format={format_type}")

        # Check if multi-view report is needed
        if "view_ids" in view_info or "view_names" in view_info:
            return generate_report_use_case.generate_multi_view_pending_report(
                view_ids=view_info.get("view_ids"),
                view_names=view_info.get("view_names"),
                format_type=format_type,
                limit=limit
            )

        # Single view report
        return generate_report_use_case.generate_pending_report(
            view_id=view_info.get("view_id"),
            view_name=view_info.get("view_name"),
            format_type=format_type,
            limit=limit
        )

    def _generate_multi_view_report(
        self,
        generate_report_use_case,
        view_info: Dict[str, Any],
        days: int,
        enhanced: bool,
        format_type: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Generate a multi-view report.

        Args:
            generate_report_use_case: Use case for generating reports
            view_info: Information about which views to include
            days: Number of days to include
            enhanced: Whether to use enhanced format
            format_type: Output format
            limit: Maximum number of tickets to include

        Returns:
            Generated report
        """
        logger.info(f"Generating multi-view report: views={view_info}, days={days}, enhanced={enhanced}, format={format_type}")

        # Check if view IDs or names are provided
        if "view_ids" in view_info or "view_names" in view_info:
            return generate_report_use_case.generate_multi_view_sentiment_report(
                view_ids=view_info.get("view_ids"),
                view_names=view_info.get("view_names"),
                days=days,
                enhanced=enhanced,
                format_type=format_type,
                limit=limit
            )
        else:
            # No view IDs or names provided
            raise ValueError("Multi-view report requires either view IDs (--view-ids) or view names (--view-names)")
