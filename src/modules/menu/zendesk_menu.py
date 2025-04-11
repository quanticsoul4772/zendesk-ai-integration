"""
Zendesk Menu Module

This module provides an interactive terminal-based menu system for navigating
Zendesk views and executing actions on them.
"""

import os
import logging
import sys
import platform
from typing import List, Dict, Any, Optional, Tuple, Callable

# Import local modules
from .view_hierarchy import ViewHierarchyParser
from .breadcrumb import BreadcrumbTrail

# Set up logging
logger = logging.getLogger(__name__)

# Create platform-specific menu system
if platform.system() == "Windows":
    logger.info("Using Windows-compatible menu system")
    # Try to import the Windows-specific menu
    try:
        from .windows_menu import WindowsMenu as MenuImplementation
        # Define create_menu function for Windows
        def create_menu(options, **kwargs):
            return MenuImplementation(options, **kwargs)
    except ImportError as e:
        logger.error(f"Error importing Windows menu: {e}")
        # Create a basic fallback menu for Windows
        def create_menu(options, **kwargs):
            title = kwargs.get('title', '')
            status_bar = kwargs.get('status_bar', '')
            
            class BasicMenu:
                def __init__(self, options, title=None, status_bar=None):
                    self.options = options
                    self.title = title
                    self.status_bar = status_bar
                    
                def show(self):
                    os.system('cls')  # Clear screen
                    if self.title:
                        print(f"\n{self.title}\n")
                    if self.status_bar:
                        print(f"{self.status_bar}\n")
                    
                    for i, entry in enumerate(self.options):
                        print(f"{i+1}. {entry}")
                    
                    while True:
                        try:
                            choice = input("\nEnter selection (q to quit): ")
                            if choice.lower() == 'q':
                                return None
                            idx = int(choice) - 1
                            if 0 <= idx < len(self.options):
                                return idx
                            print("Invalid selection. Try again.")
                        except ValueError:
                            print("Please enter a number or 'q' to quit.")
            
            return BasicMenu(options, title, status_bar)
else:
    logger.info("Using simple-term-menu for menu system")
    # Try importlib.metadata first (Python 3.8+)
    try:
        import importlib.metadata
        simple_term_menu_version = importlib.metadata.version("simple-term-menu")
        logger.info(f"simple-term-menu version: {simple_term_menu_version}")
    except (ImportError, Exception):
        logger.info("Could not determine simple-term-menu version")
    
    # Try to import the simple-term-menu library
    try:
        from simple_term_menu import TerminalMenu as MenuImplementation
        # Define create_menu function for Unix-like systems
        def create_menu(options, **kwargs):
            return MenuImplementation(options, **kwargs)
    except ImportError:
        logger.error("simple-term-menu is not installed. Run: pip install simple-term-menu")
        # Create a fallback TerminalMenu class for basic functionality
        def create_menu(options, **kwargs):
            title = kwargs.get('title', '')
            status_bar = kwargs.get('status_bar', '')
            
            class BasicMenu:
                def __init__(self, options, title=None, status_bar=None):
                    self.options = options
                    self.title = title
                    self.status_bar = status_bar
                    
                def show(self):
                    os.system('clear')  # Clear screen
                    if self.title:
                        print(f"\n{self.title}\n")
                    if self.status_bar:
                        print(f"{self.status_bar}\n")
                    
                    for i, entry in enumerate(self.options):
                        print(f"{i+1}. {entry}")
                    
                    while True:
                        try:
                            choice = input("\nEnter selection (q to quit): ")
                            if choice.lower() == 'q':
                                return None
                            idx = int(choice) - 1
                            if 0 <= idx < len(self.options):
                                return idx
                            print("Invalid selection. Try again.")
                        except ValueError:
                            print("Please enter a number or 'q' to quit.")
            
            return BasicMenu(options, title, status_bar)


class ZendeskMenu:
    """
    Interactive menu system for Zendesk AI integration.
    
    This class provides a hierarchical menu system for navigating Zendesk views
    and executing actions on them. Now includes view status checking functionality.
    """
    
    def __init__(self, zendesk_client, db_repository=None, max_recent_views=5):
        """
        Initialize the ZendeskMenu system.
        
        Args:
            zendesk_client: Instance of ZendeskClient for API interactions
            db_repository: Optional database repository for storing user preferences
            max_recent_views: Maximum number of recent views to track (default: 5)
        """
        self.zendesk_client = zendesk_client
        self.db_repository = db_repository
        self.max_recent_views = max_recent_views
        self.breadcrumbs = BreadcrumbTrail()
        self.recent_views = self._load_recent_views()
        
        # Initialize view status cache
        self._view_status_cache = {}
        
        logger.info("Initializing Zendesk menu system")
        logger.info("Fetching views from Zendesk")
        
        # Fetch all views from Zendesk
        try:
            self.views = list(zendesk_client.fetch_views())
            logger.info(f"Successfully fetched {len(self.views)} views")
        except Exception as e:
            logger.error(f"Error fetching views: {e}")
            self.views = []
            
        # Parse views into a hierarchical structure
        self.view_hierarchy = ViewHierarchyParser(self.views)
        
        # Define action handlers (will be implemented in child classes or extended)
        self.action_handlers = {
            "run_sentiment_analysis": self._action_not_implemented,
            "generate_report": self._action_not_implemented,
            "view_tickets": self._action_not_implemented,
        }
        
        logger.info("Zendesk menu system initialized")
        
    def _load_recent_views(self) -> List[int]:
        """
        Load recently used views from storage.
        
        Returns:
            List of recent view IDs
        """
        # If db_repository is available, load from there
        if self.db_repository and hasattr(self.db_repository, 'get_user_preferences'):
            try:
                prefs = self.db_repository.get_user_preferences()
                if prefs and 'recent_views' in prefs:
                    return prefs['recent_views'][:self.max_recent_views]
            except Exception as e:
                logger.error(f"Error loading recent views: {e}")
        
        return []
        
    def _save_recent_views(self) -> None:
        """
        Save recently used views to storage.
        """
        # If db_repository is available, save to it
        if self.db_repository and hasattr(self.db_repository, 'update_user_preferences'):
            try:
                self.db_repository.update_user_preferences({
                    'recent_views': self.recent_views[:self.max_recent_views]
                })
                logger.debug(f"Saved {len(self.recent_views)} recent views")
            except Exception as e:
                logger.error(f"Error saving recent views: {e}")
                
    def _add_recent_view(self, view_id: int) -> None:
        """
        Add a view to the recently used list.
        
        Args:
            view_id: ID of the view to add
        """
        # Remove if already exists (to move to top)
        if view_id in self.recent_views:
            self.recent_views.remove(view_id)
            
        # Add to the beginning of the list
        self.recent_views.insert(0, view_id)
        
        # Trim list if too long
        if len(self.recent_views) > self.max_recent_views:
            self.recent_views = self.recent_views[:self.max_recent_views]
            
        # Save the updated list
        self._save_recent_views()
        
    def _create_menu(self, options: List[str], title: Optional[str] = None, 
                    status_bar: Optional[str] = None, multi_select: bool = False,
                    show_search: bool = True) -> Any:
        """
        Create a terminal menu with consistent styling.
        
        Args:
            options: List of menu options to display
            title: Optional title for the menu (default: breadcrumb trail)
            status_bar: Optional status bar text
            multi_select: Whether to allow multiple selections (default: False)
            show_search: Whether to show search hint (default: True)
            
        Returns:
            Configured menu instance
        """
        if title is None:
            title = str(self.breadcrumbs)
            
        try:
            # Create menu using the platform-specific factory function
            menu = create_menu(
                options,
                title=title,
                status_bar=status_bar,
                cursor="▶ ",
                cursor_index=0,
                cycle_cursor=True,
                clear_screen=True,
                multi_select=multi_select,
                show_search_hint=show_search,
                preview_border="rounded",
                shortcut_key_highlighting=True
            )
        except Exception as e:
            logger.error(f"Error creating menu: {e}")
            # Fallback to basic implementation
            class BasicFallbackMenu:
                def __init__(self, options, title=None):
                    self.options = options
                    self.title = title
                    
                def show(self):
                    if self.title:
                        print(f"\n{self.title}\n")
                    
                    for i, entry in enumerate(self.options):
                        print(f"{i+1}. {entry}")
                    
                    while True:
                        try:
                            choice = input("\nEnter selection (q to quit): ")
                            if choice.lower() == 'q':
                                return None
                            idx = int(choice) - 1
                            if 0 <= idx < len(self.options):
                                return idx
                            print("Invalid selection. Try again.")
                        except ValueError:
                            print("Please enter a number or 'q' to quit.")
            
            menu = BasicFallbackMenu(options, title=title)
            
        return menu
        
    def _action_not_implemented(self, view_id: int, view_name: str) -> None:
        """
        Placeholder for actions not yet implemented.
        
        Args:
            view_id: ID of the selected view
            view_name: Name of the selected view
        """
        print(f"\nAction not implemented for view: {view_name} (ID: {view_id})")
        input("Press Enter to continue...")
        
    def run_main_menu(self) -> None:
        """
        Display and handle the main menu.
        
        This is the entry point for the interactive menu system.
        """
        logger.info("Starting main menu")
        
        while True:
            # Clear breadcrumbs when returning to main menu
            self.breadcrumbs.clear()
            
            # Get top-level categories
            categories = self.view_hierarchy.get_categories()
            
            # Build menu options
            menu_options = []
            
            # Add recently used views section if available
            if self.recent_views:
                recent_view_names = self.view_hierarchy.get_recently_used_views(self.recent_views)
                if recent_view_names:
                    # Update the status of recent views
                    self._update_view_status_cache_if_needed(list(recent_view_names.values()))
                    
                    menu_options.append("--- Recent Views ---")
                    for name, view_id in recent_view_names.items():
                        # Add status indicator for recent views
                        if view_id in self._view_status_cache:
                            if self._view_status_cache[view_id] is False:
                                menu_options.append(f"Recent [Empty]: {name}")
                            elif self._view_status_cache[view_id] is True:
                                menu_options.append(f"Recent [✓]: {name}")
                            else:
                                menu_options.append(f"Recent: {name}")
                        else:
                            menu_options.append(f"Recent: {name}")
                    menu_options.append("--- Categories ---")
            
            # Add categories
            for category in sorted(categories):
                menu_options.append(category)
                
            # Add utilities section
            menu_options.append("--- Utilities ---")
            menu_options.append("Check Views for Tickets")
                
            # Add exit option
            menu_options.append("Exit")
            
            # Create and show menu
            title = "Zendesk AI Integration - Main Menu"
            status_bar = "Navigate: ↑/↓  Select: Enter  Search: /  Exit: Esc"
            menu = self._create_menu(menu_options, title=title, status_bar=status_bar)
            
            selection = menu.show()
            
            # Handle selection
            if selection is None or menu_options[selection] == "Exit":
                logger.info("Exiting menu system")
                break
                
            selected_option = menu_options[selection]
            
            # Handle recent view selection
            if selected_option.startswith("Recent: ") or \
               selected_option.startswith("Recent [Empty]: ") or \
               selected_option.startswith("Recent [✓]: "):
                
                # Extract view name by removing the prefix
                if selected_option.startswith("Recent: "):
                    view_name = selected_option[8:]  # Strip "Recent: " prefix
                elif selected_option.startswith("Recent [Empty]: "):
                    view_name = selected_option[15:]  # Strip "Recent [Empty]: " prefix
                else:  # Recent [✓]: prefix
                    view_name = selected_option[12:]  # Strip "Recent [✓]: " prefix
                    
                for view in self.views:
                    if view.title == view_name:
                        self._handle_view_actions(view.id, view_name)
                        break
            # Handle utility selection
            elif selected_option == "Check Views for Tickets":
                self._handle_check_views_menu()
            # Handle category selection
            elif selected_option not in ["--- Recent Views ---", "--- Categories ---", "--- Utilities ---"]:
                self.breadcrumbs.add(selected_option)
                self._handle_category_menu([selected_option])
                
        logger.info("Menu system closed")
        
    def _handle_category_menu(self, path: List[str]) -> None:
        """
        Display and handle the category/subcategory menu.
        
        Args:
            path: List of category names forming the current path
        """
        if not path:
            return
            
        current_category = path[-1]
        logger.debug(f"Handling category menu for: {current_category}")
        
        # Get subcategories for this path
        subcategories = self.view_hierarchy.get_subcategories(path)
        
        # Get views for this path
        views = self.view_hierarchy.get_views(path)
        
        # Update view status cache for these views if needed
        self._update_view_status_cache_if_needed(views.values())
        
        while True:
            # Build menu options
            menu_options = []
            
            # Add subcategories if available
            if subcategories:
                menu_options.append("--- Subcategories ---")
                for subcat in sorted(subcategories):
                    menu_options.append(subcat)
                    
            # Add views if available
            if views:
            menu_options.append("--- Views ---")
            for view_name in sorted(views.keys()):
            view_id = views[view_name]
            
            # Add indicator based on view status
            if view_id in self._view_status_cache:
            # We have status information for this view
            status_info = self._view_status_cache[view_id]
            
            if not status_info.get('has_tickets', False):
                # View has no tickets
            menu_options.append(f"View [Empty]: {view_name}")
            else:
                # View has tickets - show detailed status
            total = status_info.get('total', 0)
            pending = status_info.get('pending', 0)
                    open_tickets = status_info.get('open', 0)
                
                if total > 0:
                                    # Show detailed counts
                                    status_str = f"[{total} total"
                                    if pending > 0:
                                        status_str += f", {pending} pending"
                                    if open_tickets > 0:
                                        status_str += f", {open_tickets} open"
                                    status_str += "]"
                                    menu_options.append(f"View {status_str}: {view_name}")
                                else:
                                    # Fallback to simple indicator
                                    menu_options.append(f"View [✓]: {view_name}")
                        else:
                            # No status information
                            menu_options.append(f"View: {view_name}")
            
            # Add back/exit options
            menu_options.append("Back")
            menu_options.append("Main Menu")
            
            # Create and show menu
            title = f"Category: {current_category}"
            status_bar = "Navigate: ↑/↓  Select: Enter  Search: /  Back: Esc"
            menu = self._create_menu(menu_options, status_bar=status_bar)
            
            selection = menu.show()
            
            # Handle selection
            if selection is None or menu_options[selection] == "Back":
                self.breadcrumbs.pop()
                break
            elif menu_options[selection] == "Main Menu":
                self.breadcrumbs.clear()
                break
                
            selected_option = menu_options[selection]
            
            # Handle view selection
            if selected_option.startswith("View: ") or \
               selected_option.startswith("View [Empty]: ") or \
               selected_option.startswith("View [✓]: "):
                
                # Extract view name by removing the prefix
                if selected_option.startswith("View: "):
                    view_name = selected_option[6:]  # Strip "View: " prefix
                elif selected_option.startswith("View [Empty]: "):
                    view_name = selected_option[13:]  # Strip "View [Empty]: " prefix
                else:  # View [✓]: prefix
                    view_name = selected_option[10:]  # Strip "View [✓]: " prefix
                    
                view_id = views[view_name]
                self._handle_view_actions(view_id, view_name)
            # Handle subcategory selection
            elif selected_option not in ["--- Subcategories ---", "--- Views ---", "Back", "Main Menu"]:
                self.breadcrumbs.add(selected_option)
                new_path = path + [selected_option]
                self._handle_category_menu(new_path)
                self.breadcrumbs.pop()
        
    def _handle_view_actions(self, view_id: int, view_name: str) -> None:
        """
        Display and handle the actions menu for a selected view.
        
        Args:
            view_id: ID of the selected view
            view_name: Name of the selected view
        """
        logger.debug(f"Handling view actions for: {view_name} (ID: {view_id})")
        
        # Add to recently used views
        self._add_recent_view(view_id)
        
        # Define available actions
        actions = [
            "Run Sentiment Analysis",
            "Generate Pending Report",
            "Generate Enhanced Report",
            "View Tickets in Browser",
            "Back"
        ]
        
        # Create and show menu
        title = f"View: {view_name} (ID: {view_id})"
        status_bar = "Select an action to perform on this view"
        menu = self._create_menu(actions, title=title, status_bar=status_bar)
        
        selection = menu.show()
        
        # Handle selection
        if selection is None or actions[selection] == "Back":
            return
            
        selected_action = actions[selection]
        
        # Execute the corresponding action
        if selected_action == "Run Sentiment Analysis":
            if "run_sentiment_analysis" in self.action_handlers:
                self.action_handlers["run_sentiment_analysis"](view_id, view_name)
        elif selected_action == "Generate Pending Report":
            if "generate_report" in self.action_handlers:
                self.action_handlers["generate_report"](view_id, view_name, "pending")
        elif selected_action == "Generate Enhanced Report":
            if "generate_report" in self.action_handlers:
                self.action_handlers["generate_report"](view_id, view_name, "enhanced")
        elif selected_action == "View Tickets in Browser":
            if "view_tickets" in self.action_handlers:
                self.action_handlers["view_tickets"](view_id, view_name)
        
    def _update_view_status_cache_if_needed(self, view_ids: List[int]) -> None:
        """
        Update the cache with information about which views have tickets.
        Only checks views that don't have status information yet.
        
        Args:
            view_ids: List of view IDs to check
        """
        views_to_check = []
        for view_id in view_ids:
            if view_id not in self._view_status_cache:
                views_to_check.append(view_id)
                
        if not views_to_check:
            return
            
        logger.debug(f"Checking status for {len(views_to_check)} views")
        
        for view_id in views_to_check:
            try:
                # Fetch tickets to check view content
                tickets = self.zendesk_client.fetch_tickets_from_view(view_id, limit=50)
                
                # Check total tickets
                total_tickets = len(tickets)
                
                # Check for specific ticket types
                pending_tickets = sum(1 for t in tickets if hasattr(t, 'status') and t.status == 'pending')
                open_tickets = sum(1 for t in tickets if hasattr(t, 'status') and t.status == 'open')
                
                # Store detailed status information
                self._view_status_cache[view_id] = {
                    'has_tickets': total_tickets > 0,
                    'total': total_tickets,
                    'pending': pending_tickets,
                    'open': open_tickets
                }
                
                logger.debug(f"View {view_id} has {total_tickets} tickets, {pending_tickets} pending, {open_tickets} open")
            except Exception as e:
                logger.error(f"Error checking view {view_id} status: {e}")
                # If there's an error, we don't know the status
                self._view_status_cache[view_id] = {
                    'has_tickets': None,
                    'total': 0,
                    'pending': 0,
                    'open': 0
                }
    
    def _check_views_for_tickets(self, view_ids: List[int]) -> None:
        """
        Check which views have tickets and update the status cache.
        This method forces a refresh of the cache for the specified views.
        
        Args:
            view_ids: List of view IDs to check
        """
        for view_id in view_ids:
            try:
                # Force a new check
                tickets = self.zendesk_client.fetch_tickets_from_view(view_id, limit=1)
                has_tickets = len(tickets) > 0
                self._view_status_cache[view_id] = has_tickets
                logger.debug(f"Updated status for view {view_id}, has tickets: {has_tickets}")
            except Exception as e:
                logger.error(f"Error checking view {view_id} status: {e}")
                self._view_status_cache[view_id] = None
                
    def _handle_check_views_menu(self) -> None:
        """
        Display a menu for selecting views to check for tickets.
        """
        # Get all views
        all_views = {}
        for view in self.views:
            if hasattr(view, 'title') and hasattr(view, 'id'):
                all_views[view.title] = view.id
        
        # Build menu options
        menu_options = []
        
        # Add recently used views section if available
        if self.recent_views:
            recent_view_names = self.view_hierarchy.get_recently_used_views(self.recent_views)
            if recent_view_names:
                menu_options.append("--- Recent Views ---")
                for name, view_id in recent_view_names.items():
                    menu_options.append(f"Recent: {name}")
                    
        # Add all views option
        menu_options.append("--- Options ---")
        menu_options.append("Check All Views")
        menu_options.append("Check Views with Tickets")
        menu_options.append("Check Views without Tickets")
        
        # Add back option
        menu_options.append("Back")
        
        # Create and show menu
        title = "Select Views to Check"
        status_bar = "Navigate: ↑/↓  Select: Enter  Search: /  Back: Esc"
        menu = self._create_menu(menu_options, title=title, status_bar=status_bar)
        
        selection = menu.show()
        
        # Handle selection
        if selection is None or menu_options[selection] == "Back":
            return
        
        selected_option = menu_options[selection]
        
        if selected_option == "Check All Views":
            # Check all views
            print("\nChecking all views for tickets... This may take a while.")
            self._check_views_for_tickets(list(all_views.values()))
            
            # Display results
            self._display_view_status_results(all_views)
        elif selected_option == "Check Views with Tickets":
            # Filter views that have tickets
            views_with_tickets = {}
            for name, view_id in all_views.items():
                if view_id in self._view_status_cache and self._view_status_cache[view_id] is True:
                    views_with_tickets[name] = view_id
            
            if not views_with_tickets:
                print("\nNo views with tickets found in cache. Checking all views first...")
                self._check_views_for_tickets(list(all_views.values()))
                # Refilter after checking
                for name, view_id in all_views.items():
                    if view_id in self._view_status_cache and self._view_status_cache[view_id] is True:
                        views_with_tickets[name] = view_id
            
            # Display results for views with tickets
            self._display_view_status_results(views_with_tickets)
        elif selected_option == "Check Views without Tickets":
            # Filter views that don't have tickets
            views_without_tickets = {}
            for name, view_id in all_views.items():
                if view_id in self._view_status_cache and self._view_status_cache[view_id] is False:
                    views_without_tickets[name] = view_id
            
            if not views_without_tickets:
                print("\nNo empty views found in cache. Checking all views first...")
                self._check_views_for_tickets(list(all_views.values()))
                # Refilter after checking
                for name, view_id in all_views.items():
                    if view_id in self._view_status_cache and self._view_status_cache[view_id] is False:
                        views_without_tickets[name] = view_id
            
            # Display results for views without tickets
            self._display_view_status_results(views_without_tickets)
        elif selected_option.startswith("Recent: "):
            # Extract view name
            view_name = selected_option[8:]  # Strip "Recent: " prefix
            view_id = None
            
            # Find the view ID
            for view in self.views:
                if view.title == view_name:
                    view_id = view.id
                    break
            
            if view_id is not None:
                # Check this specific view
                print(f"\nChecking view '{view_name}' for tickets...")
                self._check_views_for_tickets([view_id])
                
                # Display results for just this view
                view_dict = {view_name: view_id}
                self._display_view_status_results(view_dict)
            else:
                print(f"\nView '{view_name}' not found.")
                input("Press Enter to continue...")
    
    def _display_view_status_results(self, view_dict: Dict[str, int]) -> None:
        """
        Display the results of checking views for tickets.
        
        Args:
            view_dict: Dictionary mapping view names to view IDs
        """
        # Check if we have status information for these views
        missing_status = []
        for name, view_id in view_dict.items():
            if view_id not in self._view_status_cache:
                missing_status.append((name, view_id))
        
        # Check any views with missing status
        if missing_status:
            print(f"\nChecking {len(missing_status)} views with unknown status...")
            self._check_views_for_tickets([view_id for _, view_id in missing_status])
        
        # Prepare results
        results = []
        for name, view_id in sorted(view_dict.items()):
            if view_id in self._view_status_cache:
                has_tickets = self._view_status_cache[view_id]
                if has_tickets is True:
                    status = "Has tickets"
                elif has_tickets is False:
                    status = "Empty"
                else:
                    status = "Unknown"
            else:
                status = "Unknown"
                
            results.append((name, view_id, status))
        
        # Display results
        print("\n===== View Status Check Results =====")
        print(f"{'View Name':<40} {'View ID':<15} {'Status':<15}")
        print("-" * 70)
        
        empty_count = 0
        has_tickets_count = 0
        unknown_count = 0
        
        for name, view_id, status in results:
            if status == "Empty":
                empty_count += 1
            elif status == "Has tickets":
                has_tickets_count += 1
            else:
                unknown_count += 1
                
            print(f"{name[:40]:<40} {view_id:<15} {status:<15}")
        
        # Display summary
        print("\nSummary:")
        print(f"Total views checked: {len(results)}")
        print(f"Views with tickets: {has_tickets_count}")
        print(f"Empty views: {empty_count}")
        if unknown_count > 0:
            print(f"Views with unknown status: {unknown_count}")
        
        # Wait for user input
        input("\nPress Enter to continue...")
    
    def start(self) -> None:
        """
        Start the interactive menu system.
        """
        try:
            self.run_main_menu()
        except KeyboardInterrupt:
            logger.info("Menu interrupted by user (Ctrl+C)")
            print("\nExiting...")
        except Exception as e:
            logger.exception(f"Error in menu system: {e}")
            print(f"\nAn error occurred: {e}")
        finally:
            # Ensure we save any recent views
            self._save_recent_views()
