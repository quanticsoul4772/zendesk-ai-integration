# Zendesk AI Integration - Copy-Paste Command Sheet

This document provides ready-to-use commands for installing and using the Zendesk AI Integration. Simply copy and paste these commands into your terminal/command prompt.

## Windows Commands

### Installation

```batch
:: Download the installer
curl -o install.py https://raw.githubusercontent.com/exxactcorp/zendesk-ai-integration/main/install.py

:: Run the installer
python install.py
```

### Running the Application

```batch
:: List Zendesk views
run_zendesk_ai.bat --mode list-views

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
# Download the installer
curl -o install.py https://raw.githubusercontent.com/exxactcorp/zendesk-ai-integration/main/install.py

# Run the installer
python3 install.py
```

### Running the Application

```bash
# List Zendesk views
./run_zendesk_ai.sh --mode list-views

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
run_zendesk_ai.bat --mode list-views  # Windows
./run_zendesk_ai.sh --mode list-views  # macOS/Linux
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
