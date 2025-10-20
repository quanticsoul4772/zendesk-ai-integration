"""
Unit Tests for Command Line Interface Module

Tests the functionality of the cli.py module.
"""

# SKIPPED: This test file tests modules that were removed during clean architecture refactoring.
# Reason: CommandLineInterface module removed - replaced with command pattern in src/presentation/cli
# To enable this test, the test would need to be rewritten to test the new architecture.

import pytest
pytestmark = pytest.mark.skip(reason="CommandLineInterface module removed - replaced with command pattern in src/presentation/cli")


import pytest
from unittest.mock import patch, MagicMock, call
import sys
import argparse

# Import module to test
# from src.modules.cli import CommandLineInterface


class TestCommandLineInterface:
    """Test suite for Command Line Interface functionality."""
    
    def test_init(self):
        """Test CLI initialization."""
        cli = CommandLineInterface()
        assert cli is not None
    
    def test_parse_args_defaults(self):
        """Test argument parsing with default values."""
        cli = CommandLineInterface()
        
        # Test with minimal arguments
        with patch.object(sys, 'argv', ['zendesk_ai_app.py', '--mode', 'run']):
            args = cli.parse_args()
            
            # Check defaults are set correctly
            assert args.mode == 'run'
            assert args.status == 'open'  # Default status
            assert args.days is None
            assert args.limit is None  # No default limit
            assert args.view is None
            assert args.add_comments is False
            assert args.use_openai is False
    
    def test_parse_args_full(self):
        """Test argument parsing with all parameters specified."""
        cli = CommandLineInterface()
        
        # Test with all arguments specified
        with patch.object(sys, 'argv', [
            'zendesk_ai_app.py',
            '--mode', 'sentiment',
            '--status', 'pending',
            '--days', '7',
            '--limit', '50',
            '--view', '12345',
            '--add-comments',
            '--use-openai',
            '--output', 'test_output.txt'
        ]):
            args = cli.parse_args()
            
            # Check all values are parsed correctly
            assert args.mode == 'sentiment'
            assert args.status == 'pending'
            assert args.days == 7
            assert args.limit == 50
            assert args.view == '12345'  # View ID is parsed as string
            assert args.add_comments is True
            assert args.use_openai is True
            assert args.output == 'test_output.txt'
    
    def test_parse_args_sentiment_mode(self):
        """Test parsing arguments specific to sentiment mode."""
        cli = CommandLineInterface()
        
        # Test with sentiment mode arguments
        with patch.object(sys, 'argv', [
            'zendesk_ai_app.py',
            '--mode', 'sentiment',
            '--days', '7',
            '--format', 'enhanced',
            '--views', '12345,67890'
        ]):
            args = cli.parse_args()
            
            # Check sentiment-specific values
            assert args.mode == 'sentiment'
            assert args.days == 7
            assert args.format == 'enhanced'
            assert args.views == '12345,67890'
    
    def test_execute_run_mode(self):
        """Test execution in 'run' mode."""
        cli = CommandLineInterface()
        
        # Create mock dependencies
        mock_zendesk = MagicMock()
        mock_ai_analyzer = MagicMock()
        mock_db_repository = MagicMock()
        mock_report_modules = {}
        
        # Configure mocks
        mock_zendesk.fetch_tickets.return_value = [MagicMock() for _ in range(3)]
        mock_ai_analyzer.analyze_tickets_batch.return_value = [{'ticket_id': '1'}, {'ticket_id': '2'}, {'ticket_id': '3'}]
        
        # Create args
        args = argparse.Namespace(
            mode='run',
            status='open',
            days=None,
            limit=10,
            view=None,
            views=None,
            view_name=None,
            view_names=None,
            use_openai=False,
            use_claude=True,
            component_report=False
        )
        
        # Execute CLI
        with patch.object(cli, '_handle_run_mode', return_value=True) as mock_handle_run_mode:
            result = cli.execute(args, mock_zendesk, mock_ai_analyzer, mock_db_repository, mock_report_modules)
            
            # Verify calls
            assert result is True
            mock_handle_run_mode.assert_called_once()
    
    def test_execute_sentiment_mode(self):
        """Test execution in 'sentiment' mode."""
        cli = CommandLineInterface()
        
        # Create mock dependencies
        mock_zendesk = MagicMock()
        mock_ai_analyzer = MagicMock()
        mock_db_repository = MagicMock()
        
        # Mock reporter
        mock_reporter = MagicMock()
        mock_report_modules = {'sentiment': mock_reporter}
        
        # Create args
        args = argparse.Namespace(
            mode='sentiment',
            days=7,
            status=None,
            view=None,
            views=None,
            view_name=None,
            view_names=None,
            format='standard',
            output=None,
            use_openai=False,
            use_claude=True
        )
        
        # Execute CLI
        with patch.object(cli, '_handle_sentiment_mode', return_value=True) as mock_handle_sentiment_mode:
            result = cli.execute(args, mock_zendesk, mock_ai_analyzer, mock_db_repository, mock_report_modules)
            
            # Verify calls
            assert result is True
            mock_handle_sentiment_mode.assert_called_once()
    
    def test_execute_invalid_mode(self):
        """Test execution with invalid mode."""
        cli = CommandLineInterface()
        
        # Create mock dependencies
        mock_zendesk = MagicMock()
        mock_ai_analyzer = MagicMock()
        mock_db_repository = MagicMock()
        mock_report_modules = {}
        
        # Create args with invalid mode
        args = argparse.Namespace(
            mode='invalid_mode',
            use_openai=False,
            use_claude=True
        )
        
        # Mock logger to not raise an exception
        with patch('src.modules.cli.logger.error') as mock_log:
            # Execute CLI and verify it returns False
            result = cli.execute(args, mock_zendesk, mock_ai_analyzer, mock_db_repository, mock_report_modules)
            assert result is False
            mock_log.assert_called_once_with("Unknown mode: invalid_mode")
    
    def test_execute_error_handling(self):
        """Test error handling during execution."""
        cli = CommandLineInterface()
        
        # Create mock dependencies
        mock_zendesk = MagicMock()
        mock_ai_analyzer = MagicMock()
        mock_db_repository = MagicMock()
        mock_report_modules = {}
        
        # Create args
        args = argparse.Namespace(
            mode='run',
            status='open',
            days=None,
            limit=10,
            view=None,
            views=None,
            view_name=None,
            view_names=None,
            use_openai=False,
            use_claude=True,
            component_report=False
        )
        
        # Execute CLI and verify error handling
        with patch.object(cli, '_handle_run_mode', side_effect=Exception("Test error")) as mock_handle_run_mode:
            with patch('src.modules.cli.logger.exception') as mock_log:
                result = cli.execute(args, mock_zendesk, mock_ai_analyzer, mock_db_repository, mock_report_modules)
                assert result is False
                mock_log.assert_called_once()
