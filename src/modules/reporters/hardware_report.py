"""
Hardware Reporter Module

Generates reports about hardware components mentioned in tickets.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from .reporter_base import ReporterBase

# Set up logging
logger = logging.getLogger(__name__)

class HardwareReporter(ReporterBase):
    """
    Generates reports focused on hardware components mentioned in tickets.
    """
    
    def __init__(self):
        """Initialize the hardware reporter."""
        # Initialize the parent class
        super().__init__()
        
        # Define component categories
        self.component_categories = {
            'gpu': 'Graphics Processing',
            'cpu': 'Processing',
            'memory': 'Memory',
            'ram': 'Memory',
            'drive': 'Storage',
            'ssd': 'Storage',
            'hdd': 'Storage',
            'nvme': 'Storage',
            'motherboard': 'System Board',
            'power_supply': 'Power',
            'psu': 'Power',
            'cooling': 'Thermal',
            'fan': 'Thermal',
            'display': 'Display',
            'monitor': 'Display',
            'network': 'Connectivity',
            'ethernet': 'Connectivity',
            'keyboard': 'Input',
            'mouse': 'Input'
        }
    
    def generate_report(self, tickets=None, **kwargs):
        """Generate a hardware component report."""
        # Check if we're being called with tickets directly
        if tickets and isinstance(tickets, list):
            # Process tickets directly
            return self._generate_hardware_report_from_tickets(tickets)
            
        # For backwards compatibility - just return a placeholder
        return "No hardware component data found."
    
    def _generate_report_content(self, analyses, title=None):
        """Generate the hardware report content."""
        # Create the report header
        report = f"\n{'='*60}\n"
        report += f"HARDWARE COMPONENT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Analyze component distribution
        component_distribution = self._analyze_component_distribution(analyses)
        
        # Format component distribution section
        report += self._format_component_distribution(component_distribution)
        
        # Add ticket details section
        report += "\nTICKET DETAILS\n-------------\n"
        for analysis in analyses:
            report += self._format_ticket_details(analysis) + "\n"
        
        return report
    
    def _analyze_component_distribution(self, analyses):
        """Count hardware components mentioned in analyses."""
        components = {}
        total_tickets = len(analyses)
        
        # Count component mentions
        for analysis in analyses:
            component = analysis.get('component', 'none')
            if component != 'none':
                components[component] = components.get(component, 0) + 1
                
        # Calculate percentages
        component_percentages = {}
        for component, count in components.items():
            component_percentages[component] = (count / total_tickets) * 100
            
        return {
            'counts': components,
            'percentages': component_percentages,
            'total_tickets': total_tickets
        }
    
    def _format_component_distribution(self, distribution):
        """Format the component distribution section."""
        section = "COMPONENT DISTRIBUTION\n---------------------\n"
        
        # If no components found
        if not distribution['counts']:
            section += "No hardware components detected in ticket analyses.\n"
            return section
            
        # Sort components by count (descending)
        sorted_components = sorted(
            distribution['counts'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Format each component with count and percentage
        for component, count in sorted_components:
            percentage = distribution['percentages'][component]
            # Get category if available
            category = self.component_categories.get(component, 'Other')
            section += f"{component} ({category}): {count} tickets ({percentage:.1f}%)\n"
            
        return section
    
    def _format_ticket_details(self, analysis):
        """Format details for a single ticket."""
        ticket_id = analysis.get('ticket_id', 'Unknown')
        subject = analysis.get('subject', 'No Subject')
        component = analysis.get('component', 'none')
        category = analysis.get('category', 'uncategorized')
        
        # Format basic ticket info
        ticket_info = f"#{ticket_id} - {subject}\n"
        
        # Add component if available
        if component != 'none':
            component_category = self.component_categories.get(component, 'Other')
            ticket_info += f"  Component: {component} ({component_category})\n"
            
        # Add category
        ticket_info += f"  Category: {category}\n"
        
        return ticket_info
        
    def _generate_hardware_report_from_tickets(self, tickets):
        """Generate a hardware report directly from a list of tickets."""
        # Create the report header
        report = f"\n{'='*60}\n"
        report += f"HARDWARE COMPONENT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'='*60}\n\n"
        
        # Add ticket count
        report += f"Analyzed {len(tickets)} tickets\n\n"
        
        # Simple component distribution based on ticket descriptions
        component_counts = {}
        for ticket in tickets:
            description = ticket.description or ""
            subject = ticket.subject or ""
            text = (description + " " + subject).lower()
            
            # Check for hardware components
            for component in self.component_categories.keys():
                if component in text:
                    if component not in component_counts:
                        component_counts[component] = 0
                    component_counts[component] += 1
        
        # Add component distribution section
        report += "COMPONENT DISTRIBUTION\n---------------------\n"
        if component_counts:
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
                category = self.component_categories.get(component, 'Other')
                percentage = (count / len(tickets)) * 100
                report += f"{component} ({category}): {count} tickets ({percentage:.1f}%)\n"
        else:
            report += "No hardware components detected in tickets.\n"
            
        return report

    def generate_multi_view_report(self, tickets, view_map=None):
        """Generate a hardware report for tickets from multiple views."""
        # Create the report header
        report = f"\n{'='*60}\n"
        report += f"MULTI-VIEW HARDWARE COMPONENT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'='*60}\n\n"
        
        # Add ticket count
        report += f"Analyzed {len(tickets)} tickets from {len(view_map) if view_map else 'multiple'} views\n\n"
        
        # Group tickets by view
        tickets_by_view = {}
        for ticket in tickets:
            view_id = getattr(ticket, 'source_view_id', 'unknown')
            if view_id not in tickets_by_view:
                tickets_by_view[view_id] = []
            tickets_by_view[view_id].append(ticket)
        
        # Get overall component distribution
        component_counts = {}
        for ticket in tickets:
            description = ticket.description or ""
            subject = ticket.subject or ""
            text = (description + " " + subject).lower()
            
            # Check for hardware components
            for component in self.component_categories.keys():
                if component in text:
                    if component not in component_counts:
                        component_counts[component] = 0
                    component_counts[component] += 1
        
        # Add overall component distribution section
        report += "OVERALL COMPONENT DISTRIBUTION\n----------------------------\n"
        if component_counts:
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
                category = self.component_categories.get(component, 'Other')
                percentage = (count / len(tickets)) * 100
                report += f"{component} ({category}): {count} tickets ({percentage:.1f}%)\n"
        else:
            report += "No hardware components detected in tickets.\n"
        
        # Add per-view component distribution
        report += "\nCOMPONENT DISTRIBUTION BY VIEW\n-----------------------------\n"
        for view_id, view_tickets in tickets_by_view.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"\n{view_name} ({len(view_tickets)} tickets)\n{'-' * (len(view_name) + len(str(len(view_tickets))) + 11)}\n"
            
            # Get component distribution for this view
            view_component_counts = {}
            for ticket in view_tickets:
                description = ticket.description or ""
                subject = ticket.subject or ""
                text = (description + " " + subject).lower()
                
                # Check for hardware components
                for component in self.component_categories.keys():
                    if component in text:
                        if component not in view_component_counts:
                            view_component_counts[component] = 0
                        view_component_counts[component] += 1
            
            # Add component distribution for this view
            if view_component_counts:
                for component, count in sorted(view_component_counts.items(), key=lambda x: x[1], reverse=True):
                    category = self.component_categories.get(component, 'Other')
                    percentage = (count / len(view_tickets)) * 100
                    report += f"{component} ({category}): {count} tickets ({percentage:.1f}%)\n"
            else:
                report += "No hardware components detected in tickets.\n"
        
        return report
