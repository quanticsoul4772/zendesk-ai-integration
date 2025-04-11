#!/bin/bash
# Launcher shell script for Zendesk AI Integration interactive menu

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Running with system Python."
fi

# Run the menu launcher
python zendesk_menu.py

# If in virtual environment, deactivate
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
