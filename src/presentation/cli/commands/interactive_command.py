"""
Interactive Command

This module defines the InteractiveCommand class for an interactive menu interface.
"""

import json
import logging
import os
import platform
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class InteractiveMenu:
    """Interactive menu system for navigating Zendesk views and actions."""

    def __init__(self, dependency_container):
        """
        Initialize the interactive menu.

        Args:
            dependency_container: Container for service dependencies
        """
        self.dependency_container = dependency_container

        # Recent views
        self.recent_views = []
        self.max_recent_views = 5

        # Search pattern
        self.search_pattern = None

        # View tree
        self.view_tree = []
        self.filtered_views = []

        # Navigation state
        self.menu_history = []
        self.current_path = []

        # Terminal size
        self.terminal_width, self.terminal_height = self._get_terminal_size()

    def _get_terminal_size(self) -> Tuple[int, int]:
        """
        Get the terminal size.

        Returns:
            Tuple of (width, height)
        """
        try:
            import shutil
            width, height = shutil.get_terminal_size()
            return width, height
        except (ImportError, AttributeError):
            # Fallback
            return 80, 24

    def start(self) -> None:
        """Start the interactive menu."""
        try:
            # Load views
            self._load_views()

            # Build view hierarchy
            self._build_view_hierarchy()

            # Start main menu
            self._main_menu()
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            logger.exception(f"Error in interactive menu: {e}")
            print(f"Error: {e}")

    def _load_views(self) -> None:
        """Load views from Zendesk."""
        print("Loading views from Zendesk...")
        try:
            # Get view repository
            view_repository = self.dependency_container.resolve('ticket_repository')

            # Get all views
            self.views = view_repository.get_all_views()

            print(f"Loaded {len(self.views)} views")
        except Exception as e:
            logger.exception(f"Error loading views: {e}")
            print(f"Error loading views: {e}")
            self.views = []

    def _build_view_hierarchy(self) -> None:
        """Build a hierarchical tree of views."""
        # Group views by parent_id
        views_by_parent = {}
        for view in self.views:
            # Skip inactive views
            if not view.get("active", True):
                continue

            parent_id = view.get("parent_id", 0)
            if parent_id not in views_by_parent:
                views_by_parent[parent_id] = []
            views_by_parent[parent_id].append(view)

        # Build tree starting from root views (parent_id = 0)
        self.view_tree = self._build_tree_level(views_by_parent, 0)

        # Initialize filtered views
        self.filtered_views = self.view_tree.copy()

    def _build_tree_level(self, views_by_parent: Dict[int, List[Dict[str, Any]]],
                         parent_id: int) -> List[Dict[str, Any]]:
        """
        Build a tree level.

        Args:
            views_by_parent: Views grouped by parent ID
            parent_id: Parent ID to filter by

        Returns:
            List of views at this level
        """
        if parent_id not in views_by_parent:
            return []

        # Sort views by title
        views = sorted(views_by_parent[parent_id], key=lambda v: v.get("title", ""))

        # Add children to each view
        for view in views:
            view_id = view.get("id")
            view["children"] = self._build_tree_level(views_by_parent, view_id)

        return views

    def _main_menu(self) -> None:
        """Display the main menu."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Zendesk AI Integration - Main Menu")

            # Display menu options
            print("1. Browse Views")
            print("2. Recent Views")
            print("3. Search Views")
            print("4. Analyze Ticket")
            print("5. Generate Report")
            print("6. Webhook Management")
            print("7. Scheduler Management")
            print("8. Exit")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-8): ", r"^[1-8]$")

            # Handle choice
            if choice == "1":
                self._browse_views_menu()
            elif choice == "2":
                self._recent_views_menu()
            elif choice == "3":
                self._search_views_menu()
            elif choice == "4":
                self._analyze_ticket_menu()
            elif choice == "5":
                self._generate_report_menu()
            elif choice == "6":
                self._webhook_menu()
            elif choice == "7":
                self._scheduler_menu()
            elif choice == "8":
                print("\nExiting...")
                break

    def _browse_views_menu(self) -> None:
        """Display the browse views menu."""
        # Reset current path and filtered views
        self.current_path = []
        self.filtered_views = self.view_tree.copy()

        # Navigate view hierarchy
        self._navigate_views("Browse Views")

    def _recent_views_menu(self) -> None:
        """Display the recent views menu."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Recent Views")

            # Display recent views
            if not self.recent_views:
                print("No recent views.")
                self._wait_for_input()
                break

            # Display recent views
            for i, view in enumerate(self.recent_views, 1):
                print(f"{i}. {view.get('title')} (ID: {view.get('id')})")

            print(f"{len(self.recent_views) + 1}. Back")

            # Get user choice
            choice = self._get_input(f"\nEnter your choice (1-{len(self.recent_views) + 1}): ",
                                    f"^[1-{len(self.recent_views) + 1}]$")

            # Handle choice
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.recent_views):
                    self._view_actions_menu(self.recent_views[choice_num - 1])
                else:
                    break
            except ValueError:
                print("Invalid choice. Please try again.")
                self._wait_for_input()

    def _search_views_menu(self) -> None:
        """Display the search views menu."""
        # Get search pattern
        search_pattern = input("\nEnter search pattern: ")

        if not search_pattern:
            return

        # Search views
        results = self._search_views(search_pattern)

        # Display results
        self._display_search_results(search_pattern, results)

    def _search_views(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Search views.

        Args:
            pattern: Search pattern

        Returns:
            List of matching views
        """
        results = []
        pattern_lower = pattern.lower()

        for view in self.views:
            # Skip inactive views
            if not view.get("active", True):
                continue

            title = view.get("title", "").lower()
            if pattern_lower in title:
                results.append(view)

        return results

    def _display_search_results(self, pattern: str, results: List[Dict[str, Any]]) -> None:
        """
        Display search results.

        Args:
            pattern: Search pattern
            results: Search results
        """
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(f"Search Results: '{pattern}'")

            if not results:
                print("No matching views found.")
                self._wait_for_input()
                break

            # Display results
            for i, view in enumerate(results, 1):
                print(f"{i}. {view.get('title')} (ID: {view.get('id')})")

            print(f"{len(results) + 1}. Back")

            # Get user choice
            choice = self._get_input(f"\nEnter your choice (1-{len(results) + 1}): ",
                                    f"^[1-{len(results) + 1}]$")

            # Handle choice
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(results):
                    # Add to recent views
                    self._add_to_recent_views(results[choice_num - 1])

                    # Show view actions
                    self._view_actions_menu(results[choice_num - 1])
                else:
                    break
            except ValueError:
                print("Invalid choice. Please try again.")
                self._wait_for_input()

    def _navigate_views(self, title: str, views: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Navigate view hierarchy.

        Args:
            title: Menu title
            views: Views to display (default: current filtered views)
        """
        if views is None:
            views = self.filtered_views

        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(title)

            # Display current path
            if self.current_path:
                path_str = " > ".join(self.current_path)
                print(f"Path: {path_str}\n")

            # Display views
            if not views:
                print("No views in this category.")
                self._wait_for_input()
                break

            # Display views
            for i, view in enumerate(views, 1):
                has_children = bool(view.get("children"))
                child_indicator = "+" if has_children else " "
                print(f"{i}. [{child_indicator}] {view.get('title')} (ID: {view.get('id')})")

            # Extra options
            view_count = len(views)
            print(f"{view_count + 1}. Back")

            # Get user choice
            choice = self._get_input(f"\nEnter your choice (1-{view_count + 1}): ",
                                    f"^[1-{view_count + 1}]$")

            # Handle choice
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= view_count:
                    selected_view = views[choice_num - 1]
                    children = selected_view.get("children", [])

                    # Add to recent views
                    self._add_to_recent_views(selected_view)

                    if children:
                        # Navigate to children
                        self.current_path.append(selected_view.get("title", ""))
                        self._navigate_views(f"Browse Views: {selected_view.get('title', '')}", children)
                        self.current_path.pop()
                    else:
                        # Show view actions
                        self._view_actions_menu(selected_view)
                else:
                    break
            except ValueError:
                print("Invalid choice. Please try again.")
                self._wait_for_input()

    def _view_actions_menu(self, view: Dict[str, Any]) -> None:
        """
        Display actions for a view.

        Args:
            view: View to show actions for
        """
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            view_title = view.get("title", "")
            view_id = view.get("id")
            self._display_header(f"View: {view_title} (ID: {view_id})")

            # Display actions
            print("1. Analyze Tickets in View")
            print("2. Generate Sentiment Report")
            print("3. Generate Hardware Report")
            print("4. Generate Pending Report")
            print("5. View Tickets in Browser")
            print("6. Back")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-6): ", r"^[1-6]$")

            # Handle choice
            if choice == "1":
                self._analyze_view(view)
            elif choice == "2":
                self._generate_view_report(view, "sentiment")
            elif choice == "3":
                self._generate_view_report(view, "hardware")
            elif choice == "4":
                self._generate_view_report(view, "pending")
            elif choice == "5":
                self._view_tickets_in_browser(view)
            elif choice == "6":
                break

    def _analyze_ticket_menu(self) -> None:
        """Menu for analyzing a single ticket."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Analyze Ticket")

        # Get ticket ID
        ticket_id_str = self._get_input("Enter ticket ID: ", r"^\d+$")
        ticket_id = int(ticket_id_str)

        # Get AI service
        use_claude = self._yes_no_prompt("Use Claude AI service?")

        # Get required services
        analyze_ticket_use_case = self.dependency_container.resolve('analyze_ticket_use_case')

        if use_claude:
            # Switch to Claude service
            ticket_analysis_service = self.dependency_container.resolve('ticket_analysis_service')
            claude_service = self.dependency_container.resolve('claude_service')
            ticket_analysis_service.ai_service = claude_service

        print(f"\nAnalyzing ticket {ticket_id}...")

        try:
            # Execute the use case
            analysis = analyze_ticket_use_case.analyze_ticket(ticket_id)

            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(f"Analysis Results: Ticket {ticket_id}")

            # Display analysis results
            print(f"Subject: {analysis.subject}")
            print(f"Sentiment: {analysis.sentiment}")
            print(f"Category: {analysis.category}")
            print(f"Priority: {analysis.priority}")
            print(f"Hardware components: {', '.join(analysis.hardware_components) if analysis.hardware_components else 'None'}")

            if hasattr(analysis, 'business_impact') and analysis.business_impact:
                print(f"Business impact: {analysis.business_impact}")

            if hasattr(analysis, 'frustration_level') and analysis.frustration_level:
                print(f"Frustration level: {analysis.frustration_level}/5")

            if hasattr(analysis, 'urgency') and analysis.urgency:
                print(f"Urgency: {analysis.urgency}/5")

            # Action options
            print("\nActions:")
            print("1. Add Comments to Ticket")
            print("2. Add Tags to Ticket")
            print("3. Back to Main Menu")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-3): ", r"^[1-3]$")

            if choice == "1":
                self._add_comments_to_ticket(ticket_id, analysis)
            elif choice == "2":
                self._add_tags_to_ticket(ticket_id, analysis)

            self._wait_for_input()

        except Exception as e:
            print(f"Error analyzing ticket: {e}")
            self._wait_for_input()

    def _analyze_view(self, view: Dict[str, Any]) -> None:
        """
        Analyze tickets in a view.

        Args:
            view: View to analyze tickets in
        """
        # Clear screen
        self._clear_screen()

        # Display header
        view_title = view.get("title", "")
        view_id = view.get("id")
        self._display_header(f"Analyze View: {view_title} (ID: {view_id})")

        # Get options
        limit = self._get_input("Enter maximum number of tickets to analyze (blank for all): ", r"^\d*$")
        limit = int(limit) if limit else None

        use_claude = self._yes_no_prompt("Use Claude AI service?")
        add_comments = self._yes_no_prompt("Add analysis as comments to tickets?")
        add_tags = self._yes_no_prompt("Add tags based on analysis to tickets?")

        # Get required services
        analyze_ticket_use_case = self.dependency_container.resolve('analyze_ticket_use_case')

        if use_claude:
            # Switch to Claude service
            ticket_analysis_service = self.dependency_container.resolve('ticket_analysis_service')
            claude_service = self.dependency_container.resolve('claude_service')
            ticket_analysis_service.ai_service = claude_service

        print(f"\nAnalyzing tickets in view {view_id}...")

        try:
            # Execute the use case
            analyses = analyze_ticket_use_case.analyze_view(
                view_id=view_id,
                limit=limit,
                add_comment=add_comments,
                add_tags=add_tags
            )

            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(f"Analysis Results: {view_title}")

            # Print summary
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
            priority_labels = {
                10: "Critical (10)",
                9: "Very High (9)",
                8: "High (8)",
                7: "Medium-High (7)",
                6: "Medium (6)",
                5: "Medium (5)",
                4: "Medium-Low (4)",
                3: "Low (3)",
                2: "Very Low (2)",
                1: "Minimal (1)"
            }

            for priority in sorted(priority_counts.keys(), reverse=True):
                count = priority_counts[priority]
                label = priority_labels.get(priority, f"Priority {priority}")
                print(f"  {label}: {count}")

            if add_comments:
                print(f"\nAdded comments to tickets: Yes")

            if add_tags:
                print(f"\nAdded tags to tickets: Yes")

            self._wait_for_input()

        except Exception as e:
            print(f"Error analyzing view: {e}")
            self._wait_for_input()

    def _generate_report_menu(self) -> None:
        """Menu for generating reports."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Generate Report")

            # Display menu options
            print("1. Sentiment Report")
            print("2. Enhanced Sentiment Report")
            print("3. Hardware Report")
            print("4. Pending Report")
            print("5. Multi-View Report")
            print("6. Back to Main Menu")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-6): ", r"^[1-6]$")

            # Handle choice
            if choice == "1":
                self._generate_report("sentiment", False)
            elif choice == "2":
                self._generate_report("sentiment", True)
            elif choice == "3":
                self._generate_report("hardware", False)
            elif choice == "4":
                self._generate_report("pending", False)
            elif choice == "5":
                self._generate_multi_view_report()
            elif choice == "6":
                break

    def _generate_report(self, report_type: str, enhanced: bool) -> None:
        """
        Generate a report.

        Args:
            report_type: Type of report to generate
            enhanced: Whether to use enhanced format
        """
        # Clear screen
        self._clear_screen()

        # Display header
        type_label = f"Enhanced {report_type.capitalize()}" if enhanced else report_type.capitalize()
        self._display_header(f"Generate {type_label} Report")

        # Get view ID
        view_id_str = self._get_input("Enter view ID (blank for all tickets): ", r"^\d*$")
        view_id = int(view_id_str) if view_id_str else None

        # Get days to include
        if report_type in ["sentiment", "hardware"]:
            days_str = self._get_input("Enter number of days to include (default: 7): ", r"^\d*$")
            days = int(days_str) if days_str else 7
        else:
            days = 7

        # Get output format
        format_options = ["text", "html", "json"]
        format_type = self._select_from_options("Select output format:", format_options)

        # Get required services
        generate_report_use_case = self.dependency_container.resolve('generate_report_use_case')

        print(f"\nGenerating {type_label} report...")

        try:
            # Generate report
            if report_type == "sentiment":
                report = generate_report_use_case.generate_sentiment_report(
                    view_id=view_id,
                    days=days,
                    enhanced=enhanced,
                    format_type=format_type
                )
            elif report_type == "hardware":
                report = generate_report_use_case.generate_report_use_case.execute(
                    view_id=view_id,
                    days=days,
                    format_type=format_type
                )
            elif report_type == "pending":
                report = generate_report_use_case.generate_report_use_case.execute(
                    view_id=view_id,
                    format_type=format_type
                )

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"{'enhanced_' if enhanced else ''}{report_type}"
            filename = f"{report_name}_report_{timestamp}.{format_type}"

            # Create report directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)

            # Save report to file
            report_path = os.path.join(reports_dir, filename)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(f"{type_label} Report Generated")

            print(f"Report saved to: {os.path.abspath(report_path)}")

            # Display report if it's text format
            if format_type == "text" and self._yes_no_prompt("View report?"):
                # Clear screen
                self._clear_screen()

                # Display header
                self._display_header(f"{type_label} Report")

                # Display report
                print(report)

            self._wait_for_input()

        except Exception as e:
            print(f"Error generating report: {e}")
            self._wait_for_input()

    def _generate_view_report(self, view: Dict[str, Any], report_type: str) -> None:
        """
        Generate a report for a specific view.

        Args:
            view: View to generate report for
            report_type: Type of report to generate
        """
        # Clear screen
        self._clear_screen()

        # Display header
        view_title = view.get("title", "")
        view_id = view.get("id")
        self._display_header(f"Generate {report_type.capitalize()} Report: {view_title}")

        # Get days to include for sentiment and hardware reports
        if report_type in ["sentiment", "hardware"]:
            days_str = self._get_input("Enter number of days to include (default: 7): ", r"^\d*$")
            days = int(days_str) if days_str else 7
        else:
            days = 7

        # Get enhanced option for sentiment reports
        enhanced = False
        if report_type == "sentiment":
            enhanced = self._yes_no_prompt("Generate enhanced sentiment report?")

        # Get output format
        format_options = ["text", "html", "json"]
        format_type = self._select_from_options("Select output format:", format_options)

        # Get required services
        generate_report_use_case = self.dependency_container.resolve('generate_report_use_case')

        print(f"\nGenerating {report_type} report for view {view_id}...")

        try:
            # Generate report
            if report_type == "sentiment":
                report = generate_report_use_case.generate_sentiment_report(
                    view_id=view_id,
                    days=days,
                    enhanced=enhanced,
                    format_type=format_type
                )
            elif report_type == "hardware":
                report = generate_report_use_case.generate_report_use_case.execute(
                    view_id=view_id,
                    days=days,
                    format_type=format_type
                )
            elif report_type == "pending":
                report = generate_report_use_case.generate_report_use_case.execute(
                    view_id=view_id,
                    format_type=format_type
                )

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"{'enhanced_' if enhanced and report_type == 'sentiment' else ''}{report_type}"
            filename = f"{report_name}_report_{view_id}_{timestamp}.{format_type}"

            # Create report directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)

            # Save report to file
            report_path = os.path.join(reports_dir, filename)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header(f"Report Generated: {view_title}")

            print(f"Report saved to: {os.path.abspath(report_path)}")

            # Display report if it's text format
            if format_type == "text" and self._yes_no_prompt("View report?"):
                # Clear screen
                self._clear_screen()

                # Display header
                self._display_header(f"{report_type.capitalize()} Report: {view_title}")

                # Display report
                print(report)

            self._wait_for_input()

        except Exception as e:
            print(f"Error generating report: {e}")
            self._wait_for_input()

    def _generate_multi_view_report(self) -> None:
        """Generate a multi-view report."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Generate Multi-View Report")

        # Get view IDs
        view_ids_str = self._get_input("Enter comma-separated view IDs: ", r"^(\d+,)*\d+$")
        view_ids = [int(v.strip()) for v in view_ids_str.split(",") if v.strip()]

        # Get days to include
        days_str = self._get_input("Enter number of days to include (default: 7): ", r"^\d*$")
        days = int(days_str) if days_str else 7

        # Get enhanced option
        enhanced = self._yes_no_prompt("Generate enhanced sentiment report?")

        # Get output format
        format_options = ["text", "html", "json"]
        format_type = self._select_from_options("Select output format:", format_options)

        # Get required services
        generate_report_use_case = self.dependency_container.resolve('generate_report_use_case')

        print(f"\nGenerating multi-view report for {len(view_ids)} views...")

        try:
            # Generate report
            report = generate_report_use_case.generate_multi_view_sentiment_report(
                view_ids=view_ids,
                days=days,
                enhanced=enhanced,
                format_type=format_type
            )

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_view_report_{timestamp}.{format_type}"

            # Create report directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)

            # Save report to file
            report_path = os.path.join(reports_dir, filename)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Multi-View Report Generated")

            print(f"Report saved to: {os.path.abspath(report_path)}")

            # Display report if it's text format
            if format_type == "text" and self._yes_no_prompt("View report?"):
                # Clear screen
                self._clear_screen()

                # Display header
                self._display_header("Multi-View Report")

                # Display report
                print(report)

            self._wait_for_input()

        except Exception as e:
            print(f"Error generating multi-view report: {e}")
            self._wait_for_input()

    def _webhook_menu(self) -> None:
        """Menu for webhook management."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Webhook Management")

            # Display menu options
            print("1. Start Webhook Server")
            print("2. Stop Webhook Server")
            print("3. Get Webhook Status")
            print("4. Back to Main Menu")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-4): ", r"^[1-4]$")

            # Handle choice
            if choice == "1":
                self._start_webhook()
            elif choice == "2":
                self._stop_webhook()
            elif choice == "3":
                self._webhook_status()
            elif choice == "4":
                break

    def _start_webhook(self) -> None:
        """Start the webhook server."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Start Webhook Server")

        # Get webhook configuration
        # Default to 0.0.0.0 to bind to all interfaces for webhook server (user configurable)
        host = self._get_input("Enter host (default: 0.0.0.0): ", r"^[a-zA-Z0-9\.:]+$") or "0.0.0.0"  # nosec B104
        port_str = self._get_input("Enter port (default: 5000): ", r"^\d*$") or "5000"
        port = int(port_str)
        path = self._get_input("Enter webhook path (default: /webhook): ", r"^/.*$") or "/webhook"

        # Get webhook options
        add_comments = self._yes_no_prompt("Add analysis as comments to tickets?")
        add_tags = self._yes_no_prompt("Add tags based on analysis to tickets?")

        # Get webhook service
        webhook_service = self.dependency_container.resolve('webhook_service')

        print(f"\nStarting webhook server on {host}:{port}{path}...")

        try:
            # Configure webhook service
            webhook_service.set_comment_preference(add_comments)
            webhook_service.set_tag_preference(add_tags)

            # Create webhook handler
            from src.presentation.webhook.webhook_handler import WebhookHandler
            webhook_handler = WebhookHandler(webhook_service)

            # Start webhook server in a background thread
            import threading
            self.webhook_thread = threading.Thread(
                target=webhook_handler.start,
                args=(host, port, path, False),
                daemon=True
            )
            self.webhook_thread.start()

            # Store webhook handler for stopping later
            self.webhook_handler = webhook_handler

            print(f"\nWebhook server started on http://{host}:{port}{path}")
            print("\nConfiguration:")
            print(f"  - Add comments: {add_comments}")
            print(f"  - Add tags: {add_tags}")
            print("\nServer is running in the background.")
            print("Use 'Stop Webhook Server' to stop it when finished.")

            # Save state
            self.webhook_status = {
                "running": True,
                "host": host,
                "port": port,
                "path": path,
                "add_comments": add_comments,
                "add_tags": add_tags
            }

            self._wait_for_input()

        except Exception as e:
            print(f"Error starting webhook server: {e}")
            self._wait_for_input()

    def _stop_webhook(self) -> None:
        """Stop the webhook server."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Stop Webhook Server")

        if not hasattr(self, 'webhook_thread') or not self.webhook_thread.is_alive():
            print("Webhook server is not running.")
            self._wait_for_input()
            return

        print("Stopping webhook server...")

        try:
            # Stop the webhook server
            if hasattr(self, 'webhook_handler'):
                self.webhook_handler.stop()

            # Update status
            self.webhook_status = {"running": False}

            print("Webhook server stopped.")
            self._wait_for_input()

        except Exception as e:
            print(f"Error stopping webhook server: {e}")
            self._wait_for_input()

    def _webhook_status(self) -> None:
        """Display webhook server status."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Webhook Server Status")

        if hasattr(self, 'webhook_status') and self.webhook_status.get("running", False):
            # Server is running
            host = self.webhook_status.get("host", "0.0.0.0")  # nosec B104
            port = self.webhook_status.get("port", 5000)
            path = self.webhook_status.get("path", "/webhook")
            add_comments = self.webhook_status.get("add_comments", False)
            add_tags = self.webhook_status.get("add_tags", False)

            print("Webhook server is running.")
            print(f"URL: http://{host}:{port}{path}")
            print("\nConfiguration:")
            print(f"  - Add comments: {add_comments}")
            print(f"  - Add tags: {add_tags}")
        else:
            print("Webhook server is not running.")

        self._wait_for_input()

    def _scheduler_menu(self) -> None:
        """Menu for scheduler management."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Scheduler Management")

            # Display menu options
            print("1. Schedule New Task")
            print("2. List Scheduled Tasks")
            print("3. Remove Task")
            print("4. Start Scheduler Daemon")
            print("5. Stop Scheduler Daemon")
            print("6. Back to Main Menu")

            # Get user choice
            choice = self._get_input("\nEnter your choice (1-6): ", r"^[1-6]$")

            # Handle choice
            if choice == "1":
                self._schedule_task_menu()
            elif choice == "2":
                self._list_scheduled_tasks()
            elif choice == "3":
                self._remove_task()
            elif choice == "4":
                self._start_scheduler_daemon()
            elif choice == "5":
                self._stop_scheduler_daemon()
            elif choice == "6":
                break

    def _schedule_task_menu(self) -> None:
        """Menu for scheduling a new task."""
        while True:
            # Clear screen
            self._clear_screen()

            # Display header
            self._display_header("Schedule New Task")

            # Get schedule type
            print("Schedule Type:")
            print("1. Daily")
            print("2. Weekly")
            print("3. Back")

            schedule_choice = self._get_input("\nEnter your choice (1-3): ", r"^[1-3]$")

            if schedule_choice == "3":
                break

            # Get task type
            print("\nTask Type:")
            print("1. Daily Summary")
            print("2. Weekly Summary")
            print("3. Analyze All Tickets")
            print("4. Update Views")
            print("5. Sentiment Report")
            print("6. Hardware Report")
            print("7. Pending Report")

            task_choice = self._get_input("\nEnter your choice (1-7): ", r"^[1-7]$")

            # Map task choice to task name
            task_map = {
                "1": "daily-summary",
                "2": "weekly-summary",
                "3": "analyze-all",
                "4": "update-views",
                "5": "sentiment-report",
                "6": "hardware-report",
                "7": "pending-report"
            }
            task_name = task_map.get(task_choice)

            # Get view ID if applicable
            view_id = None
            if task_name in ["sentiment-report", "hardware-report", "pending-report"]:
                view_id_str = self._get_input("\nEnter view ID (blank for all tickets): ", r"^\d*$")
                view_id = int(view_id_str) if view_id_str else None

            # Get schedule details
            if schedule_choice == "1":
                # Daily schedule
                time_str = self._get_input("\nEnter time (HH:MM, default: 00:00): ",
                                         r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$") or "00:00"

                # Parse time
                hour, minute = map(int, time_str.split(":"))

                # Get scheduler service
                scheduler_service = self.dependency_container.resolve('scheduler_service')

                try:
                    # Create parameters
                    params = {}
                    if view_id is not None:
                        params["view_id"] = view_id

                    # Schedule task
                    task_id = scheduler_service.schedule_daily_task(
                        task_name=task_name,
                        hour=hour,
                        minute=minute,
                        parameters=params
                    )

                    print(f"\nDaily task '{task_name}' scheduled at {time_str}.")
                    print(f"Task ID: {task_id}")
                    self._wait_for_input()
                    break

                except Exception as e:
                    print(f"\nError scheduling task: {e}")
                    self._wait_for_input()
                    continue
            else:
                # Weekly schedule
                day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                day_index = int(self._get_input("\nEnter day of week (1=Monday, 7=Sunday): ", r"^[1-7]$")) - 1
                day = day_options[day_index].lower()

                time_str = self._get_input("\nEnter time (HH:MM, default: 00:00): ",
                                         r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$") or "00:00"

                # Parse time
                hour, minute = map(int, time_str.split(":"))

                # Get scheduler service
                scheduler_service = self.dependency_container.resolve('scheduler_service')

                try:
                    # Create parameters
                    params = {}
                    if view_id is not None:
                        params["view_id"] = view_id

                    # Schedule task
                    task_id = scheduler_service.schedule_weekly_task(
                        task_name=task_name,
                        day=day,
                        hour=hour,
                        minute=minute,
                        parameters=params
                    )

                    print(f"\nWeekly task '{task_name}' scheduled on {day_options[day_index]} at {time_str}.")
                    print(f"Task ID: {task_id}")
                    self._wait_for_input()
                    break

                except Exception as e:
                    print(f"\nError scheduling task: {e}")
                    self._wait_for_input()
                    continue

    def _list_scheduled_tasks(self) -> None:
        """List all scheduled tasks."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Scheduled Tasks")

        # Get scheduler service
        scheduler_service = self.dependency_container.resolve('scheduler_service')

        try:
            # Get all tasks
            tasks = scheduler_service.list_tasks()

            if not tasks:
                print("No tasks scheduled.")
            else:
                for task in tasks:
                    # Get task details
                    task_id = task.get("id", "Unknown")
                    task_name = task.get("task", "Unknown")
                    schedule = task.get("schedule", "Unknown")
                    next_run = task.get("next_run", "Unknown")
                    enabled = task.get("enabled", True)
                    parameters = task.get("parameters", {})

                    # Format task details
                    print(f"ID: {task_id}")
                    print(f"Task: {task_name}")
                    print(f"Schedule: {schedule}")
                    print(f"Next Run: {next_run}")
                    print(f"Status: {'Enabled' if enabled else 'Disabled'}")

                    # Add parameters if available
                    if parameters:
                        print("Parameters:")
                        for key, value in parameters.items():
                            if value is not None:
                                print(f"  - {key}: {value}")

                    print()

            self._wait_for_input()

        except Exception as e:
            print(f"Error listing tasks: {e}")
            self._wait_for_input()

    def _remove_task(self) -> None:
        """Remove a scheduled task."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Remove Task")

        # Get task ID
        task_id = self._get_input("Enter task ID: ", r"^.+$")

        # Get scheduler service
        scheduler_service = self.dependency_container.resolve('scheduler_service')

        try:
            # Remove task
            success = scheduler_service.remove_task(task_id)

            if success:
                print(f"\nTask {task_id} removed successfully.")
            else:
                print(f"\nTask {task_id} not found.")

            self._wait_for_input()

        except Exception as e:
            print(f"\nError removing task: {e}")
            self._wait_for_input()

    def _start_scheduler_daemon(self) -> None:
        """Start the scheduler daemon."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Start Scheduler Daemon")

        # Get daemon options
        daemon_mode = self._yes_no_prompt("Run in daemon mode (background)?")

        # Get log file
        log_file = None
        if self._yes_no_prompt("Write logs to file?"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_log = f"scheduler_{timestamp}.log"
            log_file = self._get_input(f"Enter log file path (default: {default_log}): ", r"^.*$") or default_log

        # Get scheduler service
        scheduler_service = self.dependency_container.resolve('scheduler_service')

        try:
            # Start scheduler
            if daemon_mode:
                # Start in daemon mode
                pid_file = "scheduler.pid"
                pid = scheduler_service.start_daemon(pid_file, log_file)

                print(f"\nScheduler daemon started with PID {pid}")
                print(f"PID written to {pid_file}")
            else:
                # Start in interactive mode
                print("\nStarting scheduler in interactive mode...")
                print("Press Ctrl+C to stop")

                # Configure logging if needed
                if log_file:
                    # Add file handler
                    scheduler_log_handler = logging.FileHandler(log_file)
                    scheduler_log_handler.setFormatter(
                        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    )
                    logging.getLogger().addHandler(scheduler_log_handler)

                # Set a flag to indicate the scheduler is running
                self.scheduler_running = True

                # Start scheduler in a background thread
                import threading
                self.scheduler_thread = threading.Thread(
                    target=scheduler_service.start,
                    daemon=True
                )
                self.scheduler_thread.start()

                print("\nScheduler started.")

            self._wait_for_input()

        except Exception as e:
            print(f"\nError starting scheduler: {e}")
            self._wait_for_input()

    def _stop_scheduler_daemon(self) -> None:
        """Stop the scheduler daemon."""
        # Clear screen
        self._clear_screen()

        # Display header
        self._display_header("Stop Scheduler Daemon")

        # Check if daemon mode
        if os.path.exists("scheduler.pid"):
            # Daemon mode
            try:
                # Get scheduler service
                scheduler_service = self.dependency_container.resolve('scheduler_service')

                # Stop daemon
                success = scheduler_service.stop_daemon("scheduler.pid")

                if success:
                    print("\nScheduler daemon stopped successfully.")
                else:
                    print("\nFailed to stop scheduler daemon.")
            except Exception as e:
                print(f"\nError stopping scheduler daemon: {e}")
        elif hasattr(self, 'scheduler_running') and self.scheduler_running:
            # Interactive mode
            try:
                # Get scheduler service
                scheduler_service = self.dependency_container.resolve('scheduler_service')

                # Stop scheduler
                scheduler_service.stop()

                # Update flag
                self.scheduler_running = False

                print("\nScheduler stopped.")
            except Exception as e:
                print(f"\nError stopping scheduler: {e}")
        else:
            print("\nScheduler is not running.")

        self._wait_for_input()

    def _add_to_recent_views(self, view: Dict[str, Any]) -> None:
        """
        Add a view to the recent views list.

        Args:
            view: View to add
        """
        # Check if view is already in recent views
        for i, recent_view in enumerate(self.recent_views):
            if recent_view.get("id") == view.get("id"):
                # Move to the top
                self.recent_views.pop(i)
                self.recent_views.insert(0, view)
                return

        # Add to the top
        self.recent_views.insert(0, view)

        # Trim if necessary
        if len(self.recent_views) > self.max_recent_views:
            self.recent_views.pop()

    def _view_tickets_in_browser(self, view: Dict[str, Any]) -> None:
        """
        Open tickets in the browser.

        Args:
            view: View to open tickets from
        """
        view_id = view.get("id")

        # Generate Zendesk URL
        zendesk_domain = self._get_input("Enter your Zendesk domain (e.g., company.zendesk.com): ", r"^.+\.zendesk\.com$")
        url = f"https://{zendesk_domain}/agent/filters/{view_id}"

        # Open in browser
        import webbrowser
        webbrowser.open(url)

        print(f"\nOpening {url} in browser...")
        self._wait_for_input()

    def _add_comments_to_ticket(self, ticket_id: int, analysis) -> None:
        """
        Add analysis as comments to a ticket.

        Args:
            ticket_id: ID of the ticket
            analysis: Analysis results
        """
        # Get required services
        ticket_repository = self.dependency_container.resolve('ticket_repository')

        try:
            # Generate comment
            comment = "AI Analysis Results:\n\n"
            comment += f"Sentiment: {analysis.sentiment}\n"
            comment += f"Category: {analysis.category}\n"
            comment += f"Priority: {analysis.priority}\n"

            if hasattr(analysis, 'hardware_components') and analysis.hardware_components:
                comment += f"Hardware components: {', '.join(analysis.hardware_components)}\n"

            if hasattr(analysis, 'business_impact') and analysis.business_impact:
                comment += f"Business impact: {analysis.business_impact}\n"

            if hasattr(analysis, 'frustration_level') and analysis.frustration_level:
                comment += f"Frustration level: {analysis.frustration_level}/5\n"

            if hasattr(analysis, 'urgency') and analysis.urgency:
                comment += f"Urgency: {analysis.urgency}/5\n"

            # Add comment to ticket
            ticket_repository.add_private_comment(ticket_id, comment)

            print("\nAdded analysis as private comment to ticket.")

        except Exception as e:
            print(f"\nError adding comment to ticket: {e}")

    def _add_tags_to_ticket(self, ticket_id: int, analysis) -> None:
        """
        Add tags based on analysis to a ticket.

        Args:
            ticket_id: ID of the ticket
            analysis: Analysis results
        """
        # Get required services
        ticket_repository = self.dependency_container.resolve('ticket_repository')

        try:
            # Generate tags
            tags = []

            # Add sentiment tag
            if hasattr(analysis, 'sentiment') and analysis.sentiment:
                tags.append(f"sentiment:{analysis.sentiment.lower()}")

            # Add category tag
            if hasattr(analysis, 'category') and analysis.category:
                tags.append(f"category:{analysis.category.lower().replace(' ', '_')}")

            # Add priority tag
            if hasattr(analysis, 'priority') and analysis.priority:
                if analysis.priority >= 7:
                    tags.append("priority:high")
                elif analysis.priority >= 4:
                    tags.append("priority:medium")
                else:
                    tags.append("priority:low")

            # Add hardware tags
            if hasattr(analysis, 'hardware_components') and analysis.hardware_components:
                for component in analysis.hardware_components:
                    tags.append(f"hw:{component.lower()}")

            # Add business impact tag
            if hasattr(analysis, 'business_impact') and analysis.business_impact:
                tags.append("business_impact")

            # Add tags to ticket
            ticket_repository.add_tags(ticket_id, tags)

            print("\nAdded tags to ticket:")
            for tag in tags:
                print(f"  - {tag}")

        except Exception as e:
            print(f"\nError adding tags to ticket: {e}")

    def _clear_screen(self) -> None:
        """Clear the screen."""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    def _display_header(self, title: str) -> None:
        """
        Display a header.

        Args:
            title: Header title
        """
        print(title)
        print("=" * len(title))
        print()

    def _get_input(self, prompt: str, pattern: Optional[str] = None) -> str:
        """
        Get user input with optional validation.

        Args:
            prompt: Prompt to display
            pattern: Regular expression pattern to validate input

        Returns:
            User input
        """
        while True:
            user_input = input(prompt)

            if pattern is None or re.match(pattern, user_input):
                return user_input

            print("Invalid input. Please try again.")

    def _yes_no_prompt(self, prompt: str) -> bool:
        """
        Display a yes/no prompt.

        Args:
            prompt: Prompt to display

        Returns:
            True if user selected yes, False otherwise
        """
        while True:
            choice = input(f"{prompt} (y/n): ").lower()

            if choice in ["y", "yes"]:
                return True
            elif choice in ["n", "no"]:
                return False

            print("Invalid input. Please enter 'y' or 'n'.")

    def _select_from_options(self, prompt: str, options: List[str]) -> str:
        """
        Display a selection prompt.

        Args:
            prompt: Prompt to display
            options: List of options

        Returns:
            Selected option
        """
        print(prompt)

        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        while True:
            try:
                choice = input("\nEnter your choice: ")
                index = int(choice) - 1

                if 0 <= index < len(options):
                    return options[index]

                print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def _wait_for_input(self) -> None:
        """Wait for user input."""
        input("\nPress Enter to continue...")


class InteractiveCommand(Command):
    """Command for interactive mode."""

    @property
    def name(self) -> str:
        """Get the command name."""
        return "interactive"

    @property
    def description(self) -> str:
        """Get the command description."""
        return "Start interactive menu for easier navigation of Zendesk views and actions"

    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        # No additional arguments needed
        pass

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        logger.info("Starting interactive mode")

        try:
            # Create the interactive menu
            menu = InteractiveMenu(self.dependency_container)

            # Start the menu
            menu.start()

            return {"success": True}
        except KeyboardInterrupt:
            logger.info("Interactive mode interrupted by user")
            return {"success": True}
        except Exception as e:
            logger.exception(f"Error in interactive mode: {e}")
            print(f"Error in interactive mode: {e}")
            return {"success": False, "error": str(e)}
