"""
Command Pattern Implementation

This module defines the Command interface and related classes for implementing
the command pattern in the CLI interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Command(ABC):
    """
    Interface for command pattern implementation.

    Commands encapsulate actions that can be executed by the CLI.
    """

    def __init__(self, dependency_container):
        """
        Initialize the command.

        Args:
            dependency_container: Container for service dependencies
        """
        self.dependency_container = dependency_container

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        pass

    @abstractmethod
    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        pass

    @property
    def name(self) -> str:
        """
        Get the name of the command.

        Returns:
            Command name
        """
        return self.__class__.__name__.lower().replace('command', '')

    @property
    def description(self) -> str:
        """
        Get the description of the command.

        Returns:
            Command description
        """
        return "No description available"
