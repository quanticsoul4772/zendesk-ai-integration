"""
Hardware Component Reporter Module

This module is responsible for generating reports about hardware components
mentioned in support tickets.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from zenpy.lib.api_objects import Ticket

# Set up logging
logger = logging.getLogger(__name__)

class HardwareReporter:
    """Generates reports about hardware components in tickets."""
    
    def __init__(self):
        """Initialize the reporter."""
        self.hardware_terms = {
            "gpu": ["gpu", "graphics card", "video card", "rtx", "gtx", "quadro", "nvidia", "radeon"],
            "cpu": ["cpu", "processor", "intel", "amd", "ryzen", "xeon", "threadripper", "core"],
            "memory": ["memory", "ram", "ddr", "dimm"],
            "drive": ["drive", "ssd", "hdd", "nvme", "storage", "disk"],
            "power_supply": ["power supply", "psu"],
            "motherboard": ["motherboard", "mobo", "mainboard"],
            "cooling": ["cooling", "fan", "heat sink", "thermal"],
            "display": ["display", "monitor", "screen"],
            "network": ["network", "ethernet", "wifi", "wireless", "lan"],
            "ipmi": ["ipmi", "remote management", "bmc"],
            "bios": ["bios", "uefi"],
            "boot": ["boot", "startup", "post"]
        }
    
    def extract_hardware_components(self, text: str) -> List[str]:
        """
        Extract hardware components from text based on keyword matching.
        
        Args:
            text: Text to analyze for hardware component mentions
            
        Returns:
            List of identified component types
        """
        if not text:
            return []
        
        components = []
        text_lower = text.lower()
        
        for component, terms in self.hardware_terms.items():
            for term in terms:
                if term in text_lower:
                    components.append(component)
                    break
        
        return list(set(components))
    
    def generate_report(self, tickets: List[Ticket]) -> str:
        """
        Generate hardware component report for a set of tickets.
        
        Args:
            tickets: List of Zendesk tickets to analyze
            
        Returns:
            String containing the formatted report
        """
        if not tickets:
            return "No tickets to analyze"
        
        # Count component mentions
        component_counts = {}
        ticket_details = []
        
        for ticket in tickets:
            # Extract components from ticket subject and description
            description = ticket.description or ""
            subject = ticket.subject or ""
            components = self.extract_hardware_components(subject + " " + description)
            
            # Track component counts
            for component in components:
                component_counts[component] = component_counts.get(component, 0) + 1
            
            # Add ticket details
            if components:
                ticket_details.append({
                    "id": ticket.id,
                    "subject": subject,
                    "components": ", ".join(components)
                })
        
        # Generate report
        report = "HARDWARE COMPONENT REPORT\n"
        report += "=======================\n\n"
        report += f"Total tickets analyzed: {len(tickets)}\n"
        report += f"Tickets with hardware components: {len(ticket_details)}\n\n"
        
        report += "COMPONENT DISTRIBUTION\n"
        report += "---------------------\n"
        for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"{component}: {count}\n"
        
        report += "\nTICKET DETAILS\n"
        report += "-------------\n"
        for detail in ticket_details:
            report += f"#{detail['id']} - {detail['subject']}\n"
            report += f"Components: {detail['components']}\n\n"
        
        return report
    
    def generate_multi_view_report(self, tickets: List[Ticket], view_map: Optional[Dict] = None) -> str:
        """
        Generate hardware component report for tickets from multiple views.
        
        Args:
            tickets: List of Zendesk tickets to analyze
            view_map: Dictionary mapping view IDs to view names
            
        Returns:
            String containing the formatted report
        """
        if not tickets:
            return "No tickets to analyze"
        
        # Group tickets by view
        view_tickets = {}
        for ticket in tickets:
            if hasattr(ticket, 'source_view_id'):
                view_id = getattr(ticket, 'source_view_id')
                if view_id not in view_tickets:
                    view_tickets[view_id] = []
                view_tickets[view_id].append(ticket)
            else:
                # If no view information, put in unknown category
                if 'unknown' not in view_tickets:
                    view_tickets['unknown'] = []
                view_tickets['unknown'].append(ticket)
        
        # Count component mentions overall
        overall_component_counts = {}
        view_component_counts = {}
        all_ticket_details = []
        
        for view_id, tickets_in_view in view_tickets.items():
            view_component_counts[view_id] = {}
            
            for ticket in tickets_in_view:
                # Extract components from ticket subject and description
                description = ticket.description or ""
                subject = ticket.subject or ""
                components = self.extract_hardware_components(subject + " " + description)
                
                # Add view information to ticket details
                view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
                
                # Track component counts overall
                for component in components:
                    overall_component_counts[component] = overall_component_counts.get(component, 0) + 1
                    view_component_counts[view_id][component] = view_component_counts[view_id].get(component, 0) + 1
                
                # Add ticket details
                if components:
                    all_ticket_details.append({
                        "id": ticket.id,
                        "subject": subject,
                        "components": ", ".join(components),
                        "view_id": view_id,
                        "view_name": view_name
                    })
        
        # Generate report
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"MULTI-VIEW HARDWARE COMPONENT REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        report += "OVERVIEW\n"
        report += "--------\n"
        report += f"Total tickets analyzed: {len(tickets)}\n"
        report += f"Tickets with hardware components: {len(all_ticket_details)}\n"
        report += f"Total views: {len(view_tickets)}\n\n"
        
        report += "TICKETS BY VIEW\n"
        report += "--------------\n"
        for view_id, tickets_in_view in view_tickets.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"{view_name}: {len(tickets_in_view)} tickets\n"
        report += "\n"
        
        report += "OVERALL COMPONENT DISTRIBUTION\n"
        report += "-----------------------------\n"
        for component, count in sorted(overall_component_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"{component}: {count}\n"
        report += "\n"
        
        report += "COMPONENT DISTRIBUTION BY VIEW\n"
        report += "------------------------------\n"
        for view_id, components in view_component_counts.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True):
                report += f"{component}: {count}\n"
        
        report += "\nTICKET DETAILS\n"
        report += "-------------\n"
        
        # Group ticket details by view for better readability
        for view_id in view_tickets.keys():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            tickets_in_view = [t for t in all_ticket_details if t["view_id"] == view_id]
            
            if tickets_in_view:
                report += f"\n{view_name}\n{'-' * len(view_name)}\n"
                for detail in tickets_in_view:
                    report += f"#{detail['id']} - {detail['subject']}\n"
                    report += f"Components: {detail['components']}\n\n"
        
        return report
    
    def save_report(self, report: str, filename: str = None) -> str:
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
            filename = f"hardware_report_{timestamp}.txt"
        
        try:
            with open(filename, "w") as file:
                file.write(report)
            logger.info(f"Hardware component report saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            return None
