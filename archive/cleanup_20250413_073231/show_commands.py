#!/usr/bin/env python3
"""
Show available commands for the Zendesk AI Integration CLI.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    # Print header
    print("Zendesk AI Integration - Available Commands")
    print("===========================================")
    print("\nThese are the available commands and their options:\n")
    
    # Define commands and their options
    commands = {
        "views": [
            "--format [text|json|csv]",
            "--output FILE",
            "--flat",
            "--include-inactive",
            "--filter STRING"
        ],
        "analyze": [
            "--ticket-id INTEGER",
            "--view-id INTEGER",
            "--ai-provider [openai|claude]",
            "--days INTEGER",
            "--limit INTEGER",
            "--add-comments",
            "--add-tags",
            "--output [json|text]",
            "--output-file TEXT"
        ],
        "report": [
            "--type [sentiment|enhanced-sentiment|hardware|pending|multi-view]",
            "--view-id INTEGER",
            "--view-name TEXT",
            "--view-ids TEXT",
            "--view-names TEXT",
            "--days INTEGER",
            "--limit INTEGER",
            "--format [text|html|json|csv]",
            "--output TEXT",
            "--enhanced"
        ],
        "interactive": [],
        "webhook": [
            "--start",
            "--stop",
            "--status",
            "--host TEXT",
            "--port INTEGER",
            "--endpoint TEXT",
            "--auto-analyze",
            "--ai-provider [openai|claude]"
        ],
        "schedule": [
            "--list",
            "--add",
            "--remove",
            "--task [analyze_pending|generate_report]",
            "--view-id INTEGER",
            "--time TEXT",
            "--interval [daily|weekly|monthly]",
            "--params TEXT",
            "--id INTEGER"
        ]
    }
    
    # Print commands and their options
    for command, options in commands.items():
        print(f"python -m src.main {command}")
        if options:
            print("  Options:")
            for option in options:
                print(f"    {option}")
        print()
    
    # Print global options
    print("Global Options:")
    print("  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]")
    print("  --log-file TEXT")
    print("  --config-file TEXT")
    print()
    
    # Print examples
    print("Examples:")
    print("  python -m src.main views")
    print("  python -m src.main analyze --ticket-id 12345")
    print("  python -m src.main analyze --view-id 67890 --limit 10")
    print("  python -m src.main report --type sentiment --days 7")
    print("  python -m src.main interactive")
    print("  python -m src.main webhook --start --host 0.0.0.0 --port 8000")
    print("  python -m src.main schedule --list")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
