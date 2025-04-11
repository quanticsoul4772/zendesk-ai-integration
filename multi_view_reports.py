#!/usr/bin/env python3
"""
Multi-View Report Generator

This script provides an interactive interface for selecting multiple Zendesk views
and generating combined reports across them.

Usage:
    python multi_view_reports.py [--mode {pending,sentiment,enhanced}]
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main entry point for the multi-view report generator."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Multi-View Report Generator")
    parser.add_argument("--mode", choices=["pending", "sentiment", "enhanced"],
                      help="Report mode to use (default: choose interactively)",
                      default=None)
    args = parser.parse_args()
    
    # Add the src directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    try:
        # Import required modules
        from src.modules.zendesk_client import ZendeskClient
        from src.modules.ai_analyzer import AIAnalyzer
        from src.modules.db_repository import DBRepository
        from src.modules.menu.multi_view_selector import MultiViewSelector
        
        # Initialize components
        zendesk_client = ZendeskClient()
        ai_analyzer = AIAnalyzer()
        db_repository = DBRepository()
        
        # Import report modules
        report_modules = {}
        
        try:
            from src.modules.reporters.pending_report import PendingReporter
            report_modules["pending"] = PendingReporter()
            logger.info("Loaded pending reporter module")
        except ImportError as e:
            logger.warning(f"Could not load pending reporter: {e}")
        
        try:
            from src.modules.reporters.sentiment_report import SentimentReporter
            report_modules["sentiment"] = SentimentReporter()
            logger.info("Loaded sentiment reporter module")
        except ImportError as e:
            logger.warning(f"Could not load sentiment reporter: {e}")
            
        try:
            from src.modules.reporters.enhanced_sentiment_report import EnhancedSentimentReporter
            report_modules["sentiment_enhanced"] = EnhancedSentimentReporter()
            logger.info("Loaded enhanced sentiment reporter module")
        except ImportError as e:
            logger.warning(f"Could not load enhanced sentiment reporter: {e}")
        
        # Initialize the multi-view selector
        selector = MultiViewSelector(zendesk_client, db_repository)
        
        # If mode is not specified, ask user
        mode = args.mode
        if not mode:
            print("\nPlease select a report type:")
            print("1. Pending Report")
            print("2. Basic Sentiment Analysis")
            print("3. Enhanced Sentiment Analysis")
            
            while True:
                choice = input("\nEnter your choice (1-3): ").strip()
                if choice == "1":
                    mode = "pending"
                    break
                elif choice == "2":
                    mode = "sentiment"
                    break
                elif choice == "3":
                    mode = "enhanced"
                    break
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
        
        # Display view selector with appropriate message
        message = f"Select views for {mode.capitalize()} Report"
        selected_view_ids, selected_view_names = selector.display_view_selector(message)
        
        if not selected_view_ids:
            print("\nNo views selected. Exiting.")
            return 0
        
        # Generate the report
        print(f"\nGenerating {mode} report for {len(selected_view_ids)} views...")
        selector.generate_multi_view_report(
            selected_view_ids,
            mode,
            ai_analyzer=ai_analyzer,
            report_modules=report_modules
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user. Exiting...")
        return 1
    except Exception as e:
        logger.exception(f"Error in multi-view report generator: {e}")
        print(f"\nAn error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
