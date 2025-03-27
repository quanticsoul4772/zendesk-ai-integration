"""
Pending Support Reporter Module

This module is responsible for generating reports about pending support tickets.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from zenpy.lib.api_objects import Ticket

# Set up logging
logger = logging.getLogger(__name__)

# Import hardware component extraction functionality
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reporters.hardware_report import HardwareReporter

class PendingReporter:
    """Generates reports about pending support tickets."""
    
    def __init__(self):
        """Initialize the reporter."""
        self.hardware_reporter = HardwareReporter()
    
    def generate_report(self, tickets: List[Ticket], view_name: Optional[str] = None) -> str:
        """
        Generate a comprehensive report of pending support tickets.
        
        Args:
            tickets: List of Zendesk tickets
            view_name: Name of the view (for report heading)
        
        Returns:
            Formatted report text.
        """
        if not tickets:
            return "No tickets found in this view."
        
        now = datetime.now()
        report = f"\n{'='*51}\n"
        report += f"PENDING SUPPORT TICKET REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*51}\n\n"
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total Tickets: {len(tickets)}\n"
        
        if view_name:
            report += f"Queue Purpose: New Support tickets waiting for assignment to agent\n"
            report += f"View: {view_name}\n\n"
        
        # Status distribution
        status_counts = {}
        for ticket in tickets:
            status = ticket.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        report += "STATUS DISTRIBUTION\n------------------\n"
        for status, count in sorted(status_counts.items()):
            report += f"{status}: {count}\n"
        report += "\n"
        
        # Priority distribution
        priority_counts = {}
        for ticket in tickets:
            priority = ticket.priority or "normal"
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        report += "PRIORITY DISTRIBUTION\n--------------------\n"
        for priority, count in sorted(priority_counts.items()):
            report += f"{priority}: {count}\n"
        report += "\n"
        
        # Hardware component distribution
        component_counts = {}
        for ticket in tickets:
            subject = ticket.subject or ""
            description = ticket.description or ""
            components = self.hardware_reporter.extract_hardware_components(subject + " " + description)
            for component in components:
                component_counts[component] = component_counts.get(component, 0) + 1
        
        if component_counts:
            report += "HARDWARE COMPONENT DISTRIBUTION\n-----------------------------\n"
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
                report += f"{component}: {count}\n"
            report += "\n"
        
        # Customer distribution
        customer_counts = {}
        for ticket in tickets:
            requester = ticket.requester
            if requester:
                name = getattr(requester, 'name', 'Unknown')
                customer_counts[name] = customer_counts.get(name, 0) + 1
        
        if customer_counts:
            report += "CUSTOMER DISTRIBUTION\n------------------\n"
            count = 0
            for customer, num in sorted(customer_counts.items(), key=lambda x: x[1], reverse=True):
                if count < 10:  # Limit to top 10
                    report += f"{customer}: {num}\n"
                count += 1
            report += "\n"
        
        # Ticket age
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        age_counts = {
            "Today": 0,
            "Yesterday": 0,
            "This Week": 0,
            "Older": 0
        }
        
        for ticket in tickets:
            created = None
            if ticket.created_at:
                # Handle the created_at field which might be a string or datetime
                if isinstance(ticket.created_at, str):
                    try:
                        # Convert string to datetime using standard format
                        created_dt = datetime.strptime(ticket.created_at, '%Y-%m-%dT%H:%M:%SZ')
                        created = created_dt.date()
                    except (ValueError, TypeError):
                        try:
                            # Try another common format
                            created_dt = datetime.strptime(ticket.created_at, '%Y-%m-%d %H:%M:%S')
                            created = created_dt.date()
                        except (ValueError, TypeError):
                            # If all parsing fails, set to None
                            created = None
                else:
                    # If it's already a datetime object
                    try:
                        created = ticket.created_at.date()
                    except (AttributeError, TypeError):
                        created = None
                    
            if created == today:
                age_counts["Today"] += 1
            elif created == yesterday:
                age_counts["Yesterday"] += 1
            elif created and created >= week_ago:
                age_counts["This Week"] += 1
            else:
                age_counts["Older"] += 1
        
        report += "TICKET AGE\n---------\n"
        for age, count in age_counts.items():
            report += f"{age}: {count}\n"
        report += "\n"
        
        # Ticket details
        report += "TICKET DETAILS\n-------------\n"
        for ticket in tickets:
            subject = ticket.subject or "No Subject"
            requester_name = getattr(ticket.requester, 'name', 'Unknown')
            requester_org = "No Organization"
            if ticket.organization is not None and hasattr(ticket.organization, 'name'):
                requester_org = ticket.organization.name
            
            # Handle created_at date formatting
            created = "Unknown"
            if ticket.created_at:
                if isinstance(ticket.created_at, str):
                    try:
                        # Convert string to datetime using standard format
                        created_dt = datetime.strptime(ticket.created_at, '%Y-%m-%dT%H:%M:%SZ')
                        created = created_dt.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        try:
                            # Try another common format
                            created_dt = datetime.strptime(ticket.created_at, '%Y-%m-%d %H:%M:%S')
                            created = created_dt.strftime('%Y-%m-%d %H:%M')
                        except (ValueError, TypeError):
                            created = ticket.created_at  # Use the string as is
                else:
                    try:
                        created = ticket.created_at.strftime('%Y-%m-%d %H:%M')
                    except (AttributeError, TypeError):
                        created = "Unknown"
            
            # Handle updated_at date formatting
            updated = "Unknown"
            if ticket.updated_at:
                if isinstance(ticket.updated_at, str):
                    try:
                        # Convert string to datetime using standard format
                        updated_dt = datetime.strptime(ticket.updated_at, '%Y-%m-%dT%H:%M:%SZ')
                        updated = updated_dt.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        try:
                            # Try another common format
                            updated_dt = datetime.strptime(ticket.updated_at, '%Y-%m-%d %H:%M:%S')
                            updated = updated_dt.strftime('%Y-%m-%d %H:%M')
                        except (ValueError, TypeError):
                            updated = ticket.updated_at  # Use the string as is
                else:
                    try:
                        updated = ticket.updated_at.strftime('%Y-%m-%d %H:%M')
                    except (AttributeError, TypeError):
                        updated = "Unknown"
            
            # Extract components
            subject_text = subject or ""
            description = ticket.description or ""
            components = self.hardware_reporter.extract_hardware_components(subject_text + " " + description)
            components_text = ", ".join(components) if components else ""
            
            report += f"#{ticket.id} - {subject} ({ticket.status})\n"
            report += f"Priority: {ticket.priority or 'normal'}\n"
            if components_text:
                report += f"Components: {components_text}\n"
            report += f"Requester: {requester_name} | Organization: {requester_org}\n"
            report += f"Created: {created}\n"
            report += f"Updated: {updated}\n"
            report += "-" * 40 + "\n"
        
        return report
    
    def save_report(self, report: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Save the report to a file.
        
        Args:
            report: Report content to save
            filename: Filename to use (if None, generates a timestamp-based name)
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"pending_support_report_{timestamp}.txt"
        
        try:
            with open(filename, "w") as file:
                file.write(report)
            logger.info(f"Pending support report saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            return None
