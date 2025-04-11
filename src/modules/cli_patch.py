"""
CLI Patch Module

This module provides updated functions for the CLI module to use
the unified sentiment reporter.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

def unified_reporter_init(args, format_arg, db_repository):
    """
    Initialize the unified sentiment reporter with the appropriate format setting.
    
    Args:
        args: Command line arguments
        format_arg: Format to use ("enhanced" or "standard")
        db_repository: Database repository instance
        
    Returns:
        Initialized reporter instance
    """
    from modules.reporters import SentimentReporter
    
    # Determine the mode based on format_arg
    enhanced_mode = format_arg == "enhanced"
    
    # Create the reporter with the appropriate settings
    return SentimentReporter(db_repository=db_repository, enhanced_mode=enhanced_mode)
