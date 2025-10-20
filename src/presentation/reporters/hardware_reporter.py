"""
Hardware Reporter Implementation

This module provides an implementation of the HardwareReporter interface.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.entities.ticket import Ticket
from src.domain.interfaces.reporter_interfaces import HardwareReporter

# Set up logging
logger = logging.getLogger(__name__)


class HardwareReporterImpl(HardwareReporter):
    """
    Implementation of the HardwareReporter interface.

    This reporter generates reports about hardware components in tickets.
    """

    def generate_report(self, tickets: List[Ticket], **kwargs) -> str:
        """
        Generate a hardware component report.

        Args:
            tickets: List of tickets to include in the report
            **kwargs: Additional arguments (title, format, etc.)

        Returns:
            Report text
        """
        title = kwargs.get('title', "Hardware Component Report")
        format_type = kwargs.get('format', 'text')

        # Calculate component distribution
        component_distribution = self.calculate_component_distribution(tickets)

        if format_type == 'html':
            return self._generate_html_report(tickets, component_distribution, title)
        else:
            return self._generate_text_report(tickets, component_distribution, title)

    def _generate_text_report(self, tickets: List[Ticket], component_distribution: Dict[str, int], title: str) -> str:
        """Generate a text-formatted report."""
        # Build the report
        report = f"{title}\n"
        report += f"{'-' * len(title)}\n\n"

        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total tickets analyzed: {len(tickets)}\n\n"

        # Component distribution section
        report += "Component Distribution:\n"
        for component, count in sorted(component_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(tickets)) * 100 if tickets else 0
            report += f"  - {component.capitalize()}: {count} ({percentage:.1f}%)\n"
        report += "\n"

        # Recent tickets section
        # Check if ticket is open based on status (not solved or closed)
        open_tickets = [t for t in tickets if t.status and t.status.lower() not in ['solved', 'closed']]
        if open_tickets:
            report += "Recent Open Tickets:\n"
            # Define a sorting function that handles different created_at formats
            def sort_by_created_at(ticket):
                if not ticket.created_at:
                    return datetime.min  # Return earliest possible date for None
                if isinstance(ticket.created_at, datetime):
                    return ticket.created_at
                if isinstance(ticket.created_at, str):
                    try:
                        # Try to parse the ISO format string
                        return datetime.fromisoformat(ticket.created_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # If parsing fails, return a default date
                        return datetime.min
                return datetime.min

            # Sort by created_at, newest first
            sorted_tickets = sorted(open_tickets, key=sort_by_created_at, reverse=True)[:10]
            for ticket in sorted_tickets:
                report += f"  - Ticket {ticket.id}: {ticket.subject}\n"
                # Handle the case where created_at might be a string or a datetime
                created_at_str = ticket.created_at
                if hasattr(ticket.created_at, 'strftime'):
                    created_at_str = ticket.created_at.strftime('%Y-%m-%d')
                report += f"    Status: {ticket.status}, Created: {created_at_str}\n"

        return report

    def _generate_html_report(self, tickets: List[Ticket], component_distribution: Dict[str, int], title: str) -> str:
        """Generate an HTML-formatted report."""
        # Get the view name if available
        view_name = ""
        if tickets and hasattr(tickets[0], 'source_view_name') and tickets[0].source_view_name:
            view_name = tickets[0].source_view_name

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 20px;
        }}
        .meta-info {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .component-distribution {{
            margin-bottom: 20px;
        }}
        .component-bar {{
            display: flex;
            margin-bottom: 10px;
            align-items: center;
        }}
        .component-name {{
            width: 150px;
            font-weight: bold;
        }}
        .component-count {{
            width: 80px;
            text-align: right;
            padding-right: 10px;
        }}
        .bar-container {{
            flex-grow: 1;
            background-color: #ecf0f1;
            height: 20px;
            border-radius: 4px;
            overflow: hidden;
        }}
        .bar {{
            height: 100%;
            background-color: #3498db;
        }}
        .tickets-list {{
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .ticket {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .ticket:last-child {{
            border-bottom: none;
        }}
        .ticket-header {{
            display: flex;
            justify-content: space-between;
        }}
        .ticket-id {{
            font-weight: bold;
            color: #3498db;
        }}
        .ticket-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .component-unknown {{
            background-color: #95a5a6;
        }}
        .component-gpu {{
            background-color: #e74c3c;
        }}
        .component-cpu {{
            background-color: #2ecc71;
        }}
        .component-memory {{
            background-color: #f39c12;
        }}
        .component-drive {{
            background-color: #9b59b6;
        }}
        .component-power_supply {{
            background-color: #1abc9c;
        }}
        .component-motherboard {{
            background-color: #34495e;
        }}
        .component-cooling {{
            background-color: #3498db;
        }}
        .component-network {{
            background-color: #e67e22;
        }}
        .component-other {{
            background-color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="meta-info">
        <p><strong>Report generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total tickets analyzed:</strong> {len(tickets)}</p>"""

        if view_name:
            html += f"\n            <p><strong>View:</strong> {view_name}</p>"

        html += "\n        </div>\n\n"

        # Component legend
        html += """        <div class="component-legend">
            <div class="legend-item"><div class="legend-color component-gpu"></div> GPU</div>
            <div class="legend-item"><div class="legend-color component-cpu"></div> CPU</div>
            <div class="legend-item"><div class="legend-color component-memory"></div> Memory</div>
            <div class="legend-item"><div class="legend-color component-drive"></div> Drive</div>
            <div class="legend-item"><div class="legend-color component-power_supply"></div> Power Supply</div>
            <div class="legend-item"><div class="legend-color component-motherboard"></div> Motherboard</div>
            <div class="legend-item"><div class="legend-color component-cooling"></div> Cooling</div>
            <div class="legend-item"><div class="legend-color component-network"></div> Network</div>
            <div class="legend-item"><div class="legend-color component-other"></div> Other</div>
            <div class="legend-item"><div class="legend-color component-unknown"></div> Unknown</div>
        </div>
        """

        # Component distribution section
        html += "        <h2>Component Distribution</h2>\n"
        html += "        <div class=\"component-distribution\">\n"

        # Get max count for scaling bars
        max_count = max(component_distribution.values()) if component_distribution else 1

        for component, count in sorted(component_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(tickets)) * 100 if tickets else 0
            bar_width = (count / max_count) * 100

            html += f"""            <div class="component-bar">
                <div class="component-name">{component.capitalize()}</div>
                <div class="component-count">{count} ({percentage:.1f}%)</div>
                <div class="bar-container">
                    <div class="bar component-{component}" style="width: {bar_width}%"></div>
                </div>
            </div>
"""

        html += "        </div>\n\n"

        # Recent tickets section
        # Check if ticket is open based on status (not solved or closed)
        open_tickets = [t for t in tickets if t.status and t.status.lower() not in ['solved', 'closed']]
        if open_tickets:
            html += "        <h2>Recent Open Tickets</h2>\n"
            html += "        <div class=\"tickets-list\">\n"

            # Define a sorting function that handles different created_at formats
            def sort_by_created_at(ticket):
                if not ticket.created_at:
                    return datetime.min
                if isinstance(ticket.created_at, datetime):
                    return ticket.created_at
                if isinstance(ticket.created_at, str):
                    try:
                        return datetime.fromisoformat(ticket.created_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return datetime.min
                return datetime.min

            # Sort by created_at, newest first
            sorted_tickets = sorted(open_tickets, key=sort_by_created_at, reverse=True)[:10]

            for ticket in sorted_tickets:
                # Handle the case where created_at might be a string or a datetime
                created_at_str = ticket.created_at
                if hasattr(ticket.created_at, 'strftime'):
                    created_at_str = ticket.created_at.strftime('%Y-%m-%d')

                # Find the main component in the subject line
                ticket_component = "unknown"
                component_keywords = {
                    "gpu": ["gpu", "graphics", "video card", "rtx", "gtx", "radeon"],
                    "cpu": ["cpu", "processor", "ryzen", "intel", "amd"],
                    "memory": ["memory", "ram", "dimm", "ddr"],
                    "drive": ["drive", "ssd", "hdd", "nvme", "storage"],
                    "power_supply": ["power", "psu", "supply"],
                    "motherboard": ["motherboard", "mobo", "mainboard"],
                    "cooling": ["cooling", "fan", "heat", "thermal", "temperature"],
                    "network": ["network", "ethernet", "wifi", "wireless"],
                    "other": ["case", "chassis", "keyboard", "mouse", "monitor", "display"]
                }

                for component, keywords in component_keywords.items():
                    if any(keyword in ticket.subject.lower() for keyword in keywords):
                        ticket_component = component
                        break

                status_class = ""
                if ticket.status:
                    lower_status = ticket.status.lower()
                    if lower_status == "open":
                        status_class = "status-open"
                    elif lower_status == "new":
                        status_class = "status-new"
                    elif lower_status == "pending":
                        status_class = "status-pending"

                html += f"""            <div class="ticket">
                <div class="ticket-header">
                    <div class="ticket-id">Ticket {ticket.id}</div>
                    <div class="ticket-status {status_class}">{ticket.status.capitalize() if ticket.status else "Unknown"}</div>
                </div>
                <div class="ticket-subject">{ticket.subject}</div>
                <div class="ticket-meta">Created: {created_at_str} | Component: {ticket_component.capitalize()}</div>
            </div>
"""

            html += "        </div>\n"

        html += "    </div>\n</body>\n</html>"

        return html

    def generate_multi_view_report(self, tickets: List[Ticket], view_map: Dict[int, str], title: str = "Multi-View Hardware Component Report", **kwargs) -> str:
        """
        Generate a multi-view hardware component report.

        Args:
            tickets: List of tickets to include in the report
            view_map: Dictionary mapping view IDs to view names
            title: Report title
            **kwargs: Additional arguments (format, etc.)

        Returns:
            Report text
        """
        # Get format type from kwargs
        format_type = kwargs.get('format', 'text')

        # Group tickets by view
        tickets_by_view: Dict[int, List[Ticket]] = {}
        for ticket in tickets:
            if hasattr(ticket, 'source_view_id') and ticket.source_view_id is not None:
                if ticket.source_view_id not in tickets_by_view:
                    tickets_by_view[ticket.source_view_id] = []
                tickets_by_view[ticket.source_view_id].append(ticket)

        # Generate the appropriate format
        if format_type == 'html':
            return self._generate_multi_view_html_report(tickets_by_view, view_map, title)
        else:
            return self._generate_multi_view_text_report(tickets_by_view, view_map, title)

    def _generate_multi_view_text_report(self, tickets_by_view: Dict[int, List[Ticket]], view_map: Dict[int, str], title: str) -> str:
        """Generate a text-formatted multi-view report."""
        # Build the report
        report = f"{title}\n"
        report += f"{'-' * len(title)}\n\n"

        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total views: {len(tickets_by_view)}\n"

        # Count total tickets
        total_tickets = sum(len(view_tickets) for view_tickets in tickets_by_view.values())
        report += f"Total tickets analyzed: {total_tickets}\n\n"

        # Overall component distribution
        all_tickets = [ticket for tickets in tickets_by_view.values() for ticket in tickets]
        component_distribution = self.calculate_component_distribution(all_tickets)

        report += "Overall Component Distribution:\n"
        for component, count in sorted(component_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_tickets) * 100 if total_tickets else 0
            report += f"  - {component.capitalize()}: {count} ({percentage:.1f}%)\n"
        report += "\n"

        # Report for each view
        for view_id, view_tickets in tickets_by_view.items():
            view_name = view_map.get(view_id, f"View {view_id}")

            report += f"View: {view_name}\n"
            report += f"{'-' * (len(view_name) + 6)}\n"
            report += f"Tickets analyzed: {len(view_tickets)}\n\n"

            # Component distribution for this view
            view_component_distribution = self.calculate_component_distribution(view_tickets)

            report += "Component Distribution:\n"
            for component, count in sorted(view_component_distribution.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(view_tickets)) * 100 if view_tickets else 0
                report += f"  - {component.capitalize()}: {count} ({percentage:.1f}%)\n"
            report += "\n"

        return report

    def _generate_multi_view_html_report(self, tickets_by_view: Dict[int, List[Ticket]], view_map: Dict[int, str], title: str) -> str:
        """Generate an HTML-formatted multi-view report."""
        # Count total tickets
        total_tickets = sum(len(view_tickets) for view_tickets in tickets_by_view.values())

        # Calculate overall component distribution
        all_tickets = [ticket for tickets in tickets_by_view.values() for ticket in tickets]
        overall_distribution = self.calculate_component_distribution(all_tickets)

        # Get max count for scaling bars
        max_overall_count = max(overall_distribution.values()) if overall_distribution else 1

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f5f7fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }}
        h3 {{
            color: #3498db;
            margin-top: 25px;
        }}
        .meta-info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 25px;
            border-left: 4px solid #3498db;
        }}
        .component-distribution {{
            margin-bottom: 30px;
        }}
        .component-bar {{
            display: flex;
            margin-bottom: 12px;
            align-items: center;
        }}
        .component-name {{
            width: 150px;
            font-weight: bold;
        }}
        .component-count {{
            width: 120px;
            text-align: right;
            padding-right: 15px;
        }}
        .bar-container {{
            flex-grow: 1;
            background-color: #ecf0f1;
            height: 24px;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }}
        .bar {{
            height: 100%;
            transition: width 0.8s ease;
        }}
        .view-section {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 5px solid #3498db;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        .view-title {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .view-count {{
            background-color: #3498db;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.9em;
        }}
        .component-legend {{
            display: flex;
            flex-wrap: wrap;
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        .summary {{
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 6px;
            margin-top: 30px;
            border-left: 4px solid #2980b9;
        }}

        /* Component color classes */
        .component-unknown {{ background-color: #95a5a6; }}
        .component-gpu {{ background-color: #e74c3c; }}
        .component-cpu {{ background-color: #2ecc71; }}
        .component-memory {{ background-color: #f39c12; }}
        .component-drive {{ background-color: #9b59b6; }}
        .component-power_supply {{ background-color: #1abc9c; }}
        .component-motherboard {{ background-color: #34495e; color: white; }}
        .component-cooling {{ background-color: #3498db; }}
        .component-network {{ background-color: #e67e22; }}
        .component-other {{ background-color: #7f8c8d; }}

        @media (max-width: 768px) {{
            .component-bar {{
                flex-direction: column;
                align-items: flex-start;
                margin-bottom: 20px;
            }}
            .component-name, .component-count {{
                width: 100%;
                text-align: left;
                padding-right: 0;
                margin-bottom: 5px;
            }}
            .bar-container {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="meta-info">
            <p><strong>Report generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total views analyzed:</strong> {len(tickets_by_view)}</p>
            <p><strong>Total tickets analyzed:</strong> {total_tickets}</p>
        </div>

        <!-- Component Legend -->
        <div class="component-legend">
            <div class="legend-item"><div class="legend-color component-gpu"></div> GPU</div>
            <div class="legend-item"><div class="legend-color component-cpu"></div> CPU</div>
            <div class="legend-item"><div class="legend-color component-memory"></div> Memory</div>
            <div class="legend-item"><div class="legend-color component-drive"></div> Drive</div>
            <div class="legend-item"><div class="legend-color component-power_supply"></div> Power Supply</div>
            <div class="legend-item"><div class="legend-color component-motherboard"></div> Motherboard</div>
            <div class="legend-item"><div class="legend-color component-cooling"></div> Cooling</div>
            <div class="legend-item"><div class="legend-color component-network"></div> Network</div>
            <div class="legend-item"><div class="legend-color component-other"></div> Other</div>
            <div class="legend-item"><div class="legend-color component-unknown"></div> Unknown</div>
        </div>

        <h2>Overall Component Distribution</h2>
        <div class="component-distribution">"""

        # Overall component distribution bars
        for component, count in sorted(overall_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_tickets) * 100 if total_tickets else 0
            bar_width = (count / max_overall_count) * 100

            html += f"""            <div class="component-bar">
                <div class="component-name">{component.capitalize()}</div>
                <div class="component-count">{count} ({percentage:.1f}%)</div>
                <div class="bar-container">
                    <div class="bar component-{component}" style="width: {bar_width}%"></div>
                </div>
            </div>
"""

        html += "        </div>\n\n"

        # Individual view sections
        html += "        <h2>View-Specific Analysis</h2>\n"

        for view_id, view_tickets in tickets_by_view.items():
            view_name = view_map.get(view_id, f"View {view_id}")

            html += f"""        <div class="view-section">
            <div class="view-title">
                <h3>{view_name}</h3>
                <div class="view-count">{len(view_tickets)} tickets</div>
            </div>
"""

            # Component distribution for this view
            view_distribution = self.calculate_component_distribution(view_tickets)

            # Get max count for scaling bars
            max_view_count = max(view_distribution.values()) if view_distribution else 1

            html += "            <div class=\"component-distribution\">\n"

            for component, count in sorted(view_distribution.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(view_tickets)) * 100 if view_tickets else 0
                bar_width = (count / max_view_count) * 100

                html += f"""                <div class="component-bar">
                    <div class="component-name">{component.capitalize()}</div>
                    <div class="component-count">{count} ({percentage:.1f}%)</div>
                    <div class="bar-container">
                        <div class="bar component-{component}" style="width: {bar_width}%"></div>
                    </div>
                </div>
"""

            html += "            </div>\n"
            html += "        </div>\n"

        # Add summary section
        html += """        <div class="summary">
            <h2>Summary</h2>
            <p>This report shows the distribution of hardware components across different support views. The most common components across all views are:</p>
            <ul>
"""

        # Add top 3 components to summary
        for component, count in sorted(overall_distribution.items(), key=lambda x: x[1], reverse=True)[:3]:
            percentage = (count / total_tickets) * 100 if total_tickets else 0
            html += f"                <li><strong>{component.capitalize()}:</strong> {count} tickets ({percentage:.1f}%)</li>\n"

        html += """            </ul>
        </div>
    </div>
</body>
</html>"""

        return html

    def calculate_component_distribution(self, tickets: List[Ticket]) -> Dict[str, int]:
        """
        Calculate component distribution.

        Args:
            tickets: List of tickets

        Returns:
            Dictionary mapping component types to counts
        """
        distribution: Dict[str, int] = {}

        # Extract component information from ticket tags, subject, and description
        # This is a simplified version - in a real implementation, we would use the
        # AI service to extract the component information from the ticket content

        # For this example, we'll just check for common component keywords in the subject
        component_keywords = {
            "gpu": ["gpu", "graphics", "video card", "rtx", "gtx", "radeon"],
            "cpu": ["cpu", "processor", "ryzen", "intel", "amd"],
            "memory": ["memory", "ram", "dimm", "ddr"],
            "drive": ["drive", "ssd", "hdd", "nvme", "storage"],
            "power_supply": ["power", "psu", "supply"],
            "motherboard": ["motherboard", "mobo", "mainboard"],
            "cooling": ["cooling", "fan", "heat", "thermal", "temperature"],
            "network": ["network", "ethernet", "wifi", "wireless"],
            "other": ["case", "chassis", "keyboard", "mouse", "monitor", "display"]
        }

        for ticket in tickets:
            found_component = False

            for component, keywords in component_keywords.items():
                if any(keyword in ticket.subject.lower() for keyword in keywords):
                    distribution[component] = distribution.get(component, 0) + 1
                    found_component = True
                    break

            if not found_component:
                distribution["unknown"] = distribution.get("unknown", 0) + 1

        return distribution

    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """
        Save a report to a file.

        Args:
            report: Report text
            filename: Optional filename (default: auto-generated)

        Returns:
            Path to the saved report file
        """
        if not filename:
            # Generate a filename based on the current date and time
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"hardware_report_{timestamp}.txt"

        try:
            # Ensure the reports directory exists
            reports_dir = os.environ.get("REPORTS_DIR", "reports")
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            # Save the report to the file
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"Saved report to {filepath}")

            return filepath
        except Exception as e:
            logger.error(f"Error saving report to {filename}: {str(e)}")

            # Try to save in the current directory as a fallback
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)

                logger.info(f"Saved report to {filename} in current directory")

                return filename
            except Exception as e2:
                logger.error(f"Error saving report to current directory: {str(e2)}")
                return ""
