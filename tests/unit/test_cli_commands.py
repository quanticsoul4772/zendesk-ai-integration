"""
Test CLI Commands

This module contains unit tests for the CLI commands.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.presentation.cli.command_handler import CommandHandler
from src.presentation.cli.commands.analyze_ticket_command import AnalyzeTicketCommand
from src.presentation.cli.commands.list_views_command import ListViewsCommand
from src.presentation.cli.commands.generate_report_command import GenerateReportCommand


class TestCommandHandler(unittest.TestCase):
    """Test cases for the CommandHandler class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the dependency container
        self.mock_dependency_container = MagicMock()
        
        # Create a patched CommandHandler that doesn't initialize services
        with patch('src.presentation.cli.command_handler.CommandHandler._initialize_services'):
            self.command_handler = CommandHandler()
            self.command_handler.dependency_container = self.mock_dependency_container
            self.command_handler.commands = {}  # Clear registered commands
    
    def test_register_command(self):
        """Test registering a command."""
        # Create a mock command class
        mock_command = MagicMock()
        mock_command.name = "test"
        mock_command.description = "Test command"
        mock_command_instance = MagicMock()
        mock_command_instance.name = "test"
        mock_command_instance.description = "Test command"
        mock_command.return_value = mock_command_instance
        
        # Register the command
        with patch('src.presentation.cli.command_handler.CommandHandler.register_command') as mock_register:
            self.command_handler.register_command(mock_command)
            mock_register.assert_called_once()
    
    def test_handle_command_no_command(self):
        """Test handling no command."""
        # Set up arguments
        args = []
        
        # Mock parser.parse_args to return an object with no command
        mock_args = MagicMock()
        mock_args.command = None
        self.command_handler.parser.parse_args = MagicMock(return_value=mock_args)
        
        # Handle command
        with patch('src.presentation.cli.command_handler.CommandHandler.parser.print_help') as mock_print_help:
            result = self.command_handler.handle_command(args)
            
            # Assertions
            self.assertEqual(result, 1)
            mock_print_help.assert_called_once()
    
    def test_handle_command_invalid_command(self):
        """Test handling an invalid command."""
        # Set up arguments
        args = ["invalid"]
        
        # Mock parser.parse_args to return an object with an invalid command
        mock_args = MagicMock()
        mock_args.command = "invalid"
        self.command_handler.parser.parse_args = MagicMock(return_value=mock_args)
        
        # Handle command
        with patch('builtins.print') as mock_print:
            result = self.command_handler.handle_command(args)
            
            # Assertions
            self.assertEqual(result, 1)
            mock_print.assert_called_once_with("Error: Command not found: invalid")
    
    def test_handle_command_success(self):
        """Test handling a valid command."""
        # Set up arguments
        args = ["test"]
        
        # Mock parser.parse_args to return an object with a valid command
        mock_args = MagicMock()
        mock_args.command = "test"
        self.command_handler.parser.parse_args = MagicMock(return_value=mock_args)
        
        # Create a mock command that returns success
        mock_command_class = MagicMock()
        mock_command_instance = MagicMock()
        mock_command_instance.execute.return_value = {"success": True}
        mock_command_class.return_value = mock_command_instance
        
        # Register the command
        self.command_handler.commands["test"] = mock_command_class
        
        # Handle command
        result = self.command_handler.handle_command(args)
        
        # Assertions
        self.assertEqual(result, 0)
        mock_command_instance.execute.assert_called_once()
    
    def test_handle_command_failure(self):
        """Test handling a valid command that fails."""
        # Set up arguments
        args = ["test"]
        
        # Mock parser.parse_args to return an object with a valid command
        mock_args = MagicMock()
        mock_args.command = "test"
        self.command_handler.parser.parse_args = MagicMock(return_value=mock_args)
        
        # Create a mock command that returns failure
        mock_command_class = MagicMock()
        mock_command_instance = MagicMock()
        mock_command_instance.execute.return_value = {"success": False}
        mock_command_class.return_value = mock_command_instance
        
        # Register the command
        self.command_handler.commands["test"] = mock_command_class
        
        # Handle command
        result = self.command_handler.handle_command(args)
        
        # Assertions
        self.assertEqual(result, 1)
        mock_command_instance.execute.assert_called_once()
    
    def test_handle_command_exception(self):
        """Test handling a command that raises an exception."""
        # Set up arguments
        args = ["test"]
        
        # Mock parser.parse_args to return an object with a valid command
        mock_args = MagicMock()
        mock_args.command = "test"
        self.command_handler.parser.parse_args = MagicMock(return_value=mock_args)
        
        # Create a mock command that raises an exception
        mock_command_class = MagicMock()
        mock_command_instance = MagicMock()
        mock_command_instance.execute.side_effect = Exception("Test exception")
        mock_command_class.return_value = mock_command_instance
        
        # Register the command
        self.command_handler.commands["test"] = mock_command_class
        
        # Handle command
        with patch('builtins.print') as mock_print:
            result = self.command_handler.handle_command(args)
            
            # Assertions
            self.assertEqual(result, 1)
            mock_command_instance.execute.assert_called_once()
            mock_print.assert_called_once_with("Error: Test exception")


class TestAnalyzeTicketCommand(unittest.TestCase):
    """Test cases for the AnalyzeTicketCommand class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the dependency container
        self.mock_dependency_container = MagicMock()
        
        # Create mock services
        self.mock_analyze_ticket_use_case = MagicMock()
        self.mock_dependency_container.resolve.return_value = self.mock_analyze_ticket_use_case
        
        # Create the command
        self.command = AnalyzeTicketCommand(self.mock_dependency_container)
    
    def test_execute_missing_target(self):
        """Test executing without specifying tickets to analyze."""
        # Set up arguments
        args = {}
        
        # Execute command
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
            
            # Assertions
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "No tickets specified for analysis")
            mock_print.assert_called()
    
    def test_execute_analyze_ticket(self):
        """Test analyzing a specific ticket."""
        # Set up arguments
        args = {"ticket_id": 12345}
        
        # Mock analyze_ticket to return a successful analysis
        mock_analysis = MagicMock()
        mock_analysis.sentiment = "positive"
        mock_analysis.category = "hardware"
        mock_analysis.priority = 5
        mock_analysis.hardware_components = ["keyboard", "monitor"]
        mock_analysis.to_dict.return_value = {
            "ticket_id": 12345,
            "sentiment": "positive",
            "category": "hardware",
            "priority": 5,
            "hardware_components": ["keyboard", "monitor"]
        }
        self.mock_analyze_ticket_use_case.analyze_ticket.return_value = mock_analysis
        
        # Execute command
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertEqual(result["ticket_id"], 12345)
            self.mock_analyze_ticket_use_case.analyze_ticket.assert_called_once_with(
                ticket_id=12345,
                add_comment=False,
                add_tags=False
            )
            mock_print.assert_called()


class TestListViewsCommand(unittest.TestCase):
    """Test cases for the ListViewsCommand class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the dependency container
        self.mock_dependency_container = MagicMock()
        
        # Create mock repository
        self.mock_repository = MagicMock()
        self.mock_dependency_container.resolve.return_value = self.mock_repository
        
        # Create the command
        self.command = ListViewsCommand(self.mock_dependency_container)
    
    def test_execute(self):
        """Test executing the command."""
        # Set up arguments
        args = {"format": "text"}
        
        # Mock get_all_views to return a list of views
        self.mock_repository.get_all_views.return_value = [
            {"id": 1, "title": "View 1", "active": True, "parent_id": None},
            {"id": 2, "title": "View 2", "active": True, "parent_id": 1},
            {"id": 3, "title": "View 3", "active": False, "parent_id": None}
        ]
        
        # Execute command
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertEqual(result["views_count"], 3)
            self.mock_repository.get_all_views.assert_called_once()
            mock_print.assert_called()


class TestGenerateReportCommand(unittest.TestCase):
    """Test cases for the GenerateReportCommand class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the dependency container
        self.mock_dependency_container = MagicMock()
        
        # Create mock use case
        self.mock_generate_report_use_case = MagicMock()
        self.mock_dependency_container.resolve.return_value = self.mock_generate_report_use_case
        
        # Create the command
        self.command = GenerateReportCommand(self.mock_dependency_container)
    
    def test_execute_sentiment_report(self):
        """Test generating a sentiment report."""
        # Set up arguments
        args = {
            "type": "sentiment",
            "days": 7,
            "format": "text"
        }
        
        # Mock generate_sentiment_report to return a report
        self.mock_generate_report_use_case.generate_sentiment_report.return_value = "Sentiment report content"
        
        # Execute command
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertEqual(result["report_type"], "sentiment")
            self.mock_generate_report_use_case.generate_sentiment_report.assert_called_once()
            mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
