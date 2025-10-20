#!/usr/bin/env python3
"""
MongoDB Installation Module for Zendesk AI Integration

This module provides functions for installing and configuring MongoDB
through various methods:
1. Docker-based MongoDB
2. Native platform-specific installation
3. MongoDB Atlas configuration
4. Custom MongoDB connection
"""

import os
import sys
import platform
import subprocess
import shutil
import re
import getpass
import json
import time
import datetime
from pathlib import Path
import tempfile
import urllib.request

# Terminal colors for better readability
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status):
    """Print a status message with color coding"""
    status_color = {
        "SUCCESS": Colors.GREEN + "✓" + Colors.END,
        "WARNING": Colors.YELLOW + "⚠" + Colors.END,
        "ERROR": Colors.RED + "✗" + Colors.END,
        "INFO": Colors.BLUE + "ℹ" + Colors.END
    }
    
    print(f"{status_color[status]} {message}")

# Docker-based MongoDB functions
def check_docker_installation():
    """Check if Docker and Docker Compose are installed."""
    docker_installed = shutil.which("docker") is not None
    docker_compose_installed = (
        shutil.which("docker-compose") is not None or
        shutil.which("docker") is not None  # Docker CLI has compose subcommand in newer versions
    )
    
    if docker_installed and docker_compose_installed:
        # Verify Docker daemon is running
        try:
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode == 0:
                return True, "Docker is installed and running"
            else:
                return False, "Docker is installed but not running"
        except Exception:
            return False, "Error checking Docker status"
    else:
        message = "Docker " + ("not " if not docker_installed else "") + "installed, "
        message += "Docker Compose " + ("not " if not docker_compose_installed else "") + "installed"
        return False, message

def setup_mongodb_docker(username, password, database_name):
    """Setup MongoDB using Docker Compose."""
    # Create directory for MongoDB files
    mongo_dir = Path("mongodb")
    mongo_dir.mkdir(exist_ok=True)
    
    # Create .env file for Docker Compose
    env_content = f"""
MONGODB_USERNAME={username}
MONGODB_PASSWORD={password}
MONGODB_DATABASE={database_name}
"""
    with open(mongo_dir / ".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Create mongo-init.js
    init_js_content = f"""
db.createUser({{
  user: "{username}",
  pwd: "{password}",
  roles: [
    {{
      role: "readWrite",
      db: "{database_name}"
    }}
  ]
}});
"""
    with open(mongo_dir / "mongo-init.js", "w", encoding="utf-8") as f:
        f.write(init_js_content)
    
    # Create docker-compose.yml
    compose_content = """
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    container_name: zendesk_ai_mongodb
    restart: always
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGODB_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGODB_DATABASE}
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro

volumes:
  mongodb_data:
"""
    with open(mongo_dir / "docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(compose_content)
    
    # Create a helper script for starting/stopping MongoDB
    if platform.system() == "Windows":
        script_content = """@echo off
if "%1" == "start" (
    echo Starting MongoDB container...
    cd mongodb
    docker-compose up -d
    echo MongoDB container started successfully.
) else if "%1" == "stop" (
    echo Stopping MongoDB container...
    cd mongodb
    docker-compose down
    echo MongoDB container stopped successfully.
) else if "%1" == "restart" (
    echo Restarting MongoDB container...
    cd mongodb
    docker-compose restart
    echo MongoDB container restarted successfully.
) else if "%1" == "status" (
    echo MongoDB container status:
    cd mongodb
    docker-compose ps
) else (
    echo Usage: mongodb.bat [start^|stop^|restart^|status]
)
"""
        with open("mongodb.bat", "w", encoding="utf-8") as f:
            f.write(script_content)
    else:
        script_content = """#!/bin/bash
if [ "$1" == "start" ]; then
    echo "Starting MongoDB container..."
    cd mongodb
    docker-compose up -d
    echo "MongoDB container started successfully."
elif [ "$1" == "stop" ]; then
    echo "Stopping MongoDB container..."
    cd mongodb
    docker-compose down
    echo "MongoDB container stopped successfully."
elif [ "$1" == "restart" ]; then
    echo "Restarting MongoDB container..."
    cd mongodb
    docker-compose restart
    echo "MongoDB container restarted successfully."
elif [ "$1" == "status" ]; then
    echo "MongoDB container status:"
    cd mongodb
    docker-compose ps
else
    echo "Usage: ./mongodb.sh [start|stop|restart|status]"
fi
"""
        with open("mongodb.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod("mongodb.sh", 0o755)
    
    # Start MongoDB container
    try:
        # Handle both traditional docker-compose and new docker compose command
        docker_compose_cmd = []
        if shutil.which("docker-compose"):
            docker_compose_cmd = ["docker-compose"]
        else:
            docker_compose_cmd = ["docker", "compose"]
        
        subprocess.run(
            docker_compose_cmd + ["up", "-d"], 
            check=True, 
            cwd=mongo_dir
        )
        
        # Wait a bit for MongoDB to start
        print("Waiting for MongoDB container to initialize...")
        time.sleep(5)
        
        return True, "MongoDB container started successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to start MongoDB container: {str(e)}"

# Native MongoDB Installation Scripts
# These string constants hold the installation scripts for different platforms

WINDOWS_MONGODB_SCRIPT = """# MongoDB Windows Installation Script
$ErrorActionPreference = "Stop"

# Configuration
$mongoVersion = "6.0.11"
$downloadUrl = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-$mongoVersion-signed.msi"
$downloadPath = "$env:TEMP\\mongodb-$mongoVersion.msi"
$installDir = "C:\\Program Files\\MongoDB\\Server\\$mongoVersion"
$dataDir = "C:\\data\\db"
$logDir = "C:\\data\\log"

Write-Host "Installing MongoDB $mongoVersion on Windows..."

# Create data and log directories
try {
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
        Write-Host "Created data directory: $dataDir"
    }
    
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "Created log directory: $logDir"
    }
} catch {
    Write-Host "Error creating directories: $_"
    exit 1
}

# Download MongoDB installer
try {
    Write-Host "Downloading MongoDB installer..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath
    Write-Host "Downloaded MongoDB installer to $downloadPath"
} catch {
    Write-Host "Error downloading MongoDB installer: $_"
    exit 1
}

# Install MongoDB silently
try {
    Write-Host "Installing MongoDB..."
    Start-Process msiexec.exe -ArgumentList "/i \\"$downloadPath\\" /quiet" -Wait
    Write-Host "MongoDB installed successfully"
} catch {
    Write-Host "Error installing MongoDB: $_"
    exit 1
}

# Create MongoDB configuration file
$configContent = @"
storage:
  dbPath: $dataDir
  journal:
    enabled: true
systemLog:
  destination: file
  path: $logDir\\mongod.log
  logAppend: true
net:
  port: 27017
  bindIp: 127.0.0.1
"@

$configPath = "$env:ProgramData\\MongoDB\\mongod.cfg"
try {
    $configContent | Out-File -FilePath $configPath -Encoding utf8
    Write-Host "Created MongoDB configuration file: $configPath"
} catch {
    Write-Host "Error creating configuration file: $_"
    exit 1
}

# Install MongoDB as a Windows service
try {
    & "$installDir\\bin\\mongod.exe" --config "$configPath" --install
    Start-Service MongoDB
    Write-Host "MongoDB service installed and started"
} catch {
    Write-Host "Error setting up MongoDB service: $_"
    exit 1
}

Write-Host "MongoDB installation completed successfully"
"""

MACOS_MONGODB_SCRIPT = """#!/bin/bash
set -e

echo "Installing MongoDB on macOS using Homebrew..."

# Check if Homebrew is installed, install if not
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [[ $(uname -m) == "arm64" ]]; then
        # M1/M2 Mac
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else:
        # Intel Mac
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# Install MongoDB Community Edition
echo "Adding MongoDB tap..."
brew tap mongodb/brew

echo "Installing MongoDB Community Edition..."
brew install mongodb-community

# Create data directory if it doesn't exist
mkdir -p ~/data/db

# Start MongoDB service
echo "Starting MongoDB service..."
brew services start mongodb-community

echo "MongoDB installation completed successfully"
echo "MongoDB is running on localhost:27017"
"""

LINUX_MONGODB_SCRIPT = """#!/bin/bash
set -e

echo "Installing MongoDB on Linux..."

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
    PACKAGE_MANAGER=""
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        PACKAGE_MANAGER="apt"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
        PACKAGE_MANAGER="yum"
    else
        echo "Unsupported Linux distribution: $OS"
        exit 1
    fi
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo "Detected $OS $VERSION using $PACKAGE_MANAGER"

# Install MongoDB based on distribution
if [ "$PACKAGE_MANAGER" == "apt" ]; then
    # For Ubuntu/Debian
    echo "Installing MongoDB on Ubuntu/Debian..."
    
    # Import MongoDB public GPG key
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
    
    # Create list file for MongoDB
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    
    # Update package database
    sudo apt update
    
    # Install MongoDB
    sudo apt install -y mongodb-org
    
    # Start MongoDB service
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
elif [ "$PACKAGE_MANAGER" == "yum" ]; then
    # For CentOS/RHEL/Fedora
    echo "Installing MongoDB on CentOS/RHEL/Fedora..."
    
    # Create a repo file
    cat <<EOF | sudo tee /etc/yum.repos.d/mongodb-org-6.0.repo
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF
    
    # Install MongoDB
    sudo yum install -y mongodb-org
    
    # Start MongoDB service
    sudo systemctl start mongod
    sudo systemctl enable mongod
fi

echo "MongoDB installation completed successfully"
echo "MongoDB is running on localhost:27017"
"""

def install_mongodb_native():
    """Install MongoDB natively based on the detected operating system."""
    system = platform.system()
    
    # Create scripts directory
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    if system == "Windows":
        # Windows installation
        script_path = scripts_dir / "install_mongodb_windows.ps1"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(WINDOWS_MONGODB_SCRIPT)
        
        try:
            print("Installing MongoDB on Windows (this may take a few minutes)...")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)], check=True)
            return True, "MongoDB installed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to install MongoDB: {str(e)}"
    
    elif system == "Darwin":  # macOS
        script_path = scripts_dir / "install_mongodb_macos.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(MACOS_MONGODB_SCRIPT)
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        try:
            print("Installing MongoDB on macOS (this may take a few minutes)...")
            subprocess.run([str(script_path)], check=True)
            return True, "MongoDB installed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to install MongoDB: {str(e)}"
    
    elif system == "Linux":
        script_path = scripts_dir / "install_mongodb_linux.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(LINUX_MONGODB_SCRIPT)
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        try:
            print("Installing MongoDB on Linux (this may take a few minutes)...")
            subprocess.run(["sudo", str(script_path)], check=True)
            return True, "MongoDB installed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to install MongoDB: {str(e)}"
    
    else:
        return False, f"Unsupported operating system: {system}"

# MongoDB Atlas Guide
MONGODB_ATLAS_GUIDE = """
==== MongoDB Atlas Setup Guide ====

MongoDB Atlas is a fully-managed cloud database service that requires no installation.
Follow these steps to set up a free MongoDB Atlas cluster:

1. Create a MongoDB Atlas account:
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up with your email or use Google/GitHub sign-in

2. Create a free cluster:
   - Select "Shared" (free) option
   - Choose a cloud provider (AWS, Azure, or GCP)
   - Select a region closest to you
   - Click "Create Cluster" (takes 1-3 minutes to provision)

3. Set up database access:
   - In the left sidebar, click "Database Access"
   - Click "Add New Database User"
   - Create a username and password (save these credentials!)
   - Set privileges to "Read and Write to Any Database"
   - Click "Add User"

4. Set up network access:
   - In the left sidebar, click "Network Access"
   - Click "Add IP Address"
   - For development, you can select "Allow Access From Anywhere" (0.0.0.0/0)
   - For production, use specific IP addresses
   - Click "Confirm"

5. Get your connection string:
   - In the Clusters view, click "Connect"
   - Select "Connect your application"
   - Choose "Python" as the driver and appropriate version
   - Copy the connection string (it looks like: mongodb+srv://username:<password>@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority)
   - Replace <password> with your database user password

Use this connection string when prompted during the Zendesk AI Integration setup.
"""

def verify_mongodb_atlas_connection(connection_string, database_name):
    """Verify connection to MongoDB Atlas."""
    try:
        print("Verifying MongoDB Atlas connection...")
        
        # Try to import pymongo
        try:
            import pymongo
        except ImportError:
            # Install pymongo if not available
            print("pymongo module not installed. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pymongo[srv]"], check=True)
            import pymongo
        
        # Try to connect to MongoDB Atlas
        try:
            # Set a short timeout for connection testing
            client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Force a connection to verify
            client.server_info()
            
            # Try to access the specified database
            db = client[database_name]
            # Try a simple operation
            db.command("ping")
            
            return True, "Successfully connected to MongoDB Atlas"
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return False, f"Failed to connect to MongoDB Atlas: Timeout. Check your connection string and network access settings. Error: {str(e)}"
        except pymongo.errors.OperationFailure as e:
            return False, f"Authentication failed for MongoDB Atlas: {str(e)}"
        except Exception as e:
            return False, f"Error connecting to MongoDB Atlas: {str(e)}"
            
    except Exception as e:
        return False, f"Unexpected error verifying MongoDB Atlas connection: {str(e)}"

# General MongoDB connection testing
def test_mongodb_connection(uri, database_name):
    """Test MongoDB connection for any connection type."""
    try:
        print(f"Testing connection to MongoDB at {uri.split('@')[-1] if '@' in uri else uri}...")
        
        # Try to import pymongo
        try:
            import pymongo
        except ImportError:
            # Install pymongo if not available
            print("pymongo module not installed. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pymongo"], check=True)
            import pymongo
        
        # Try to connect to MongoDB
        try:
            # Set a short timeout for connection testing
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            
            # Force a connection to verify
            client.server_info()
            
            # Try to access the specified database
            db = client[database_name]
            
            # Try a simple operation
            db.command("ping")
            
            # Check if we can write to the database
            test_collection = db["connection_test"]
            test_id = test_collection.insert_one({"test": "connection", "timestamp": datetime.datetime.now()}).inserted_id
            test_collection.delete_one({"_id": test_id})
            
            return True, "Successfully connected to MongoDB and verified read/write operations"
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return False, f"Failed to connect to MongoDB: Timeout. Error: {str(e)}"
        except pymongo.errors.OperationFailure as e:
            if "auth failed" in str(e).lower():
                return False, "Authentication failed. Check your username and password."
            else:
                return False, f"Operation failed: {str(e)}"
        except Exception as e:
            return False, f"Error connecting to MongoDB: {str(e)}"
            
    except Exception as e:
        return False, f"Unexpected error testing MongoDB connection: {str(e)}"

# Main MongoDB setup function
def setup_mongodb_configuration():
    """Set up MongoDB configuration with multiple installation options."""
    print(f"\n{Colors.BOLD}MongoDB Setup{Colors.END}")
    
    print(f"\n{Colors.BOLD}MongoDB Setup Options:{Colors.END}")
    print("1. Use Docker (recommended if Docker is installed)")
    print("2. Install MongoDB locally (requires admin privileges)")
    print("3. Use MongoDB Atlas (cloud-hosted, no installation required)")
    print("4. Use existing MongoDB installation or custom connection")
    
    # Check for Docker installation first
    docker_available, docker_message = check_docker_installation()
    if docker_available:
        print_status("Docker detected and running", "SUCCESS")
        recommended_option = "1"
    else:
        print_status(docker_message, "INFO")
        recommended_option = "3"  # Default to Atlas if Docker is not available
    
    # Check for existing MongoDB installation
    mongodb_installed = False
    if platform.system() == "Windows":
        mongodb_installed = Path("C:/Program Files/MongoDB").exists()
    elif platform.system() == "Darwin":  # macOS
        mongodb_installed = Path("/usr/local/bin/mongod").exists() or Path("/opt/homebrew/bin/mongod").exists()
    else:  # Linux
        mongodb_installed = shutil.which("mongod") is not None
    
    if mongodb_installed:
        print_status("Existing MongoDB installation detected", "SUCCESS")
        recommended_option = "4"
    
    choice = input(f"Choose MongoDB setup option (1-4) [{recommended_option}]: ") or recommended_option
    
    # MongoDB credentials
    username = ""
    password = ""
    database_name = ""
    uri = ""
    
    if choice == "1":
        # Docker setup
        print(f"\n{Colors.BOLD}Setting up MongoDB using Docker{Colors.END}")
        
        if not docker_available:
            print_status("Docker is not available. Please install Docker first.", "ERROR")
            print("Visit https://docs.docker.com/get-docker/ for installation instructions.")
            print("After installing Docker, run this setup script again.")
            return False
        
        # Get MongoDB credentials
        username = input("MongoDB Username [admin]: ") or "admin"
        password = getpass.getpass("MongoDB Password [admin]: ") or "admin"
        database_name = input("MongoDB Database Name [zendesk_analytics]: ") or "zendesk_analytics"
        
        # Setup Docker MongoDB
        success, message = setup_mongodb_docker(username, password, database_name)
        
        if success:
            print_status(message, "SUCCESS")
            # Set MongoDB URI
            uri = f"mongodb://{username}:{password}@localhost:27017/{database_name}?authSource=admin"
        else:
            print_status(message, "ERROR")
            print("Please check Docker installation and try again.")
            return False
    
    elif choice == "2":
        # Local installation
        print(f"\n{Colors.BOLD}Installing MongoDB locally{Colors.END}")
        print("This will install MongoDB on your local machine.")
        print("The installation may take several minutes.")
        
        if input("Continue with MongoDB installation? (y/n): ").lower() != 'y':
            print("MongoDB installation aborted by user.")
            return False
        
        # Install MongoDB based on platform
        success, message = install_mongodb_native()
        
        if success:
            print_status(message, "SUCCESS")
            
            # Set MongoDB credentials after installation
            username = input("MongoDB Username [admin]: ") or "admin"
            password = getpass.getpass("MongoDB Password [admin]: ") or "admin"
            database_name = input("MongoDB Database Name [zendesk_analytics]: ") or "zendesk_analytics"
            
            # TODO: Set up authentication on the new MongoDB installation
            # This would involve creating a user with the specified credentials
            # For simplicity, for now we'll use the connection without auth
            uri = f"mongodb://localhost:27017/{database_name}"
            
            print_status(f"Using MongoDB connection URI: {uri}", "INFO")
            print("Note: Authentication is not set up. For production use, please enable authentication.")
        else:
            print_status(message, "ERROR")
            print("Please check the installation logs for details and try again.")
            return False
    
    elif choice == "3":
        # MongoDB Atlas
        print(f"\n{Colors.BOLD}Using MongoDB Atlas (Cloud){Colors.END}")
        print("MongoDB Atlas is a fully-managed cloud database service.")
        
        # Show Atlas setup guide
        print(MONGODB_ATLAS_GUIDE)
        
        print("After setting up your MongoDB Atlas cluster, enter your connection details:")
        uri = getpass.getpass("MongoDB Atlas URI (mongodb+srv://...): ")
        
        if not uri:
            print_status("MongoDB Atlas URI is required", "ERROR")
            return False
        
        # Extract database name from URI or ask for it
        database_name = input("MongoDB Database Name [zendesk_analytics]: ") or "zendesk_analytics"
        
        # Verify the Atlas connection
        success, message = verify_mongodb_atlas_connection(uri, database_name)
        
        if success:
            print_status(message, "SUCCESS")
        else:
            print_status(message, "ERROR")
            print("Please check your MongoDB Atlas configuration and try again.")
            return False
    
    else:  # Option 4: Custom connection
        print(f"\n{Colors.BOLD}Using existing MongoDB installation or custom connection{Colors.END}")
        
        # Ask for MongoDB connection details
        uri = input("MongoDB URI [mongodb://localhost:27017]: ") or "mongodb://localhost:27017"
        database_name = input("MongoDB Database Name [zendesk_analytics]: ") or "zendesk_analytics"
        
        # Check if the URI includes credentials
        if "@" in uri and "://" in uri:
            # Extract username/password if they exist in the URI
            credentials = uri.split("://")[1].split("@")[0]
            if ":" in credentials:
                username, password = credentials.split(":", 1)
                print_status(f"Using credentials from URI: {username}", "INFO")
        else:
            # Ask for credentials if not in URI
            use_auth = input("Does your MongoDB require authentication? (y/n): ").lower() == 'y'
            if use_auth:
                username = input("MongoDB Username: ")
                password = getpass.getpass("MongoDB Password: ")
                
                # Update URI with authentication
                if "://" in uri:
                    prefix, suffix = uri.split("://", 1)
                    uri = f"{prefix}://{username}:{password}@{suffix}"
                else:
                    uri = f"mongodb://{username}:{password}@{uri.replace('mongodb://', '')}"
        
        # Test the connection
        success, message = test_mongodb_connection(uri, database_name)
        
        if success:
            print_status(message, "SUCCESS")
        else:
            print_status(message, "ERROR")
            retry = input("Do you want to continue anyway? (y/n): ").lower() == 'y'
            if not retry:
                print("Please check your MongoDB configuration and try again.")
                return False
    
    # Return the MongoDB connection information
    return {
        "uri": uri,
        "database_name": database_name,
        "username": username,
        "password": password
    }

# Entry point for direct execution
if __name__ == "__main__":
    print(f"{Colors.BOLD}MongoDB Setup Utility{Colors.END}")
    print("This script helps you set up MongoDB for the Zendesk AI Integration.")
    
    # Run the MongoDB setup
    result = setup_mongodb_configuration()
    
    if result:
        print(f"\n{Colors.GREEN}{Colors.BOLD}MongoDB setup completed successfully!{Colors.END}")
        print(f"URI: {result['uri'].split('@')[-1] if '@' in result['uri'] else result['uri']}")
        print(f"Database: {result['database_name']}")
    else:
        print(f"\n{Colors.RED}MongoDB setup failed.{Colors.END}")
        print("Please check the error messages and try again.")
