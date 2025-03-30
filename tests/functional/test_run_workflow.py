"""
Functional Tests for 'run' mode workflows

Tests the complete workflow for the 'run' mode command-line interface.
"""

import pytest
import os
import sys
import io
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the main application entry point
from src.zendesk_ai_app import main


class TestRunWorkflow:
    """Test suite for the 'run' mode workflow."""
    
    def test_run_mode_basic_workflow(self):
        """Test the basic 'run' mode workflow."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the first argument is the mock_args
        assert args[0] == mock_args
    
    def test_run_mode_with_status_parameter(self):
        """Test 'run' mode with specific status parameter."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.status = "pending"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the status parameter
        assert args[0] == mock_args
        assert args[0].status == "pending"
    
    def test_run_mode_with_view_parameter(self):
        """Test 'run' mode with view parameter."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.view = "12345"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the view parameter
        assert args[0] == mock_args
        assert args[0].view == "12345"
    
    def test_run_mode_with_limit_parameter(self):
        """Test 'run' mode with limit parameter."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.limit = 5
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the limit parameter
        assert args[0] == mock_args
        assert args[0].limit == 5
    
    def test_run_mode_with_component_report(self):
        """Test 'run' mode with component report generation."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.component_report = True
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        
        # Create a mock hardware reporter module
        mock_hardware_reporter = MagicMock()
        mock_report_modules = {"hardware": mock_hardware_reporter}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the component_report parameter
        assert args[0] == mock_args
        assert args[0].component_report == True
    
    def test_run_mode_with_ai_service_selection(self):
        """Test 'run' mode with AI service selection."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_run_mode method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(return_value=True)
        
        # Test with OpenAI (--use-openai parameter)
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.use_openai = True
        mock_args.use_claude = False
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the AI service parameters
        assert args[0] == mock_args
        assert args[0].use_openai == True
        
        # Reset mock for Claude test
        cli._handle_run_mode.reset_mock()
        
        # Test with Claude (default)
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        mock_args.use_openai = False
        mock_args.use_claude = True
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_run_mode was called
        cli._handle_run_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_run_mode.call_args
        
        # Verify the arguments contain the AI service parameters
        assert args[0] == mock_args
        assert args[0].use_claude == True
        assert args[0].use_openai == False
    
    def test_run_mode_error_handling(self):
        """Test error handling in 'run' mode workflow."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with an error-raising method
        cli = CommandLineInterface()
        cli._handle_run_mode = MagicMock(side_effect=Exception("Test error"))
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "run"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {}
        
        # Set up mocks
        with patch('logging.exception') as mock_logger_exception:
            # Call execute with error logging mocked
            result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
            
            # Verify the result is False (failure)
            assert result == False
            
            # Verify that _handle_run_mode was called
            cli._handle_run_mode.assert_called_once()
