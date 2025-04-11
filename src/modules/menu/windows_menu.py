"""
Windows-compatible menu system for Zendesk AI integration.

This module provides a Windows-compatible implementation of the menu system
using the prompt_toolkit library instead of simple-term-menu.
"""

import os
import sys
import logging
import platform
from typing import List, Dict, Any, Optional, Tuple, Callable

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import Frame, Box
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import clear, radiolist_dialog

# Set up logging
logger = logging.getLogger(__name__)

class WindowsMenu:
    """
    Windows-compatible menu system for Zendesk AI integration.
    
    This class provides similar functionality to the TerminalMenu class but
    works on Windows without requiring the termios module.
    """
    
    def __init__(self, menu_entries, title=None, status_bar=None, cursor="▶ ",
                cursor_index=0, cycle_cursor=True, clear_screen=True,
                multi_select=False, show_search_hint=True, preview_border="rounded",
                shortcut_key_highlighting=True):
        """
        Initialize the Windows-compatible menu.
        
        Args:
            menu_entries: List of menu options
            title: Optional menu title
            status_bar: Optional status bar text
            cursor: Cursor symbol to use
            cursor_index: Initial selection index
            cycle_cursor: Whether to cycle through options
            clear_screen: Whether to clear the screen before showing the menu
            multi_select: Whether to allow multiple selections
            show_search_hint: Whether to show search hint
            preview_border: Border style for preview
            shortcut_key_highlighting: Whether to highlight shortcut keys
        """
        self.menu_entries = menu_entries
        self.title = title or ""
        self.status_bar = status_bar or ""
        self.cursor = cursor
        self.cursor_index = cursor_index
        self.cycle_cursor = cycle_cursor
        self.clear_screen = clear_screen
        self.multi_select = multi_select
        self.show_search_hint = show_search_hint
        self.preview_border = preview_border
        self.shortcut_key_highlighting = shortcut_key_highlighting
        
        # Store the selection
        self.selected_index = None
        self.search_text = ""
        
        # Get terminal size
        self.terminal_height, self.terminal_width = self._get_terminal_size()
        
        logger.debug(f"Initialized WindowsMenu with {len(menu_entries)} entries")
        
    def _get_terminal_size(self):
        """
        Get the size of the terminal window.
        
        Returns:
            Tuple with (height, width) of the terminal window
        """
        try:
            # Try using shutil.get_terminal_size
            import shutil
            size = shutil.get_terminal_size()
            return size.lines, size.columns
        except (ImportError, AttributeError):
            # Fallback to os.get_terminal_size
            try:
                import os
                size = os.get_terminal_size()
                return size.lines, size.columns
            except (ImportError, AttributeError):
                # Default size if all else fails
                return 24, 80
        
    def show(self):
        """
        Show the menu and return the selected index.
        
        Returns:
            Selected index or None if canceled
        """
        if not self.menu_entries:
            logger.warning("No menu entries to display")
            return None
            
        # Use a simple text-based menu without fancy styling
        result = radiolist_dialog(
            title=self.title,
            text=self.status_bar if self.status_bar else "Select an option:",
            values=[(i, entry) for i, entry in enumerate(self.menu_entries)],
            cancel_text="Back",
            # Plain style without colors
            style=Style.from_dict({
                'dialog': '',
                'dialog.body': '',
                'dialog.border': '',
                'frame.label': '',
                'radiolist': '',
                'radio-selected': '',
            })
        ).run()
        
        return result
        
    def _render_menu(self):
        """Render the menu with prompt_toolkit."""
        # Not used in this implementation since we use radiolist_dialog
        pass

class WindowsMenuAdapter:
    """
    Adapter class to provide a consistent interface between simple-term-menu and the Windows menu.
    
    This adapter allows us to use the same code with both menu implementations.
    """
    
    def __init__(self, menu_factory):
        """
        Initialize the adapter with a factory function for creating menus.
        
        Args:
            menu_factory: Function that creates menus (TerminalMenu or WindowsMenu)
        """
        self.menu_factory = menu_factory
        
    def create_menu(self, *args, **kwargs):
        """
        Create a menu using the factory function.
        
        Args:
            *args: Positional arguments for the menu factory
            **kwargs: Keyword arguments for the menu factory
            
        Returns:
            Menu object that supports show() method
        """
        return self.menu_factory(*args, **kwargs)
