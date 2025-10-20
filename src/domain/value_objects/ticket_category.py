"""
Ticket Category Value Object

This module defines the TicketCategory value object, which represents the category of a Zendesk ticket.
"""

from enum import Enum


class TicketCategory(str, Enum):
    """Represents the category of a Zendesk ticket."""
    SYSTEM = "system"
    RESALE_COMPONENT = "resale_component"
    HARDWARE_ISSUE = "hardware_issue"
    SYSTEM_COMPONENT = "system_component"
    SO_RELEASED_TO_WAREHOUSE = "so_released_to_warehouse"
    WO_RELEASED_TO_WAREHOUSE = "wo_released_to_warehouse"
    TECHNICAL_SUPPORT = "technical_support"
    RMA = "rma"
    SOFTWARE_ISSUE = "software_issue"
    GENERAL_INQUIRY = "general_inquiry"
    UNCATEGORIZED = "uncategorized"

    @classmethod
    def from_string(cls, category_str: str) -> 'TicketCategory':
        """
        Create a TicketCategory from a string.

        Args:
            category_str: String representation of the category

        Returns:
            TicketCategory enum value
        """
        if not category_str:
            return cls.UNCATEGORIZED

        normalized = category_str.lower().replace(" ", "_").strip()

        try:
            return cls(normalized)
        except ValueError:
            # Try partial matching
            for category in cls:
                if normalized in category.value:
                    return category

            # If no match, return uncategorized
            return cls.UNCATEGORIZED

    def get_description(self) -> str:
        """
        Get a description of the category.

        Returns:
            Human-readable description of the category
        """
        descriptions = {
            self.SYSTEM: "Issues related to complete computer systems",
            self.RESALE_COMPONENT: "Issues with components being resold",
            self.HARDWARE_ISSUE: "Problems with physical hardware components",
            self.SYSTEM_COMPONENT: "Issues specific to system components",
            self.SO_RELEASED_TO_WAREHOUSE: "Sales order released to warehouse status",
            self.WO_RELEASED_TO_WAREHOUSE: "Work order released to warehouse status",
            self.TECHNICAL_SUPPORT: "General technical assistance requests",
            self.RMA: "Return merchandise authorization requests",
            self.SOFTWARE_ISSUE: "Problems with software, OS or drivers",
            self.GENERAL_INQUIRY: "Information seeking that doesn't fit other categories",
            self.UNCATEGORIZED: "Ticket that has not been categorized"
        }

        return descriptions.get(self, "Unknown category")

    def is_hardware_related(self) -> bool:
        """
        Check if the category is hardware-related.

        Returns:
            True if hardware-related, False otherwise
        """
        hardware_categories = [
            self.SYSTEM,
            self.RESALE_COMPONENT,
            self.HARDWARE_ISSUE,
            self.SYSTEM_COMPONENT,
            self.RMA
        ]

        return self in hardware_categories

    def is_software_related(self) -> bool:
        """
        Check if the category is software-related.

        Returns:
            True if software-related, False otherwise
        """
        return self == self.SOFTWARE_ISSUE

    def is_order_related(self) -> bool:
        """
        Check if the category is order-related.

        Returns:
            True if order-related, False otherwise
        """
        order_categories = [
            self.SO_RELEASED_TO_WAREHOUSE,
            self.WO_RELEASED_TO_WAREHOUSE
        ]

        return self in order_categories
