#!/bin/bash
# Multi-View Reports Launcher
# This script activates the virtual environment and runs the multi-view report generator.

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Attempting to run with system Python."
fi

# Run the script with all provided arguments
echo "Starting Multi-View Report Generator..."
python multi_view_reports.py "$@"

# Check for errors
if [ $? -ne 0 ]; then
    echo "An error occurred. See the log for details."
    read -p "Press Enter to continue..."
fi
