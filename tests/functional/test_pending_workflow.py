"""
Functional Tests for 'pending' mode workflows

Tests the complete workflow for the 'pending' report command-line interface.
"""

import pytest
import os
import sys
import io
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the main application entry point
from src.zendesk_ai_app import main


class TestPendingWorkflow:
    """Test suite for the 'pending' mode workflow."""
    
    def test_pending_mode_basic_workflow(self):
        """Test the basic 'pending' mode workflow."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_pending_mode method
        cli = CommandLineInterface()
        cli._handle_pending_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "pending"
        mock_args.pending_view = "12345"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {"pending": MagicMock()}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_pending_mode was called
        cli._handle_pending_mode.assert_called_once()
        
        # Get the actual call arguments
        args, kwargs = cli._handle_pending_mode.call_args
        
        # Verify the first argument is the mock_args
        assert args[0] == mock_args
    
    def test_pending_mode_with_view_name(self):
        """Test 'pending' mode with view name instead of ID."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_pending_mode method
        cli = CommandLineInterface()
        cli._handle_pending_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "pending"
        mock_args.pending_view = "Pending Support"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {"pending": MagicMock()}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_pending_mode was called with mock_args
        cli._handle_pending_mode.assert_called_once()
        args, kwargs = cli._handle_pending_mode.call_args
        assert args[0] == mock_args
    
    def test_pending_mode_with_limit_parameter(self):
        """Test 'pending' mode with limit parameter."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with a mocked _handle_pending_mode method
        cli = CommandLineInterface()
        cli._handle_pending_mode = MagicMock(return_value=True)
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "pending"
        mock_args.pending_view = "12345"
        mock_args.limit = 3
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {"pending": MagicMock()}
        
        # Call execute directly
        result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
        
        # Verify the result
        assert result == True
        
        # Verify that _handle_pending_mode was called with mock_args containing the limit
        cli._handle_pending_mode.assert_called_once()
        args, kwargs = cli._handle_pending_mode.call_args
        assert args[0] == mock_args
        assert args[0].limit == 3
    
    def test_pending_mode_with_output_file(self):
        """Test 'pending' mode with output to file."""
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Get the actual CommandLineInterface class
            from src.modules.cli import CommandLineInterface
            
            # Create a mock instance with a mocked _handle_pending_mode method
            cli = CommandLineInterface()
            cli._handle_pending_mode = MagicMock(return_value=True)
            
            # Create mock dependencies
            mock_args = MagicMock()
            mock_args.mode = "pending"
            mock_args.pending_view = "12345"
            mock_args.output = output_path
            
            mock_zendesk = MagicMock()
            mock_ai = MagicMock()
            mock_db = MagicMock()
            mock_report_modules = {"pending": MagicMock()}
            
            # Call execute directly
            result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
            
            # Verify the result
            assert result == True
            
            # Verify that _handle_pending_mode was called with mock_args containing the output path
            cli._handle_pending_mode.assert_called_once()
            args, kwargs = cli._handle_pending_mode.call_args
            assert args[0] == mock_args
            assert args[0].output == output_path
        
        finally:
            # Clean up temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_pending_mode_missing_view_parameter(self):
        """Test 'pending' mode without required view parameter."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance
        cli = CommandLineInterface()
        cli._handle_pending_mode = MagicMock(side_effect=ValueError("Pending view is required"))
        
        # Create mock dependencies with missing view parameter
        mock_args = MagicMock()
        mock_args.mode = "pending"
        mock_args.pending_view = None
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {"pending": MagicMock()}
        
        # Set up mocks
        with patch('logging.error') as mock_logger_error:
            # Call execute and expect it to return False
            result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
            
            # Verify the result is False (failure)
            assert result == False
            
            # Verify that _handle_pending_mode was called
            cli._handle_pending_mode.assert_called_once()
    
    def test_pending_mode_error_handling(self):
        """Test error handling in 'pending' mode workflow."""
        # Get the actual CommandLineInterface class
        from src.modules.cli import CommandLineInterface
        
        # Create a mock instance with an error-raising method
        cli = CommandLineInterface()
        cli._handle_pending_mode = MagicMock(side_effect=Exception("Test error"))
        
        # Create mock dependencies
        mock_args = MagicMock()
        mock_args.mode = "pending"
        mock_args.pending_view = "12345"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        mock_report_modules = {"pending": MagicMock()}
        
        # Set up mocks
        with patch('logging.exception') as mock_logger_exception:
            # Call execute with error logging mocked
            result = cli.execute(mock_args, mock_zendesk, mock_ai, mock_db, mock_report_modules)
            
            # Verify the result is False (failure)
            assert result == False
            
            # Verify that _handle_pending_mode was called
            cli._handle_pending_mode.assert_called_once()
