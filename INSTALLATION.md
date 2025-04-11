# Zendesk AI Integration - Installation Guide

**Last Updated: March 31, 2025**

This guide provides step-by-step instructions for installing and running the Zendesk AI Integration application on Windows, macOS, and Linux systems.

## Prerequisites

Before installing the application, ensure you have the following prerequisites:

- Python 3.9 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

For MongoDB, you have multiple options:

1. **Docker** (recommended): The easiest way to set up MongoDB
2. **Local MongoDB installation**: A native installation on your machine
3. **MongoDB Atlas**: A cloud-hosted MongoDB service (no local installation needed)
4. **Existing MongoDB installation**: Use your existing MongoDB instance

The installation process will guide you through the MongoDB setup options.

## Quick Installation (Automated Setup)

For an automated installation experience, use the universal installer script which features integrity verification, automatic retries, and progress visualization.

### Automated Setup

1. Download the installer script:
   ```bash
   curl -o install.py https://raw.githubusercontent.com/exxactcorp/zendesk-ai-integration/main/install.py
   ```

2. Run the installer which will download and verify all necessary files:
   ```bash
   python install.py
   ```

3. Or for more advanced usage, you can download and run the setup components directly:

```bash
python check_prerequisites.py  # Check if your system meets requirements
python setup.py                # Run the automated installation
```

The setup script will:
- Check if your system meets requirements
- Create a Python virtual environment
- Install all required dependencies
- Guide you through the configuration process
- Create convenient run scripts for your operating system

### Next Steps After Automated Setup

After the setup completes, you can run the application using:

**Windows**:
```
run_zendesk_ai.bat --mode list-views
```

**macOS/Linux**:
```
./run_zendesk_ai.sh --mode list-views
```

## Manual Installation Instructions

If you prefer to install the application manually, follow these steps:

### Step 1: Get the Code

**Option A: Clone the Repository (if you have Git installed)**

```bash
git clone https://github.com/exxactcorp/zendesk-ai-integration.git
cd zendesk-ai-integration
```

**Option B: Download ZIP Archive**

1. Download the ZIP file from GitHub
2. Extract the contents to a folder of your choice
3. Open a terminal/command prompt and navigate to the extracted folder

### Step 2: Create a Virtual Environment

#### Windows

```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your specific configuration:
   - Add your Zendesk API credentials
   - Add your OpenAI or Anthropic API keys
   - Configure MongoDB connection
   - Set other optional parameters

## Running the Application

### Basic Usage

```bash
# Analyze tickets with default settings (Claude AI)
python src/zendesk_ai_app.py --mode run --status open

# Generate sentiment analysis report
python src/zendesk_ai_app.py --mode sentiment --days 7

# Start webhook server
python src/zendesk_ai_app.py --mode webhook
```

See the README.md file for more detailed usage instructions and available commands.

## Updating Configuration

To update your configuration after installation:

### Automated Configuration Update

Run the configuration script:

```bash
python configure_zendesk_ai.py
```

This script will prompt you for updated values and modify your `.env` file accordingly.

### Manual Configuration Update

1. Open the `.env` file with a text editor
2. Edit the values you wish to change
3. Save the file

## OS-Specific Instructions

### Windows

#### Installing Python on Windows

1. Download the latest Python installer from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer and check "Add Python to PATH"
3. Complete the installation

#### Installing MongoDB on Windows

**Option 1: Using Docker (Recommended)**

1. Install Docker Desktop for Windows from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop
3. The installation script will handle the rest

**Option 2: Native Installation**

1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer with default settings
3. MongoDB will be installed as a Windows service

**Option 3: MongoDB Atlas (Cloud)**

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Follow the steps to create a free tier cluster
3. Set up network access and database user
4. Get your connection string for the installation process

#### Setting Environment Variables on Windows

1. Open the `.env` file with Notepad or another text editor
2. Set your API keys and other configuration variables

### macOS

#### Installing Python on macOS

1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python:
   ```bash
   brew install python
   ```

#### Installing MongoDB on macOS

**Option 1: Using Docker (Recommended)**

1. Install Docker Desktop for Mac from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop
3. The installation script will handle the rest

**Option 2: Native Installation with Homebrew**

1. Install MongoDB with Homebrew:
   ```bash
   brew tap mongodb/brew
   brew install mongodb-community
   ```

2. Start MongoDB service:
   ```bash
   brew services start mongodb-community
   ```

**Option 3: MongoDB Atlas (Cloud)**

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Follow the steps to create a free tier cluster
3. Set up network access and database user
4. Get your connection string for the installation process

#### Setting Environment Variables on macOS

1. Open the `.env` file with a text editor:
   ```bash
   nano .env
   ```
2. Set your API keys and other configuration variables

### Linux (Ubuntu/Debian)

#### Installing Python on Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Installing MongoDB on Ubuntu/Debian

**Option 1: Using Docker (Recommended)**

1. Install Docker using the official instructions:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. Install Docker Compose:
   ```bash
   sudo apt-get install docker-compose-plugin
   ```

3. The installation script will handle the rest

**Option 2: Native Installation**

```bash
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
```

**Option 3: MongoDB Atlas (Cloud)**

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Follow the steps to create a free tier cluster
3. Set up network access and database user
4. Get your connection string for the installation process

#### Setting Environment Variables on Linux

1. Open the `.env` file with a text editor:
   ```bash
   nano .env
   ```
2. Set your API keys and other configuration variables

## Verification

To verify the installation was successful:

```bash
# List available Zendesk views
python src/zendesk_ai_app.py --mode list-views
```

If this command returns a list of views from your Zendesk account, the installation is working correctly.

## Upgrading

To upgrade to a newer version of the application:

1. Back up your `.env` file
2. Pull the latest code from the repository or download the updated ZIP
3. Run the setup script again:
   ```bash
   python setup.py
   ```
4. Restore your custom settings from the backup `.env` if needed

## Customizing Installation

The installer supports several environment variables to customize the installation process:

| Variable | Description | Default |
|----------|-------------|--------|
| `ZENDESK_AI_ORG` | GitHub organization name | `exxactcorp` |
| `ZENDESK_AI_REPO` | GitHub repository name | `zendesk-ai-integration` |
| `ZENDESK_AI_BRANCH` | GitHub branch name | `main` |
| `SKIP_CHECKSUM_VERIFY` | Skip checksum verification | `false` |

### Using Environment Variables

#### On Windows:

```cmd
set ZENDESK_AI_ORG=your-org-name
set ZENDESK_AI_BRANCH=dev
python install.py
```

#### On macOS/Linux:

```bash
ZENDESK_AI_ORG=your-org-name ZENDESK_AI_BRANCH=dev python install.py
```

## Common Issues and Solutions

### MongoDB Setup and Connection Issues

**MongoDB Docker Setup**

If you chose the Docker option for MongoDB:
- Make sure Docker is installed and running on your machine
- You can manage your MongoDB container with the provided scripts:
  - On Windows: `mongodb.bat [start|stop|restart|status]`
  - On macOS/Linux: `./mongodb.sh [start|stop|restart|status]`
- The container is configured to persist data even after restarts

**Native MongoDB Installation**

If you chose the native MongoDB installation:
- Verify that MongoDB service is running
  - Windows: Check Services application for MongoDB service
  - macOS: Run `brew services list` to check status
  - Linux: Run `sudo systemctl status mongod`

**MongoDB Atlas Setup**

If you chose MongoDB Atlas:
- Ensure your IP is allowed in the Network Access settings
- Verify your database user credentials
- Test the connection string directly

**General MongoDB Connection Issues**

**Symptoms**: Error messages about failing to connect to MongoDB

**Solutions**:
- Ensure MongoDB is running on your machine
- Check your connection string in the `.env` file
- For MongoDB Atlas, ensure your IP is allowed in the network access settings
- Check that your username and password are correct
- Run `python install_mongodb.py` to reconfigure MongoDB

### Download and Checksum Issues

**Symptoms**: Errors during download or checksum verification failures

**Solutions**:
- Check your internet connection and try again
- For checksum failures, try skipping verification: `SKIP_CHECKSUM_VERIFY=true python install.py`
- Download files manually from the GitHub repository if automated downloads fail
- If using a custom branch or fork, ensure the checksums in `install.py` match the actual files

### API Key Issues

**Symptoms**: Error messages about invalid API keys or authentication failures

**Solutions**:
- Double-check your API keys in the `.env` file
- Ensure your Zendesk API token has the necessary permissions
- For OpenAI or Anthropic, make sure your API key is active and has credits

### Missing or Outdated Dependencies

**Symptoms**: Import errors or unexpected behavior

**Solutions**:
- Run `pip install -r requirements.txt` to update all dependencies
- Create a new virtual environment if issues persist

## Getting Help

If you encounter issues not covered in this guide:

- Check the error logs (usually in the console output)
- Review the documentation files in the project directory
- Run `python check_prerequisites.py` to verify system requirements
- Open an issue on the GitHub repository with detailed information about your problem
