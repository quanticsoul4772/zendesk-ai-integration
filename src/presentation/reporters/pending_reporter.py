"""
Pending Reporter Implementation

This module provides an implementation of the PendingReporter interface.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket import Ticket
from src.domain.interfaces.reporter_interfaces import PendingReporter

# Set up logging
logger = logging.getLogger(__name__)


class PendingReporterImpl(PendingReporter):
    """
    Implementation of the PendingReporter interface.
    
    This reporter generates reports about pending tickets.
    """
    
    def generate_report(self, tickets: List[Ticket], **kwargs) -> str:
        """
        Generate a pending ticket report.
        
        Args:
            tickets: List of tickets to include in the report
            **kwargs: Additional arguments (view_name, format, etc.)
            
        Returns:
            Report text
        """
        view_name = kwargs.get('view_name', "Pending Tickets")
        
        # Calculate age distribution
        age_distribution = self.calculate_age_distribution(tickets)
        
        # Build the report
        report = f"Pending Ticket Report - {view_name}\n"
        report += f"{'-' * (len(view_name) + 22)}\n\n"
        
        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total pending tickets: {len(tickets)}\n\n"
        
        # Age distribution section
        report += "Age Distribution:\n"
        for age_range, count in age_distribution.items():
            percentage = (count / len(tickets)) * 100 if tickets else 0
            report += f"  - {age_range}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Oldest tickets section
        if tickets:
            report += "Oldest Pending Tickets:\n"
            # Sort by created_at, oldest first
            for ticket in sorted(tickets, key=lambda t: t.created_at)[:10]:
                age_days = ticket.age_in_days
                report += f"  - Ticket {ticket.id}: {ticket.subject}\n"
                report += f"    Age: {age_days} days, Created: {ticket.created_at.strftime('%Y-%m-%d')}\n"
        
        return report
    
    def generate_multi_view_report(self, tickets_by_view: Dict[str, List[Ticket]], **kwargs) -> str:
        """
        Generate a multi-view pending ticket report.
        
        Args:
            tickets_by_view: Dictionary mapping view names to lists of tickets
            **kwargs: Additional arguments
            
        Returns:
            Report text
        """
        # Build the report
        report = "Multi-View Pending Ticket Report\n"
        report += "-------------------------------\n\n"
        
        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total views: {len(tickets_by_view)}\n"
        
        # Calculate total tickets
        total_tickets = sum(len(tickets) for tickets in tickets_by_view.values())
        report += f"Total pending tickets: {total_tickets}\n\n"
        
        # Report for each view
        for view_name, view_tickets in tickets_by_view.items():
            report += f"View: {view_name}\n"
            report += f"{'-' * (len(view_name) + 6)}\n"
            report += f"Pending tickets: {len(view_tickets)}\n\n"
            
            # Age distribution for this view
            view_age_distribution = self.calculate_age_distribution(view_tickets)
            
            report += "Age Distribution:\n"
            for age_range, count in view_age_distribution.items():
                percentage = (count / len(view_tickets)) * 100 if view_tickets else 0
                report += f"  - {age_range}: {count} ({percentage:.1f}%)\n"
            
            # Oldest tickets for this view
            if view_tickets:
                report += "\nOldest Tickets:\n"
                # Sort by created_at, oldest first
                for ticket in sorted(view_tickets, key=lambda t: t.created_at)[:5]:
                    age_days = ticket.age_in_days
                    report += f"  - Ticket {ticket.id}: {ticket.subject}\n"
                    report += f"    Age: {age_days} days, Created: {ticket.created_at.strftime('%Y-%m-%d')}\n"
            
            report += "\n"
        
        return report
    
    def calculate_age_distribution(self, tickets: List[Ticket]) -> Dict[str, int]:
        """
        Calculate age distribution of pending tickets.
        
        Args:
            tickets: List of tickets
            
        Returns:
            Dictionary mapping age ranges to counts
        """
        distribution = {
            "< 1 day": 0,
            "1-2 days": 0,
            "3-7 days": 0,
            "1-2 weeks": 0,
            "2-4 weeks": 0,
            "> 4 weeks": 0
        }
        
        for ticket in tickets:
            age_days = ticket.age_in_days
            
            if age_days < 1:
                distribution["< 1 day"] += 1
            elif age_days < 3:
                distribution["1-2 days"] += 1
            elif age_days < 8:
                distribution["3-7 days"] += 1
            elif age_days < 15:
                distribution["1-2 weeks"] += 1
            elif age_days < 29:
                distribution["2-4 weeks"] += 1
            else:
                distribution["> 4 weeks"] += 1
        
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
            filename = f"pending_report_{timestamp}.txt"
        
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
