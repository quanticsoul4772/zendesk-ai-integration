#!/usr/bin/env python
"""
Test runner with automatic mocking environment setup.

This script provides a convenient way to run tests with the proper mocking environment
automatically configured.

Usage:
    python run_tests.py [pytest_args]

Examples:
    python run_tests.py tests/unit/test_ai_service.py -v
    python run_tests.py tests/integration/test_sentiment_analysis_mock.py -v --log-cli-level=INFO
"""

import os
import sys
import subprocess
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)8s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up the test environment variables."""
    # Set environment variables for testing
    os.environ["OPENAI_API_KEY"] = "sk-test-123456789abcdef"
    os.environ["ANTHROPIC_API_KEY"] = "anthro-test-123456789abcdef"
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
    os.environ["MONGODB_DB_NAME"] = "test_db"
    os.environ["MONGODB_COLLECTION_NAME"] = "test_collection"
    os.environ["PYTEST_MOCK_ENABLED"] = "1"  # Custom flag to enable mocking
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    logger.info("Test environment set up successfully")

def run_tests(pytest_args):
    """Run the tests with the specified pytest arguments."""
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Run pytest with the specified arguments
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed with exit code {e.returncode}")
        return e.returncode

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests with automatic mock configuration")
    parser.add_argument("pytest_args", nargs="*", help="Arguments to pass to pytest")
    parser.add_argument("--verbose", "-v", action="store_true", help="Increase verbosity")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      help="Set the logging level")
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Configure logging based on args
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Set up the test environment
    setup_test_environment()
    
    # Build pytest arguments
    pytest_args = args.pytest_args
    if args.verbose and "-v" not in pytest_args:
        pytest_args.append("-v")
    
    # Run the tests
    exit_code = run_tests(pytest_args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
