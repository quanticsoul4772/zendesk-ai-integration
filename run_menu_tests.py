#!/usr/bin/env python3
"""
Test runner script for interactive menu tests.

This script runs the tests specifically for the interactive menu system.
"""

import os
import sys
import subprocess
import argparse

def main():
    """Run the interactive menu tests."""
    parser = argparse.ArgumentParser(description="Run tests for the interactive menu.")
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help="Increase verbosity level (use -v, -vv, or -vvv)")
    parser.add_argument("--coverage", "-c", action="store_true",
                        help="Run tests with coverage report")
    args = parser.parse_args()
    
    # Determine the pytest command
    pytest_cmd = ["pytest"]
    
    # Add verbosity flags
    if args.verbose > 0:
        pytest_cmd.extend(["-" + "v" * args.verbose])
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend(["--cov=src.modules.menu", "--cov-report=term", "--cov-report=html"])
    
    # Add the test files
    pytest_cmd.extend([
        "tests/test_interactive_menu.py",
        "tests/test_menu_actions.py",
        "tests/test_menu_comprehensive.py"
    ])
    
    # Print the command being run
    print(f"Running: {' '.join(pytest_cmd)}")
    
    # Run the tests
    result = subprocess.run(pytest_cmd)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
