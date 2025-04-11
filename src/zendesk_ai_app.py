#!/usr/bin/env python3
"""
Zendesk AI Integration Application

This is the main entry point for the Zendesk AI Integration application.
It coordinates between the various modules to provide the requested functionality.
"""

import os
import logging
import atexit
import sys
import time
import random
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zendesk_ai")

# Load environment variables
load_dotenv()

# Add the current directory to the Python path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# First ensure parent directory (project root) is in the path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Then add current directory (src)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Create a function to get a Zendesk client instance
def get_zendesk_client():
    """
    Get a Zendesk client instance for use outside the main function.
    
    Returns:
        A ZendeskClient instance
    """
    from modules.zendesk_client import ZendeskClient
    return ZendeskClient().client

# Add a utility function for exponential backoff retries
def exponential_backoff_retry(func, *args, max_retries=5, base_delay=2.0, max_delay=30.0, **kwargs):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The function to retry
        *args: Arguments to pass to the function
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function call
    
    Raises:
        The last exception encountered if all retries fail
    """
    last_exception = None
    
    for retry in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # Calculate delay with jitter to avoid thundering herd
            delay = min(max_delay, base_delay * (2 ** retry))
            jitter = random.uniform(0, delay / 2)
            total_delay = delay + jitter
            
            logger.warning(f"Retry {retry+1}/{max_retries} after {total_delay:.2f}s due to: {e}")
            time.sleep(total_delay)
    
    # If we've exhausted all retries, raise the last exception
    raise last_exception

def main():
    """Main entry point for the application."""
    try:
        # Import modules from the modular structure using absolute imports
        from modules.zendesk_client import ZendeskClient
        from modules.ai_analyzer import AIAnalyzer
        from modules.db_repository import DBRepository
        from modules.cli import CommandLineInterface
        from modules.reporters.hardware_report import HardwareReporter
        from modules.reporters.pending_report import PendingReporter
        
        # Initialize components
        zendesk_client = ZendeskClient()
        ai_analyzer = AIAnalyzer()
        db_repository = DBRepository()
        
        # Initialize report modules and import SentimentReporter
        from modules.reporters.sentiment_report import SentimentReporter
        from modules.reporters.enhanced_sentiment_report import EnhancedSentimentReporter
        
        report_modules = {
            "hardware": HardwareReporter(),
            "pending": PendingReporter(),
            "sentiment": SentimentReporter(),
            "sentiment_enhanced": EnhancedSentimentReporter()
        }
        
        # Register function to close MongoDB connections on exit
        atexit.register(db_repository.close)
        
        # Parse command-line arguments and execute the requested mode
        cli = CommandLineInterface()
        args = cli.parse_args()
        
        logger.info(f"Starting Zendesk AI Integration in {args.mode} mode")
        
        # For webhook mode, we need to pass the add_comments preference
        if args.mode == "webhook":
            from modules.webhook_server import WebhookServer
            webhook_server = WebhookServer(
                zendesk_client=zendesk_client,
                ai_analyzer=ai_analyzer,
                db_repository=db_repository
            )
            # Explicitly set comment preference to False unless requested
            webhook_server.set_comment_preference(args.add_comments)
            webhook_server.run(host=args.host, port=args.port)
            return 0
        
        # For other modes, use the CLI executor
        success = cli.execute(args, zendesk_client, ai_analyzer, db_repository, report_modules)
        
        if success:
            logger.info(f"Successfully completed {args.mode} mode")
            return 0
        else:
            logger.error(f"Failed to complete {args.mode} mode")
            return 1
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all required packages are installed. Run: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
    finally:
        # Ensure any cleanup happens
        try:
            # Initialize db_repository to None to avoid unbound variable warning
            db_repository = None
            
            # Check if db_repository was created and close it if it exists
            if 'db_repository' in locals() and db_repository is not None:
                db_repository.close()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
