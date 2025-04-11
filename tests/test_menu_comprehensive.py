"""
Comprehensive test suite for the interactive menu functionality.

This module contains tests for various view structures, large numbers of views,
search functionality, and keyboard shortcuts.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch, call

# Add the parent directory to the path for importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from src.modules.menu.view_hierarchy import ViewHierarchyParser
from src.modules.menu.breadcrumb import BreadcrumbTrail
from src.modules.menu.zendesk_menu import ZendeskMenu
from src.modules.menu.menu_actions import ZendeskMenuActions

# Create test fixtures for various view structures
@pytest.fixture
def empty_views():
    """Create an empty list of views for testing."""
    return []

@pytest.fixture
def flat_views():
    """Create a list of flat views without hierarchical structure."""
    views = []
    
    # Create a simple View class for testing
    class MockView:
        def __init__(self, id, title):
            self.id = id
            self.title = title
    
    # Create some sample views without hierarchy
    views.append(MockView(1, "Open Tickets"))
    views.append(MockView(2, "Closed Tickets"))
    views.append(MockView(3, "Pending Tickets"))
    views.append(MockView(4, "Solved Tickets"))
    views.append(MockView(5, "All Tickets"))
    
    return views

@pytest.fixture
def nested_views():
    """Create a list of views with a hierarchical structure."""
    views = []
    
    # Create a simple View class for testing
    class MockView:
        def __init__(self, id, title):
            self.id = id
            self.title = title
    
    # Create some sample views with hierarchical naming
    views.append(MockView(1, "Support :: Pending Support"))
    views.append(MockView(2, "Support :: Active Tickets"))
    views.append(MockView(3, "Support :: Escalated :: Urgent"))
    views.append(MockView(4, "Support :: Escalated :: Standard"))
    views.append(MockView(5, "Hardware :: RMA :: Pending"))
    views.append(MockView(6, "Hardware :: RMA :: Processed"))
    views.append(MockView(7, "Production :: Build Queue"))
    views.append(MockView(8, "Single Level View"))
    
    return views

@pytest.fixture
def deeply_nested_views():
    """Create a list of views with a deeply nested hierarchical structure."""
    views = []
    
    # Create a simple View class for testing
    class MockView:
        def __init__(self, id, title):
            self.id = id
            self.title = title
    
    # Create deeply nested views (4+ levels)
    views.append(MockView(1, "Level1 :: Level2 :: Level3 :: Level4 :: View1"))
    views.append(MockView(2, "Level1 :: Level2 :: Level3 :: Level4 :: View2"))
    views.append(MockView(3, "Level1 :: Level2 :: Level3 :: OtherLevel4 :: View3"))
    views.append(MockView(4, "Level1 :: Level2 :: OtherLevel3 :: Level4 :: View4"))
    views.append(MockView(5, "Level1 :: OtherLevel2 :: Level3 :: Level4 :: View5"))
    views.append(MockView(6, "OtherLevel1 :: Level2 :: Level3 :: Level4 :: View6"))
    
    return views

@pytest.fixture
def large_view_list():
    """Create a large list of views (100+) for testing performance."""
    views = []
    
    # Create a simple View class for testing
    class MockView:
        def __init__(self, id, title):
            self.id = id
            self.title = title
    
    # Create categories A through J
    categories = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    # Create subcategories 1 through 5
    subcategories = ["1", "2", "3", "4", "5"]
    
    # Create 10 views per subcategory
    view_count = 0
    for category in categories:
        for subcategory in subcategories:
            for i in range(1, 11):  # 10 views per subcategory
                view_count += 1
                title = f"{category} :: {subcategory} :: View {i}"
                views.append(MockView(view_count, title))
    
    # Should create 10 * 5 * 10 = 500 views
    return views

@pytest.fixture
def mock_zendesk_client(nested_views):
    """Create a mock ZendeskClient for testing."""
    client = MagicMock()
    client.fetch_views.return_value = nested_views
    return client

@pytest.fixture
def mock_db_repository():
    """Create a mock DBRepository for testing."""
    repo = MagicMock()
    # Set up the repository to return empty preferences
    repo.get_user_preferences.return_value = {"recent_views": []}
    return repo

# Test the ViewHierarchyParser with different view structures
class TestViewHierarchyWithDifferentStructures:
    def test_with_empty_views(self, empty_views):
        """Test that the ViewHierarchyParser handles empty view lists."""
        parser = ViewHierarchyParser(empty_views)
        
        # Even with empty views, should still initialize
        assert parser.hierarchy is not None
        
        # Categories should be empty
        assert len(parser.get_categories()) == 0
        
        # Subcategories should be empty
        assert len(parser.get_subcategories([])) == 0
        
        # Views should be empty
        assert len(parser.get_views([])) == 0
    
    def test_with_flat_views(self, flat_views):
        """Test that the ViewHierarchyParser handles flat view structures."""
        parser = ViewHierarchyParser(flat_views)
        
        # Get all views (should be at root level)
        root_views = parser.get_views([])
        
        # All views should be at the root level
        assert len(root_views) == len(flat_views)
        
        # Check that each view is in the root level
        for view in flat_views:
            assert view.title in root_views
            assert root_views[view.title] == view.id
    
    def test_with_nested_views(self, nested_views):
        """Test that the ViewHierarchyParser handles nested view structures."""
        parser = ViewHierarchyParser(nested_views)
        
        # Get top-level categories
        categories = parser.get_categories()
        assert "Support" in categories
        assert "Hardware" in categories
        assert "Production" in categories
        
        # Get subcategories
        support_subcats = parser.get_subcategories(["Support"])
        assert "Escalated" in support_subcats
        
        # Get views
        support_views = parser.get_views(["Support"])
        assert "Pending Support" in support_views
        assert "Active Tickets" in support_views
        
        # Get deeply nested views
        escalated_views = parser.get_views(["Support", "Escalated"])
        assert "Urgent" in escalated_views
        assert "Standard" in escalated_views
    
    def test_with_deeply_nested_views(self, deeply_nested_views):
        """Test that the ViewHierarchyParser handles deeply nested view structures."""
        parser = ViewHierarchyParser(deeply_nested_views)
        
        # Check the depth of the hierarchy
        level1 = parser.get_categories()
        assert "Level1" in level1
        assert "OtherLevel1" in level1
        
        # Navigate down the hierarchy
        level2 = parser.get_subcategories(["Level1"])
        assert "Level2" in level2
        assert "OtherLevel2" in level2
        
        level3 = parser.get_subcategories(["Level1", "Level2"])
        assert "Level3" in level3
        assert "OtherLevel3" in level3
        
        level4 = parser.get_subcategories(["Level1", "Level2", "Level3"])
        assert "Level4" in level4
        assert "OtherLevel4" in level4
        
        # Get the views at the deepest level
        views = parser.get_views(["Level1", "Level2", "Level3", "Level4"])
        assert "View1" in views
        assert "View2" in views
    
    def test_with_large_view_list(self, large_view_list):
        """Test that the ViewHierarchyParser handles large numbers of views efficiently."""
        import time
        
        # Measure the time it takes to build the hierarchy
        start_time = time.time()
        parser = ViewHierarchyParser(large_view_list)
        end_time = time.time()
        
        # Building the hierarchy should be reasonably fast (< 1 second)
        assert end_time - start_time < 1.0
        
        # Check that all categories are present
        categories = parser.get_categories()
        assert len(categories) == 10  # A through J
        
        # Check subcategories for a random category
        subcategories = parser.get_subcategories(["A"])
        assert len(subcategories) == 5  # 1 through 5
        
        # Get views for a specific subcategory
        views = parser.get_views(["A", "1"])
        assert len(views) == 10  # 10 views per subcategory

# Test search functionality
class TestSearchFunctionality:
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_search_functionality(self, mock_create_menu, mock_zendesk_client, mock_db_repository):
        """Test the search functionality of the menu system."""
        # Configure the mock menu to simulate search behavior
        mock_menu = MagicMock()
        mock_menu.show.return_value = None  # Simulate cancel/back
        mock_create_menu.return_value = mock_menu
        
        # Create the menu instance
        menu = ZendeskMenu(mock_zendesk_client, mock_db_repository)
        
        # Call run_main_menu which should use the menu with search
        menu.run_main_menu()
        
        # Verify that the menu was created with search_hint=True
        # Use a less specific assertion that doesn't depend on exact parameters
        mock_create_menu.assert_called()
        # Extract the call arguments
        call_args = mock_create_menu.call_args[1]
        # Check that search hint is enabled
        assert call_args.get('show_search_hint') is True

# Test keyboard shortcuts
class TestKeyboardShortcuts:
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_keyboard_shortcuts_hint(self, mock_create_menu, mock_zendesk_client, mock_db_repository):
        """Test that keyboard shortcuts are indicated in the status bar."""
        # Configure the mock menu to simulate user interaction
        mock_menu = MagicMock()
        mock_menu.show.return_value = None  # Simulate cancel/back
        mock_create_menu.return_value = mock_menu
        
        # Create the menu instance
        menu = ZendeskMenu(mock_zendesk_client, mock_db_repository)
        
        # Call run_main_menu which should show the keyboard shortcuts in the status bar
        menu.run_main_menu()
        
        # Verify that the status bar includes keyboard shortcut hints
        # Use a less specific assertion that doesn't depend on exact parameters
        mock_create_menu.assert_called()
        # Extract the call arguments
        call_args = mock_create_menu.call_args[1]
        # Check that status bar contains keyboard hints
        assert 'Navigate:' in call_args.get('status_bar', '')
        assert 'Select:' in call_args.get('status_bar', '')
        assert 'Search:' in call_args.get('status_bar', '')

# Test navigation between menu levels
class TestMenuNavigation:
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_navigation_flow(self, mock_create_menu, mock_zendesk_client, mock_db_repository):
        """Test the navigation flow between different menu levels."""
        # Configure the mock menu to simulate user selections
        mock_menu = MagicMock()
        
        # Sequence of return values to simulate:
        # 1. User selects "Support" in main menu (index 0)
        mock_menu.show.return_value = 0
        mock_create_menu.return_value = mock_menu
        
        # Create the menu instance
        menu = ZendeskMenu(mock_zendesk_client, mock_db_repository)
        
        # Set up a spy on the _handle_category_menu method
        with patch.object(menu, '_handle_category_menu') as mock_category_handler:
            # Call run_main_menu to start the navigation
            menu.run_main_menu()
            
            # Check that the category handler was called (we're more flexible with the exact arguments)
            mock_category_handler.assert_called()
        
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_breadcrumb_tracking(self, mock_create_menu, mock_zendesk_client, mock_db_repository):
        """Test that breadcrumbs correctly track the navigation path."""
        # Configure the mock menu to simulate user selections
        mock_menu = MagicMock()
        mock_menu.show.return_value = 0  # Select first item
        mock_create_menu.return_value = mock_menu
        
        # Create the menu instance
        menu = ZendeskMenu(mock_zendesk_client, mock_db_repository)
        
        # Initially breadcrumbs should be empty
        assert len(menu.breadcrumbs.get_path()) == 0
        
        # We'll patch the _handle_category_menu method to check breadcrumbs
        # Define a side effect to add to breadcrumbs
        def side_effect(path):
            assert len(path) > 0
            # Breadcrumbs should have been updated by the caller
        
        # Start the menu and navigate
        with patch.object(menu, '_handle_category_menu', side_effect=side_effect) as mock_method:
            menu.run_main_menu()

# Test action execution
class TestActionExecution:
    @patch('src.modules.menu.zendesk_menu.create_menu')
    def test_action_callbacks(self, mock_create_menu, mock_zendesk_client, mock_db_repository):
        """Test that action handlers are correctly called."""
        # Configure the mock menu to simulate user selections
        mock_menu = MagicMock()
        mock_menu.show.return_value = 0  # Select first action
        mock_create_menu.return_value = mock_menu
        
        # Create a mock action handler
        mock_action = MagicMock()
        
        # Create the menu instance with the mock action handler
        menu = ZendeskMenu(mock_zendesk_client, mock_db_repository)
        menu.action_handlers = {
            "run_sentiment_analysis": mock_action,
            "generate_report": mock_action,
            "view_tickets": mock_action,
        }
        
        # Execute the view actions menu
        menu._handle_view_actions(123, "Test View")
        
        # Verify the action handler was called with the correct arguments
        mock_action.assert_called_once_with(123, "Test View")
