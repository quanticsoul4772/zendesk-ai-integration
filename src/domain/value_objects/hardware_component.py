"""
Hardware Component Value Object

This module defines the HardwareComponent value object, which represents a hardware component type.
"""

from enum import Enum


class HardwareComponent(str, Enum):
    """Represents a hardware component type."""
    GPU = "gpu"
    CPU = "cpu"
    DRIVE = "drive"
    MEMORY = "memory"
    POWER_SUPPLY = "power_supply"
    MOTHERBOARD = "motherboard"
    COOLING = "cooling"
    DISPLAY = "display"
    NETWORK = "network"
    CASE = "case"
    PERIPHERAL = "peripheral"
    CABLE = "cable"
    NONE = "none"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, component_str: str) -> 'HardwareComponent':
        """
        Create a HardwareComponent from a string.

        Args:
            component_str: String representation of the component

        Returns:
            HardwareComponent enum value
        """
        if not component_str:
            return cls.NONE

        normalized = component_str.lower().replace(" ", "_").strip()

        try:
            return cls(normalized)
        except ValueError:
            # Handle common synonyms
            if normalized in ("graphics_card", "video_card", "graphics", "video"):
                return cls.GPU
            elif normalized in ("processor", "central_processing_unit"):
                return cls.CPU
            elif normalized in ("ram", "ddr", "dimm", "sodimm"):
                return cls.MEMORY
            elif normalized in ("hdd", "ssd", "nvme", "storage", "hard_drive", "solid_state_drive"):
                return cls.DRIVE
            elif normalized in ("psu", "power"):
                return cls.POWER_SUPPLY
            elif normalized in ("mobo", "mainboard"):
                return cls.MOTHERBOARD
            elif normalized in ("fan", "heatsink", "radiator", "aio", "water_cooling"):
                return cls.COOLING
            elif normalized in ("monitor", "screen", "lcd", "led"):
                return cls.DISPLAY
            elif normalized in ("nic", "ethernet", "wifi", "wireless", "lan", "router"):
                return cls.NETWORK
            elif normalized in ("chassis", "enclosure"):
                return cls.CASE
            elif normalized in ("keyboard", "mouse", "kvm", "external"):
                return cls.PERIPHERAL
            elif normalized in ("connector", "pcie_cable", "sata_cable", "power_cable"):
                return cls.CABLE
            else:
                return cls.UNKNOWN

    def get_display_name(self) -> str:
        """
        Get a human-readable display name for the component type.

        Returns:
            Display name
        """
        display_names = {
            self.GPU: "Graphics Card",
            self.CPU: "Processor",
            self.DRIVE: "Storage Drive",
            self.MEMORY: "Memory",
            self.POWER_SUPPLY: "Power Supply",
            self.MOTHERBOARD: "Motherboard",
            self.COOLING: "Cooling System",
            self.DISPLAY: "Display",
            self.NETWORK: "Network Component",
            self.CASE: "Case",
            self.PERIPHERAL: "Peripheral Device",
            self.CABLE: "Cable/Connector",
            self.NONE: "None",
            self.UNKNOWN: "Unknown Component"
        }

        return display_names.get(self, "Unknown Component")

    def is_critical(self) -> bool:
        """
        Check if the component is critical for system operation.

        Returns:
            True if the component is critical, False otherwise
        """
        critical_components = [
            self.CPU,
            self.MOTHERBOARD,
            self.MEMORY,
            self.POWER_SUPPLY
        ]

        return self in critical_components
