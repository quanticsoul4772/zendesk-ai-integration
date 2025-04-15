#!/usr/bin/env python3
"""
Create the run_zendesk_ai.sh script for Linux environments.
This script can be run directly on Linux to generate the runner script.
"""

import os
from pathlib import Path

def create_run_script():
    """Create the run_zendesk_ai.sh script"""
    print("Creating run_zendesk_ai.sh script...")
    
    # Define the script path
    script_path = Path("run_zendesk_ai.sh")
    
    # Write the script content
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("# Run the Zendesk AI Integration application\n\n")
        f.write("# Activate virtual environment if it exists\n")
        f.write("if [ -d \"venv\" ]; then\n")
        f.write("    source venv/bin/activate\n")
        f.write("fi\n\n")
        f.write("# Run the application with all arguments passed to this script\n")
        f.write("python3 src/zendesk_ai_app.py \"$@\"\n")
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    print(f"Created {script_path} successfully!")
    print(f"You can now run the application with: ./{script_path} --mode list-views")

if __name__ == "__main__":
    create_run_script()
