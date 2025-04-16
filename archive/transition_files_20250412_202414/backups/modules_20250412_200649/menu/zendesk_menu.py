"""
Zendesk Menu Module

This module provides backward compatibility for the zendesk_menu module.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)


class ZendeskMenu:
    """
    Legacy Zendesk menu class.
    
    This is a compatibility stub that delegates to the new implementation.
    """
    
    def __init__(self, zendesk_client=None, ai_analyzer=None, db_repository=None):
        """
        Initialize the Zendesk menu.
        
        Args:
            zendesk_client: ZendeskClient instance
            ai_analyzer: AIAnalyzer instance
            db_repository: DBRepository instance
        """
        logger.debug("ZendeskMenu initialized (compatibility mode)")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Import here to avoid circular imports
        from src.modules.menu.breadcrumb import BreadcrumbTrail
        from src.modules.menu.menu_actions import ZendeskMenuActions
        
        self.breadcrumb = BreadcrumbTrail()
        self.actions = ZendeskMenuActions(zendesk_client, ai_analyzer, db_repository)
    
    def start(self):
        """
        Start the menu.
        
        Returns:
            Menu result
        """
        logger.debug("Starting Zendesk menu (compatibility mode)")
        
        # Import here to avoid circular imports
        from src.presentation.cli.commands.interactive_command import InteractiveCommand
        
        command = InteractiveCommand()
        return command.execute()
    
    def display_menu(self, menu_items):
        """
        Display a menu.
        
        Args:
            menu_items: Menu items to display
            
        Returns:
            Selected menu item
        """
        logger.debug(f"Displaying menu with {len(menu_items)} items (compatibility mode)")
        
        for i, item in enumerate(menu_items, 1):
            print(f"{i}. {item}")
        
        while True:
            try:
                choice = input("Enter your choice: ")
                index = int(choice) - 1
                if 0 <= index < len(menu_items):
                    return menu_items[index]
                print(f"Please enter a number between 1 and {len(menu_items)}")
            except ValueError:
                print("Please enter a valid number")
