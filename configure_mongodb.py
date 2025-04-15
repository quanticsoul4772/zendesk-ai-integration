#!/usr/bin/env python3
"""
MongoDB Configuration Script for Zendesk AI Integration

This script provides a standalone tool for configuring MongoDB.
It can be run independently to set up or reconfigure MongoDB.

Usage:
  python configure_mongodb.py
"""

import os
import sys
import re
from pathlib import Path

# Import the MongoDB setup module
try:
    from install_mongodb import setup_mongodb_configuration, Colors, print_status
except ImportError:
    print("Error: Cannot import from install_mongodb.py. Make sure it exists in the same directory.")
    sys.exit(1)

def update_env_file(mongodb_config):
    """Update the MongoDB settings in the .env file."""
    env_file = Path(".env")
    if not env_file.exists():
        print_status(".env file not found", "ERROR")
        print("Creating a new .env file with MongoDB settings...")
        
        # Create a minimal .env file with just MongoDB settings
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"# MongoDB Configuration\n")
            f.write(f"MONGODB_URI={mongodb_config['uri']}\n")
            f.write(f"MONGODB_DB_NAME={mongodb_config['database_name']}\n")
            
        print_status("Created a new .env file with MongoDB settings", "SUCCESS")
        return True
    
    # Update existing .env file
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            env_content = f.read()
        
        # Update MongoDB URI
        if "MONGODB_URI=" in env_content:
            env_content = re.sub(r'MONGODB_URI=.*', f'MONGODB_URI={mongodb_config["uri"]}', env_content)
        else:
            env_content += f"\nMONGODB_URI={mongodb_config['uri']}\n"
        
        # Update MongoDB DB name
        if "MONGODB_DB_NAME=" in env_content:
            env_content = re.sub(r'MONGODB_DB_NAME=.*', f'MONGODB_DB_NAME={mongodb_config["database_name"]}', env_content)
        else:
            env_content += f"MONGODB_DB_NAME={mongodb_config['database_name']}\n"
        
        # Write updated .env file
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
            
        print_status("MongoDB configuration updated in .env file", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Error updating .env file: {str(e)}", "ERROR")
        return False

def print_mongodb_management_info():
    """Print information about MongoDB management if using Docker."""
    if Path("mongodb").exists():
        print(f"\n{Colors.BOLD}MongoDB Management{Colors.END}")
        print("You can manage your MongoDB Docker container using the provided scripts:")
        
        if os.name == 'nt':  # Windows
            print("  mongodb.bat start    - Start the MongoDB container")
            print("  mongodb.bat stop     - Stop the MongoDB container")
            print("  mongodb.bat restart  - Restart the MongoDB container")
            print("  mongodb.bat status   - Check the MongoDB container status")
        else:  # Unix (Linux/macOS)
            print("  ./mongodb.sh start    - Start the MongoDB container")
            print("  ./mongodb.sh stop     - Stop the MongoDB container")
            print("  ./mongodb.sh restart  - Restart the MongoDB container")
            print("  ./mongodb.sh status   - Check the MongoDB container status")

def main():
    """Main function for MongoDB configuration."""
    print(f"\n{Colors.BOLD}MongoDB Configuration Utility{Colors.END}")
    print("This script will help you set up or reconfigure MongoDB for the Zendesk AI Integration.")
    
    # Run the MongoDB setup
    mongodb_config = setup_mongodb_configuration()
    
    if mongodb_config:
        # Update the .env file with MongoDB settings
        update_env_file(mongodb_config)
        
        # Print management info if using Docker
        print_mongodb_management_info()
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}MongoDB configuration completed successfully!{Colors.END}")
    else:
        print(f"\n{Colors.RED}MongoDB configuration failed or was canceled.{Colors.END}")
        print("Please check the error messages and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
