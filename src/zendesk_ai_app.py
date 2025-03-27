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
if current_dir not in sys.path:
    sys.path.append(current_dir)

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
        
        # Initialize report modules
        report_modules = {
            "hardware": HardwareReporter(),
            "pending": PendingReporter(),
            "sentiment": None  # Will be initialized on demand
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
