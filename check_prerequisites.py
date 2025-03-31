#!/usr/bin/env python3
"""
Prerequisites Checker for Zendesk AI Integration

This script checks if all required prerequisites are installed and properly configured.
Run this script before attempting to install or run the Zendesk AI Integration.

Usage:
  python check_prerequisites.py
"""

import os
import sys
import importlib.util
import platform
import subprocess
import shutil
from pathlib import Path
import urllib.request

# Terminal colors for better readability
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status, details=None):
    """Print a status message with color coding"""
    status_color = {
        "PASS": Colors.GREEN + "✓" + Colors.END,
        "WARN": Colors.YELLOW + "⚠" + Colors.END,
        "FAIL": Colors.RED + "✗" + Colors.END,
        "INFO": Colors.BLUE + "ℹ" + Colors.END
    }
    
    print(f"{status_color[status]} {message}")
    if details:
        print(f"  {details}")

def check_python_version():
    """Check if Python version is 3.9 or higher"""
    current_version = sys.version_info
    required_version = (3, 9)
    
    if current_version.major > required_version[0] or (current_version.major == required_version[0] and current_version.minor >= required_version[1]):
        print_status(
            f"Python version {current_version.major}.{current_version.minor}.{current_version.micro}",
            "PASS"
        )
        return True
    else:
        print_status(
            f"Python version {current_version.major}.{current_version.minor}.{current_version.micro} (version 3.9+ required)",
            "FAIL",
            "Please install Python 3.9 or higher from https://www.python.org/downloads/"
        )
        return False

def check_pip():
    """Check if pip is installed and accessible"""
    if shutil.which("pip") or shutil.which("pip3"):
        pip_cmd = "pip" if shutil.which("pip") else "pip3"
        try:
            result = subprocess.run([pip_cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print_status(f"Pip is installed: {result.stdout.strip()}", "PASS")
                return True
        except Exception as e:
            pass
    
    print_status("Pip is not installed or not in PATH", "FAIL",
                "Please install pip: https://pip.pypa.io/en/stable/installation/")
    return False

def check_venv():
    """Check if venv module is available"""
    if importlib.util.find_spec("venv"):
        print_status("Python venv module is available", "PASS")
        return True
    else:
        print_status("Python venv module is not available", "FAIL",
                   "This is usually included with Python, but on some systems may need separate installation.")
        if platform.system() == "Linux":
            print("  On Ubuntu/Debian: sudo apt install python3-venv")
            print("  On CentOS/RHEL: sudo yum install python3-venv")
        return False

def check_git():
    """Check if Git is installed (optional)"""
    if shutil.which("git"):
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print_status(f"Git is installed: {result.stdout.strip()}", "PASS")
                return True
        except Exception:
            pass
    
    print_status("Git is not installed or not in PATH", "WARN",
               "Git is optional, but recommended for version control and updates.")
    if platform.system() == "Windows":
        print("  Download from: https://git-scm.com/download/win")
    elif platform.system() == "Darwin":  # macOS
        print("  Install with: brew install git")
    elif platform.system() == "Linux":
        print("  On Ubuntu/Debian: sudo apt install git")
        print("  On CentOS/RHEL: sudo yum install git")
    return False

def check_mongodb():
    """Check if MongoDB is available"""
    # First check if MongoDB is installed locally
    mongodb_installed = False
    
    if platform.system() == "Windows":
        mongo_paths = [
            r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
            r"C:\Program Files\MongoDB\*\bin\mongod.exe"
        ]
        for path_pattern in mongo_paths:
            import glob
            if glob.glob(path_pattern):
                mongodb_installed = True
                break
    else:  # macOS and Linux
        if shutil.which("mongod"):
            mongodb_installed = True
    
    if mongodb_installed:
        print_status("MongoDB appears to be installed locally", "PASS")
        return True
    
    # If not installed, check if MongoDB Atlas or other remote instance might be used
    env_file = Path(".env")
    example_env = Path(".env.example")
    
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()
            if "MONGODB_URI=" in env_content and "mongodb+srv://" in env_content:
                print_status("MongoDB does not appear to be installed locally, but remote MongoDB URI found in .env", "PASS",
                           "Using a remote MongoDB instance like MongoDB Atlas is fine.")
                return True
    
    print_status("MongoDB is not installed or not detected", "WARN",
               "MongoDB is required for storing analysis results.")
    if platform.system() == "Windows":
        print("  Download from: https://www.mongodb.com/try/download/community")
    elif platform.system() == "Darwin":  # macOS
        print("  Install with: brew tap mongodb/brew && brew install mongodb-community")
    elif platform.system() == "Linux":
        print("  On Ubuntu/Debian: Follow https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/")
    print("  Alternatively, use MongoDB Atlas: https://www.mongodb.com/cloud/atlas/register")
    return False

def check_zendesk_api_credentials():
    """Check if Zendesk API credentials are configured"""
    env_file = Path(".env")
    example_env = Path(".env.example")
    
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()
            
            # Basic check for Zendesk credentials
            has_email = "ZENDESK_EMAIL=" in env_content and "your_email@" not in env_content
            has_token = "ZENDESK_API_TOKEN=" in env_content and "your_zendesk_api_token" not in env_content
            has_subdomain = "ZENDESK_SUBDOMAIN=" in env_content and "your_zendesk_subdomain" not in env_content
            
            if has_email and has_token and has_subdomain:
                print_status("Zendesk API credentials found in .env", "PASS")
                return True
            else:
                print_status("Zendesk API credentials incomplete or contain placeholder values", "WARN",
                           "Please update .env with your actual Zendesk credentials.")
                return False
    elif example_env.exists():
        print_status(".env file not found, but .env.example exists", "WARN",
                   "Please copy .env.example to .env and update with your Zendesk credentials.")
    else:
        print_status(".env file not found", "FAIL",
                   "Please create a .env file with your Zendesk API credentials.")
    return False

def check_ai_api_keys():
    """Check if AI API keys are configured"""
    env_file = Path(".env")
    
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()
            
            has_openai = "OPENAI_API_KEY=" in env_content and "your_openai_api_key" not in env_content
            has_anthropic = "ANTHROPIC_API_KEY=" in env_content and "your_anthropic_api_key" not in env_content
            
            if has_openai or has_anthropic:
                if has_openai and has_anthropic:
                    print_status("Both OpenAI and Anthropic API keys found in .env", "PASS")
                elif has_openai:
                    print_status("OpenAI API key found in .env", "PASS", 
                               "Anthropic API key not found, but one AI service is sufficient.")
                else:
                    print_status("Anthropic API key found in .env", "PASS",
                               "OpenAI API key not found, but one AI service is sufficient.")
                return True
            else:
                print_status("No AI API keys found or they contain placeholder values", "WARN",
                           "At least one AI API key (OpenAI or Anthropic) is required.")
                return False
    return False

def check_network_connectivity():
    """Check network connectivity to required services"""
    services = [
        ("api.openai.com", "OpenAI API"),
        ("api.anthropic.com", "Anthropic API"),
        ("github.com", "GitHub (for updates)")
    ]
    
    all_ok = True
    for host, service_name in services:
        try:
            urllib.request.urlopen(f"https://{host}", timeout=5)
            print_status(f"Connection to {service_name} ({host})", "PASS")
        except Exception as e:
            print_status(f"Connection to {service_name} ({host})", "WARN", 
                       f"Could not connect: {str(e)}")
            all_ok = False
    
    return all_ok

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        "flask",
        "pymongo",
        "requests",
        "cachetools",
        "python-dotenv"
    ]
    
    all_ok = True
    for package in required_packages:
        if importlib.util.find_spec(package):
            print_status(f"Package '{package}' is installed", "PASS")
        else:
            print_status(f"Package '{package}' is not installed", "WARN",
                       f"Will be installed with 'pip install -r requirements.txt'")
            all_ok = False
    
    # Check for Zenpy specifically
    if importlib.util.find_spec("zenpy"):
        print_status("Zenpy (Zendesk Python client) is installed", "PASS")
    else:
        print_status("Zenpy (Zendesk Python client) is not installed", "WARN",
                   "Will be installed with 'pip install -r requirements.txt'")
        all_ok = False
    
    # Check for either OpenAI or Anthropic
    has_openai = importlib.util.find_spec("openai") is not None
    has_anthropic = importlib.util.find_spec("anthropic") is not None
    
    if has_openai or has_anthropic:
        if has_openai:
            print_status("OpenAI Python client is installed", "PASS")
        if has_anthropic:
            print_status("Anthropic Python client is installed", "PASS")
    else:
        print_status("Neither OpenAI nor Anthropic Python clients are installed", "WARN",
                   "Will be installed with 'pip install -r requirements.txt'")
        all_ok = False
    
    return all_ok

def main():
    """Main function to run all checks"""
    print(f"\n{Colors.BOLD}Zendesk AI Integration - Prerequisites Check{Colors.END}\n")
    
    results = {}
    
    print(f"{Colors.BOLD}System Requirements:{Colors.END}")
    results["python"] = check_python_version()
    results["pip"] = check_pip()
    results["venv"] = check_venv()
    results["git"] = check_git()  # Optional
    print()
    
    print(f"{Colors.BOLD}Database:{Colors.END}")
    results["mongodb"] = check_mongodb()
    print()
    
    print(f"{Colors.BOLD}API Credentials:{Colors.END}")
    results["zendesk"] = check_zendesk_api_credentials()
    results["ai_apis"] = check_ai_api_keys()
    print()
    
    print(f"{Colors.BOLD}Network Connectivity:{Colors.END}")
    results["network"] = check_network_connectivity()
    print()
    
    print(f"{Colors.BOLD}Python Dependencies:{Colors.END}")
    results["dependencies"] = check_dependencies()
    print()
    
    # Summary and recommendations
    critical_requirements = ["python", "pip", "venv"]
    important_requirements = ["mongodb", "zendesk", "ai_apis"]
    
    critical_failed = any(not results[req] for req in critical_requirements)
    important_failed = any(not results[req] for req in important_requirements)
    
    if critical_failed:
        print(f"{Colors.RED}{Colors.BOLD}Critical requirements missing!{Colors.END}")
        print("Please address the issues marked with ✗ before proceeding with installation.")
        print("The application cannot be installed until these requirements are met.")
    elif important_failed:
        print(f"{Colors.YELLOW}{Colors.BOLD}Some important requirements are missing or incomplete.{Colors.END}")
        print("You can proceed with installation, but the application may not function correctly")
        print("until the issues marked with ⚠ are addressed.")
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}All requirements satisfied!{Colors.END}")
        print("You're ready to install and run the Zendesk AI Integration.")

    # Next steps
    print("\nNext steps:")
    if critical_failed:
        print("1. Address the critical requirements mentioned above")
        print("2. Run this prerequisites check again")
    else:
        print("1. Run: python -m venv venv")
        if platform.system() == "Windows":
            print("2. Run: venv\\Scripts\\activate")
        else:
            print("2. Run: source venv/bin/activate")
        print("3. Run: pip install -r requirements.txt")
        print("4. Make sure your .env file is properly configured")
        print("5. Run: python src/zendesk_ai_app.py --mode list-views")

if __name__ == "__main__":
    main()
