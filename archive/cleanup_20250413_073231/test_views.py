#!/usr/bin/env python3
"""
Test script for the views command
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Test the views command"""
    try:
        # Import necessary modules
        from src.presentation.cli.commands.list_views_command import ListViewsCommand
        from src.infrastructure.utils.dependency_injection import DependencyContainer
        from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
        from src.domain.interfaces.repository_interfaces import ViewRepository
        
        # Create dependency container
        dependency_container = DependencyContainer()
        
        # Create and register Zendesk repository
        zendesk_repo = ZendeskRepository()
        dependency_container.register_instance(ViewRepository, zendesk_repo)
        
        # Create command
        views_command = ListViewsCommand(dependency_container)
        
        # Execute command with various options
        print("=== Testing views command with default options ===")
        result = views_command.execute({
            "format": "text",
            "output": None,
            "flat": False,
            "include_inactive": False,
            "filter": None
        })
        print("\n\n")
        
        print("=== Testing views command with flat list ===")
        result = views_command.execute({
            "format": "text",
            "output": None,
            "flat": True,
            "include_inactive": False,
            "filter": None
        })
        print("\n\n")
        
        print("=== Testing views command with inactive views ===")
        result = views_command.execute({
            "format": "text",
            "output": None,
            "flat": False,
            "include_inactive": True,
            "filter": None
        })
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
