#!/usr/bin/env python3
"""
Setup Script for Zendesk AI Integration

This script automates the installation and initial setup of the Zendesk AI Integration.
It will:
1. Check prerequisites
2. Create a virtual environment
3. Install dependencies
4. Set up initial configuration
5. Verify the installation

Usage:
  python setup.py
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import getpass
import re
import random
import string
import time
import json

# Terminal colors for better readability
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step_number, message):
    """Print a step message with color coding"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Step {step_number}: {message}{Colors.END}")

def print_status(message, status):
    """Print a status message with color coding"""
    status_color = {
        "SUCCESS": Colors.GREEN + "✓" + Colors.END,
        "WARNING": Colors.YELLOW + "⚠" + Colors.END,
        "ERROR": Colors.RED + "✗" + Colors.END,
        "INFO": Colors.BLUE + "ℹ" + Colors.END
    }
    
    print(f"{status_color[status]} {message}")

def run_command(command, shell=False):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_prerequisites():
    """Run the prerequisites check script"""
    print_step(1, "Checking prerequisites")
    
    prereq_script = Path("check_prerequisites.py")
    if not prereq_script.exists():
        print_status("Prerequisites check script not found", "ERROR")
        print("Please download the check_prerequisites.py script first.")
        return False
    
    success, output = run_command([sys.executable, "check_prerequisites.py"])
    print(output)
    
    # Check if critical prerequisites are missing
    if "Critical requirements missing!" in output:
        print_status("Critical prerequisites missing", "ERROR")
        print("Please address the issues above before continuing.")
        return False
    
    return True

def setup_virtual_environment():
    """Set up a Python virtual environment"""
    print_step(2, "Creating virtual environment")
    
    venv_dir = Path("venv")
    if venv_dir.exists():
        print_status("Virtual environment already exists", "INFO")
        choice = input("Do you want to recreate it? (y/n): ").lower()
        if choice == 'y':
            shutil.rmtree(venv_dir)
        else:
            print_status("Using existing virtual environment", "INFO")
            return True
    
    success, output = run_command([sys.executable, "-m", "venv", "venv"])
    
    if success:
        print_status("Virtual environment created successfully", "SUCCESS")
        return True
    else:
        print_status("Failed to create virtual environment", "ERROR")
        print(output)
        return False

def activate_virtual_environment():
    """Activate the virtual environment and return the Python path"""
    if platform.system() == "Windows":
        python_path = os.path.abspath("venv/Scripts/python.exe")
        pip_path = os.path.abspath("venv/Scripts/pip.exe")
    else:
        python_path = os.path.abspath("venv/bin/python")
        pip_path = os.path.abspath("venv/bin/pip")
    
    return python_path, pip_path

def install_dependencies(pip_path):
    """Install dependencies from requirements.txt"""
    print_step(3, "Installing dependencies")
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print_status("requirements.txt not found", "ERROR")
        return False
    
    print("Installing dependencies (this may take a few minutes)...")
    success, output = run_command([pip_path, "install", "-r", "requirements.txt"])
    
    if success:
        print_status("Dependencies installed successfully", "SUCCESS")
        return True
    else:
        print_status("Failed to install dependencies", "ERROR")
        print(output)
        return False

def verify_installation(python_path):
    """Verify the installation by running a simple test"""
    print_step(5, "Verifying installation")
    
    # Check if the main application file exists
    app_file = Path("src/zendesk_ai_app.py")
    if not app_file.exists():
        print_status("Main application file not found", "ERROR")
        return False
    
    # Try running the list-views command
    print("Testing the application by listing Zendesk views...")
    success, output = run_command([python_path, "src/zendesk_ai_app.py", "--mode", "list-views"])
    
    if success:
        print_status("Installation verified successfully", "SUCCESS")
        return True
    else:
        print_status("Verification failed", "WARNING")
        print("This might be due to incorrect Zendesk credentials or network issues.")
        print("You can try running the application manually later.")
        return False

def setup_configuration():
    """Set up the configuration (.env file)"""
    print_step(4, "Setting up configuration")
    
    env_file = Path(".env")
    example_env = Path(".env.example")
    
    if not example_env.exists():
        print_status(".env.example not found", "ERROR")
        return False
    
    if env_file.exists():
        print_status(".env file already exists", "INFO")
        choice = input("Do you want to reconfigure it? (y/n): ").lower()
        if choice != 'y':
            print_status("Using existing configuration", "INFO")
            return True
    
    # Read the example env file
    with open(example_env, "r") as f:
        env_content = f.read()
    
    # Get user input for configuration
    print("\nPlease provide the following information for your configuration:")
    
    # Zendesk credentials
    print(f"\n{Colors.BOLD}Zendesk API Credentials:{Colors.END}")
    zendesk_email = input("Zendesk Email: ")
    zendesk_api_token = getpass.getpass("Zendesk API Token: ")
    zendesk_subdomain = input("Zendesk Subdomain: ")
    
    # AI API keys
    print(f"\n{Colors.BOLD}AI API Keys (at least one is required):{Colors.END}")
    print("1. OpenAI API Key")
    print("2. Anthropic API Key")
    print("3. Both")
    ai_choice = input("Which AI service do you want to configure? (1/2/3): ")
    
    openai_key = ""
    anthropic_key = ""
    
    if ai_choice in ["1", "3"]:
        openai_key = getpass.getpass("OpenAI API Key: ")
    
    if ai_choice in ["2", "3"]:
        anthropic_key = getpass.getpass("Anthropic API Key: ")
    
    # MongoDB configuration
    print(f"\n{Colors.BOLD}MongoDB Configuration:{Colors.END}")
    print("1. Local MongoDB (mongodb://localhost:27017)")
    print("2. MongoDB Atlas (Cloud)")
    mongo_choice = input("Which MongoDB setup do you want to use? (1/2): ")
    
    if mongo_choice == "2":
        mongodb_uri = getpass.getpass("MongoDB Atlas URI (mongodb+srv://...): ")
    else:
        mongodb_uri = "mongodb://localhost:27017"
    
    mongodb_db_name = input("MongoDB Database Name [zendesk_analytics]: ") or "zendesk_analytics"
    
    # Generate a secure webhook key
    webhook_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # Update the env content
    env_content = re.sub(r'ZENDESK_EMAIL=.*', f'ZENDESK_EMAIL={zendesk_email}', env_content)
    env_content = re.sub(r'ZENDESK_API_TOKEN=.*', f'ZENDESK_API_TOKEN={zendesk_api_token}', env_content)
    env_content = re.sub(r'ZENDESK_SUBDOMAIN=.*', f'ZENDESK_SUBDOMAIN={zendesk_subdomain}', env_content)
    
    if openai_key:
        env_content = re.sub(r'OPENAI_API_KEY=.*', f'OPENAI_API_KEY={openai_key}', env_content)
    
    if anthropic_key:
        env_content = re.sub(r'ANTHROPIC_API_KEY=.*', f'ANTHROPIC_API_KEY={anthropic_key}', env_content)
    
    env_content = re.sub(r'MONGODB_URI=mongodb://localhost:27017', f'MONGODB_URI={mongodb_uri}', env_content)
    env_content = re.sub(r'MONGODB_DB_NAME=.*', f'MONGODB_DB_NAME={mongodb_db_name}', env_content)
    env_content = re.sub(r'WEBHOOK_SECRET_KEY=.*', f'WEBHOOK_SECRET_KEY={webhook_key}', env_content)
    
    # Write the updated env content
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print_status("Configuration file created successfully", "SUCCESS")
    return True

def create_run_scripts():
    """Create OS-specific run scripts for easy execution"""
    print_step(6, "Creating helper scripts")
    
    # Create Windows batch script
    if platform.system() == "Windows":
        with open("run_zendesk_ai.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Activating virtual environment...\n")
            f.write("call venv\\Scripts\\activate\n")
            f.write("echo Starting Zendesk AI Integration...\n")
            f.write("python src\\zendesk_ai_app.py %*\n")
            f.write("pause\n")
        print_status("Created run_zendesk_ai.bat", "SUCCESS")
    
    # Create Unix shell script
    else:
        with open("run_zendesk_ai.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo 'Activating virtual environment...'\n")
            f.write("source venv/bin/activate\n")
            f.write("echo 'Starting Zendesk AI Integration...'\n")
            f.write("python src/zendesk_ai_app.py \"$@\"\n")
        
        # Make the shell script executable
        os.chmod("run_zendesk_ai.sh", 0o755)
        print_status("Created run_zendesk_ai.sh", "SUCCESS")
    
    # Create a config script
    with open("configure_zendesk_ai.py", "w") as f:
        f.write("""#!/usr/bin/env python3
"""
Configuration Tool for Zendesk AI Integration

This script helps you update the configuration of the Zendesk AI Integration.
"""

import os
import sys
import getpass
import re
from pathlib import Path

def main():
    print("Zendesk AI Integration - Configuration Tool\\n")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("Error: .env file not found. Please run setup.py first.")
        return
    
    # Read the current configuration
    with open(env_file, "r") as f:
        env_content = f.read()
    
    # Get user input for configuration
    print("Please provide the following information (leave blank to keep current value):")
    
    # Zendesk credentials
    print("\\nZendesk API Credentials:")
    zendesk_email = input("Zendesk Email: ")
    zendesk_api_token = getpass.getpass("Zendesk API Token (leave blank to keep current): ")
    zendesk_subdomain = input("Zendesk Subdomain: ")
    
    # AI API keys
    print("\\nAI API Keys:")
    openai_key = getpass.getpass("OpenAI API Key (leave blank to keep current): ")
    anthropic_key = getpass.getpass("Anthropic API Key (leave blank to keep current): ")
    
    # MongoDB configuration
    print("\\nMongoDB Configuration:")
    mongodb_uri = input("MongoDB URI: ")
    mongodb_db_name = input("MongoDB Database Name: ")
    
    # Update the env content if values provided
    if zendesk_email:
        env_content = re.sub(r'ZENDESK_EMAIL=.*', f'ZENDESK_EMAIL={zendesk_email}', env_content)
    if zendesk_api_token:
        env_content = re.sub(r'ZENDESK_API_TOKEN=.*', f'ZENDESK_API_TOKEN={zendesk_api_token}', env_content)
    if zendesk_subdomain:
        env_content = re.sub(r'ZENDESK_SUBDOMAIN=.*', f'ZENDESK_SUBDOMAIN={zendesk_subdomain}', env_content)
    if openai_key:
        env_content = re.sub(r'OPENAI_API_KEY=.*', f'OPENAI_API_KEY={openai_key}', env_content)
    if anthropic_key:
        env_content = re.sub(r'ANTHROPIC_API_KEY=.*', f'ANTHROPIC_API_KEY={anthropic_key}', env_content)
    if mongodb_uri:
        env_content = re.sub(r'MONGODB_URI=.*', f'MONGODB_URI={mongodb_uri}', env_content)
    if mongodb_db_name:
        env_content = re.sub(r'MONGODB_DB_NAME=.*', f'MONGODB_DB_NAME={mongodb_db_name}', env_content)
    
    # Write the updated env content
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("\\nConfiguration updated successfully!")

if __name__ == "__main__":
    main()
""")
    
    # Make the config script executable
    if platform.system() != "Windows":
        os.chmod("configure_zendesk_ai.py", 0o755)
    
    print_status("Created configure_zendesk_ai.py", "SUCCESS")
    return True

def save_installation_info():
    """Save installation information for troubleshooting"""
    print_step(7, "Saving installation information")
    
    # Collect system information
    info = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": platform.system(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "installation_path": os.path.abspath(".")
    }
    
    # Save to file
    with open("installation_info.json", "w") as f:
        json.dump(info, f, indent=2)
    
    print_status("Installation information saved", "SUCCESS")
    return True

def main():
    """Main function for setting up the application"""
    print(f"\n{Colors.BOLD}Zendesk AI Integration - Setup{Colors.END}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Activate virtual environment
    python_path, pip_path = activate_virtual_environment()
    
    # Install dependencies
    if not install_dependencies(pip_path):
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        sys.exit(1)
    
    # Create helper scripts
    create_run_scripts()
    
    # Save installation information
    save_installation_info()
    
    # Verify installation
    verify_installation(python_path)
    
    # Final message
    print(f"\n{Colors.GREEN}{Colors.BOLD}Installation completed!{Colors.END}")
    print("\nTo run the application, use:")
    if platform.system() == "Windows":
        print("  run_zendesk_ai.bat --mode list-views")
    else:
        print("  ./run_zendesk_ai.sh --mode list-views")
    
    print("\nFor more options, refer to the README.md file.")

if __name__ == "__main__":
    main()