# Zendesk AI Integration - Copy-Paste Command Sheet

This document provides ready-to-use commands for installing and using the Zendesk AI Integration. Simply copy and paste these commands into your terminal/command prompt.

## Windows Commands

### Installation

```batch
:: Clone the repository
git clone https://github.com/quanticsoul4772/zendesk-ai-integration.git
cd zendesk-ai-integration

:: Option 1: Run the easy installer (recommended)
easy_install.bat

:: Option 2: Run the Python installer directly with correct environment variables
set ZENDESK_AI_ORG=quanticsoul4772
set ZENDESK_AI_REPO=zendesk-ai-integration
set SKIP_CHECKSUM_VERIFY=true
python install.py
```

### Running the Application

```batch
:: List Zendesk views
run_zendesk_ai.bat --mode listviews

:: Analyze a specific ticket
run_zendesk_ai.bat --mode analyzeticket --ticket-id 12345

:: Generate a sentiment report
run_zendesk_ai.bat --mode generatereport --type sentiment --days 7

:: Start the webhook server
run_zendesk_ai.bat --mode webhook --start --host 0.0.0.0 --port 8000
```

### MongoDB Management (if using Docker)

```batch
:: Start MongoDB container
mongodb.bat start

:: Check MongoDB status
mongodb.bat status

:: Stop MongoDB container
mongodb.bat stop

:: Restart MongoDB container
mongodb.bat restart
```

## macOS/Linux Commands

### Installation

```bash
# Clone the repository
git clone https://github.com/quanticsoul4772/zendesk-ai-integration.git
cd zendesk-ai-integration

# Option 1: Run the easy installer (recommended)
chmod +x easy_install.sh
./easy_install.sh

# Option 2: Run the Python installer directly with correct environment variables
export ZENDESK_AI_ORG=quanticsoul4772
export ZENDESK_AI_REPO=zendesk-ai-integration
export SKIP_CHECKSUM_VERIFY=true
python3 install.py
```

### Running the Application

```bash
# List Zendesk views
./run_zendesk_ai.sh --mode listviews

# Analyze a specific ticket
./run_zendesk_ai.sh --mode analyzeticket --ticket-id 12345

# Generate a sentiment report
./run_zendesk_ai.sh --mode generatereport --type sentiment --days 7

# Start the webhook server
./run_zendesk_ai.sh --mode webhook --start --host 0.0.0.0 --port 8000
```

### MongoDB Management (if using Docker)

```bash
# Start MongoDB container
./mongodb.sh start

# Check MongoDB status
./mongodb.sh status

# Stop MongoDB container
./mongodb.sh stop

# Restart MongoDB container
./mongodb.sh restart
```

## Configuration Commands

### Update Configuration

```bash
# Run configuration utility
python configure_zendesk_ai.py
```

### Test Connection

```bash
# Test Zendesk connection
run_zendesk_ai.bat --mode listviews  # Windows
./run_zendesk_ai.sh --mode listviews  # macOS/Linux
```

## Troubleshooting Commands

### Check Python Version

```bash
python --version   # Windows
python3 --version  # macOS/Linux
```

### Check MongoDB Connection

```bash
# For local MongoDB
mongosh --eval "db.adminCommand('ping')"

# For Docker MongoDB
docker exec zendesk_ai_mongodb mongosh --eval "db.adminCommand('ping')"
```

### Check Log Files

```bash
# View log file
type zendesk_ai.log     # Windows
cat zendesk_ai.log      # macOS/Linux

# View last 50 lines of log
type zendesk_ai.log | findstr /n "." | findstr /b "[45][0-9][0-9]:"  # Windows
tail -50 zendesk_ai.log                                             # macOS/Linux
```

### Reinstall After Download Issues

```bash
# If you encounter download issues, try:
# Windows:
set ZENDESK_AI_ORG=quanticsoul4772
set ZENDESK_AI_REPO=zendesk-ai-integration
set SKIP_CHECKSUM_VERIFY=true
python install.py

# macOS/Linux:
export ZENDESK_AI_ORG=quanticsoul4772
export ZENDESK_AI_REPO=zendesk-ai-integration
export SKIP_CHECKSUM_VERIFY=true
python3 install.py
```
