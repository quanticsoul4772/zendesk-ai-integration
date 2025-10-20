"""
List Views Command

This module defines the ListViewsCommand class for listing Zendesk views.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class ViewHierarchyFormatter:
    """Utility class for formatting view hierarchies."""

    def format_hierarchy(self, views: List[Dict[str, Any]], include_inactive: bool = False,
                         filter_string: Optional[str] = None) -> str:
        """
        Format views into a hierarchical structure.

        Args:
            views: List of view objects
            include_inactive: Whether to include inactive views
            filter_string: Optional string to filter views by name

        Returns:
            Formatted string representation
        """
        # Filter views based on active status and filter string
        filtered_views = []
        for view in views:
            # Skip inactive views if not including them
            if not include_inactive and not view.get("active", True):
                continue

            # Filter by name if filter string is provided
            if filter_string and filter_string.lower() not in view.get("title", "").lower():
                continue

            filtered_views.append(view)

        # Group views by parent_id
        views_by_parent = {}
        for view in filtered_views:
            parent_id = view.get("parent_id", 0)
            if parent_id not in views_by_parent:
                views_by_parent[parent_id] = []
            views_by_parent[parent_id].append(view)

        # Format the hierarchy
        result = "Available Zendesk Views:\n"
        result += "=====================\n\n"

        if filter_string:
            result += f"Filter: '{filter_string}'\n\n"

        if not include_inactive:
            result += "Note: Inactive views are hidden. Use --include-inactive to show them.\n\n"

        # Add total count
        result += f"Total Views: {len(filtered_views)}\n\n"

        # Add root views (with no parent) and get updated result
        result = self._append_views(result, views_by_parent, 0, 0)

        return result

    def _append_views(self, result: str, views_by_parent: Dict[int, List[Dict[str, Any]]],
                     parent_id: int, level: int) -> str:
        """
        Append views with the given parent ID to the result string.

        Args:
            result: Result string to append to
            views_by_parent: Views grouped by parent ID
            parent_id: Parent ID to filter by
            level: Current hierarchy level

        Returns:
            Updated result string
        """
        if parent_id not in views_by_parent:
            return result

        # Sort views by title
        views = sorted(views_by_parent[parent_id], key=lambda v: v.get("title", ""))

        # Create a new result string to hold the current result and new additions
        updated_result = result

        # Append each view
        for view in views:
            # Indent based on level
            indent = "  " * level

            # Add view information
            title = view.get('title', 'Unnamed View')
            view_id = view.get('id', 'Unknown ID')

            # Mark inactive views
            inactive_marker = " (Inactive)" if not view.get("active", True) else ""

            updated_result += f"{indent}- {title}{inactive_marker} (ID: {view_id})\n"

            # Recursively add child views and update the result string
            updated_result = self._append_views(updated_result, views_by_parent, view.get("id"), level + 1)

        return updated_result

    def format_flat_list(self, views: List[Dict[str, Any]], include_inactive: bool = False,
                        filter_string: Optional[str] = None) -> str:
        """
        Format views as a flat list.

        Args:
            views: List of view objects
            include_inactive: Whether to include inactive views
            filter_string: Optional string to filter views by name

        Returns:
            Formatted string representation
        """
        # Filter views based on active status and filter string
        filtered_views = []
        for view in views:
            # Skip inactive views if not including them
            if not include_inactive and not view.get("active", True):
                continue

            # Filter by name if filter string is provided
            if filter_string and filter_string.lower() not in view.get("title", "").lower():
                continue

            filtered_views.append(view)

        # Sort views by title
        sorted_views = sorted(filtered_views, key=lambda v: v.get("title", ""))

        # Format the flat list
        result = "Zendesk Views:\n"
        result += "=============\n\n"

        if filter_string:
            result += f"Filter: '{filter_string}'\n\n"

        if not include_inactive:
            result += "Note: Inactive views are hidden. Use --include-inactive to show them.\n\n"

        # Add total count
        result += f"Total Views: {len(filtered_views)}\n\n"

        # Add each view
        for view in sorted_views:
            title = view.get('title', 'Unnamed View')
            view_id = view.get('id', 'Unknown ID')

            # Mark inactive views
            inactive_marker = " (Inactive)" if not view.get("active", True) else ""

            result += f"{title}{inactive_marker} (ID: {view_id})\n"

        return result


class ListViewsCommand(Command):
    """Command for listing Zendesk views."""

    @property
    def name(self) -> str:
        """Get the command name."""
        return "views"

    @property
    def description(self) -> str:
        """Get the command description."""
        return "List all available Zendesk views"

    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        parser.add_argument(
            "--format",
            choices=["text", "json", "csv"],
            default="text",
            help="Output format (default: text)"
        )

        parser.add_argument(
            "--output",
            help="Output file path (default: print to console)"
        )

        parser.add_argument(
            "--flat",
            action="store_true",
            help="Display as a flat list instead of a hierarchy"
        )

        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Include inactive views"
        )

        parser.add_argument(
            "--filter",
            help="Filter views by name (case-insensitive)"
        )

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing views command with args: {args}")

        # Get required services
        from src.domain.interfaces.repository_interfaces import ViewRepository
        view_repository = self.dependency_container.resolve(ViewRepository)

        try:
            # Extract arguments
            format_type = args.get("format", "text")
            output_file = args.get("output")
            flat = args.get("flat", False)
            include_inactive = args.get("include_inactive", False)
            filter_string = args.get("filter")

            # Get all views
            views = view_repository.get_all_views()

            # Filter views if needed
            filtered_views = self._filter_views(views, include_inactive, filter_string)

            # Generate output based on requested format
            if format_type == "json":
                # JSON format
                output = json.dumps(filtered_views, indent=2)
            elif format_type == "csv":
                # CSV format
                output = self._generate_csv(filtered_views)
            else:
                # Text format
                formatter = ViewHierarchyFormatter()
                if flat:
                    output = formatter.format_flat_list(views, include_inactive, filter_string)
                else:
                    output = formatter.format_hierarchy(views, include_inactive, filter_string)

            # Output to file or console
            if output_file:
                # Create directory if it doesn't exist
                output_dir = os.path.dirname(output_file)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                # Write to file
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(output)

                print(f"Views list saved to: {os.path.abspath(output_file)}")
            else:
                # Print to console
                print(output)

            return {
                "success": True,
                "views_count": len(filtered_views),
                "format": format_type,
                "output_file": output_file,
                "include_inactive": include_inactive,
                "filter": filter_string
            }

        except Exception as e:
            logger.exception(f"Error listing views: {e}")
            print(f"Error listing views: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _filter_views(self, views: List[Dict[str, Any]], include_inactive: bool,
                      filter_string: Optional[str]) -> List[Dict[str, Any]]:
        """
        Filter views based on criteria.

        Args:
            views: List of views to filter
            include_inactive: Whether to include inactive views
            filter_string: Optional string to filter views by name

        Returns:
            Filtered list of views
        """
        filtered_views = []

        for view in views:
            # Skip inactive views if not including them
            if not include_inactive and not view.get("active", True):
                continue

            # Filter by name if filter string is provided
            if filter_string and filter_string.lower() not in view.get("title", "").lower():
                continue

            filtered_views.append(view)

        return filtered_views

    def _generate_csv(self, views: List[Dict[str, Any]]) -> str:
        """
        Generate CSV output for views.

        Args:
            views: List of views

        Returns:
            CSV formatted string
        """
        # Define CSV header
        header = "ID,Title,Active,Parent ID,URL\n"

        # Generate CSV rows
        rows = []
        for view in views:
            view_id = view.get("id", "")
            title = view.get("title", "").replace(",", "\\,")  # Escape commas
            active = "Yes" if view.get("active", True) else "No"
            parent_id = view.get("parent_id", "")
            url = f"https://yourdomain.zendesk.com/agent/filters/{view_id}" if view_id else ""

            row = f"{view_id},{title},{active},{parent_id},{url}"
            rows.append(row)

        # Combine header and rows
        return header + "\n".join(rows)
