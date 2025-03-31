# Zendesk AI Integration

[![Python Tests](https://github.com/yourusername/zendesk-ai-integration/actions/workflows/python-tests.yml/badge.svg)](https://github.com/yourusername/zendesk-ai-integration/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/yourusername/zendesk-ai-integration/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/zendesk-ai-integration)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-black)](https://github.com/pycqa/flake8)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/zendesk-ai-integration/blob/main/VERSION.md)

This application integrates Zendesk support tickets with AI services (OpenAI and Anthropic Claude) to provide automated sentiment analysis, categorization, and reporting while maintaining a read-only approach to customer tickets.

## Quick Start

### One-Step Installation

Run the universal installer script which works on Windows, macOS, and Linux:

```bash
# Download the installer
curl -o install.py https://raw.githubusercontent.com/yourusername/zendesk-ai-integration/main/install.py

# Run the installer
python install.py
```

The installer will:
1. Check if your system meets all requirements
2. Download necessary files
3. Set up a Python virtual environment
4. Install all dependencies
5. Guide you through configuration
6. Create OS-specific convenience scripts

After installation, you can run the application using:

**Windows**:
```
run_zendesk_ai.bat --mode list-views
```

**macOS/Linux**:
```
./run_zendesk_ai.sh --mode list-views
```

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

## Features

### AI Integration
- **Multi-LLM Support**:
  - **OpenAI**: Advanced GPT-4o model with GPT-3.5 Turbo fallback
  - **Anthropic Claude**: Claude 3 models (Haiku, Sonnet) with multiple fallbacks
  - Seamless switching between AI providers
  - Automatic error handling and retry logic

### Enhanced Sentiment Analysis
- **Nuanced Analysis**:
  - Contextual examples for better sentiment classification
  - Temperature-controlled variance for nuanced analysis
  - Sentiment polarity detection (positive, negative, neutral)
- **Support Metrics**:
  - Urgency level detection (1-5 scale)
  - Frustration level detection (1-5 scale)
  - Technical expertise estimation
  - Priority score calculation (1-10 scale)
- **Business Intelligence**:
  - Business impact assessment
  - Key phrase extraction
  - Emotion detection

### Reporting Capabilities
- **Intuitive Reporting** with descriptive labels and contextual information
  - Executive summary highlighting critical issues
  - Descriptive labels for numerical scales
  - Percentage values for all metrics
  - Summaries and alerts for significant findings
- **Specialized Reports**:
  - Hardware component detection and analysis
  - Multi-view aggregated analytics
  - Sentiment distribution analysis
  - High-priority ticket identification

### Performance & Security
- **Read-only Design** - analyzes tickets without modifying them
- **Performance Optimizations**:
  - Caching system with TTL and intelligent cache validation
  - Parallel batch processing for ticket analysis
  - Self-healing cache with automatic refresh mechanism
- **Enhanced Security**:
  - IP whitelisting for webhook endpoints
  - HMAC signature verification
  - Robust error handling and input validation

### Multiple Operation Modes
- One-time batch analysis
- Real-time webhook analysis
- Scheduled daily/weekly analysis
- View-based reporting and analytics
- Multi-view aggregated analysis

## Installation

### Automated Installation (Recommended)

The project includes several automated installation options:

1. **Universal Installer (Easiest)**:
   ```bash
   python install.py
   ```

2. **Step-by-Step Setup**:
   ```bash
   python check_prerequisites.py  # Check system requirements
   python setup.py                # Run guided setup
   ```

3. **Configuration Helper**:
   ```bash
   python configure_zendesk_ai.py  # Update configuration
   ```

### Manual Installation

For manual installation:

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up MongoDB database
6. Configure environment variables in `.env` file
7. Set up pre-commit hooks: `pre-commit install` (see [PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md) for details)

See [INSTALLATION.md](INSTALLATION.md) for detailed OS-specific instructions for Windows, macOS, and Linux.

## Configuration

Create a `.env` file with your configuration (or copy and modify `.env.example`):

```
# Zendesk API credentials
ZENDESK_EMAIL=your_email@company.com
ZENDESK_API_TOKEN=your_zendesk_api_token
ZENDESK_SUBDOMAIN=your_zendesk_subdomain

# AI API keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# MongoDB configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=zendesk_analytics
MONGODB_COLLECTION_NAME=ticket_analysis

# Slack integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Security settings
WEBHOOK_SECRET_KEY=your_secure_random_key_here
ALLOWED_IPS=127.0.0.1,10.0.0.0/24

# Feature flags
DISABLE_TAG_UPDATES=true
```

The `.env.example` file includes additional configuration options for:
- Caching settings
- Performance tuning parameters
- Logging configuration
- Report settings

Generate a secure webhook key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

### Sentiment Analysis with Claude or OpenAI

Analyze tickets with Claude (default):

```bash
python src/zendesk_ai_app.py --mode run --status open
```

Specify OpenAI instead of Claude:

```bash
python src/zendesk_ai_app.py --mode run --status open --use-openai
```

Enhanced sentiment analysis is now the standard for all operations.

To reanalyze existing tickets with the improved sentiment model:

```bash
python src/zendesk_ai_app.py --mode run --reanalyze --days 7
```

### Sentiment Analysis Reporting

Generate detailed sentiment analysis reports:

```bash
python src/zendesk_ai_app.py --mode sentiment --days 7
```

This generates a comprehensive report including:
- Sentiment distribution
- Urgency and frustration levels
- Business impact assessment
- High-priority tickets
- Average sentiment metrics

You can specify a specific view:

```bash
python src/zendesk_ai_app.py --mode sentiment --view "Support Queue"
```

Or output to a file:

```bash
python src/zendesk_ai_app.py --mode sentiment --days 30 --output sentiment_report.txt
```

### View-Based Reporting

Generate a report for a specific Zendesk view:

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support"
```

For multi-view enhanced reports:

```bash
python src/zendesk_ai_app.py --mode sentiment --views 18002932412055,25973272172823 --format enhanced
```

### Webhook Server

Start a webhook server for real-time analysis:

```bash
python src/zendesk_ai_app.py --mode webhook
```

### Scheduled Analysis

Run daily and weekly summaries automatically:

```bash
python src/zendesk_ai_app.py --mode schedule
```

### List Available Views

To see all available Zendesk views:

```bash
python src/zendesk_ai_app.py --mode list-views
```

For more usage examples, see:
- [ENHANCED_REPORTS.md](ENHANCED_REPORTS.md) - Enhanced reporting feature
- [MULTI_VIEW.md](MULTI_VIEW.md) - Multi-view analysis documentation

## Development Timeline

### March 2025
- **Mar 12:** Initial project creation
- **Mar 18:** Added test framework and OpenAI integration
- **Mar 22:** Added configuration samples and security enhancements
- **Mar 25:** Implemented comprehensive Zendesk view reporting
- **Mar 26:** Added Claude AI integration and multi-view analysis
- **Mar 27:** Implemented performance optimizations and caching
- **Mar 30:** Added cross-platform installation scripts and enhanced documentation

For full commit history, see [VERSION.md](VERSION.md).

## Documentation

- [README.md](README.md) - Main documentation
- [INSTALLATION.md](INSTALLATION.md) - Detailed installation instructions for all platforms
- [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) - Webhook configuration instructions
- [REPORTING.md](REPORTING.md) - Detailed reporting documentation
- [ENHANCED_REPORTS.md](ENHANCED_REPORTS.md) - Enhanced reporting documentation
- [MULTI_VIEW.md](MULTI_VIEW.md) - Multi-view analysis documentation
- [SENTIMENT_ANALYSIS.md](SENTIMENT_ANALYSIS.md) - Sentiment analysis methodology
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - Performance optimization features
- [TESTING.md](TESTING.md) - Testing strategy and instructions
- [PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md) - Pre-commit hooks setup guide
- [VERSION.md](VERSION.md) - Version history and release notes

## Architecture and Project Structure

The application follows the Single Responsibility Principle, with each module having a clearly defined responsibility:

### Main Components

- `src/zendesk_ai_app.py` - Entry point that coordinates between modules
- `src/modules/` - Directory containing modular components:
  - `zendesk_client.py` - Handles all Zendesk API interactions (read-only)
  - `ai_analyzer.py` - Processes ticket content using AI services
  - `db_repository.py` - Manages database operations
  - `webhook_server.py` - Handles webhook requests
  - `scheduler.py` - Manages scheduled tasks
  - `cli.py` - Command-line interface and argument parsing

### Reporters Package
- `src/modules/reporters/` - Contains report generators
  
### AI Services
- `src/ai_service.py` - OpenAI integration with error handling
- `src/enhanced_sentiment.py` - Enhanced OpenAI sentiment analysis implementation
- `src/claude_service.py` - Anthropic Claude integration with error handling
- `src/claude_enhanced_sentiment.py` - Enhanced Claude sentiment analysis implementation
- `src/security.py` - Security-related functions and decorators

### Installation Components
- `install.py` - Universal installer script for all platforms
- `check_prerequisites.py` - System requirements checker
- `setup.py` - Guided installation and configuration script

## Dependencies

This project requires Python 3.9+ and the following key dependencies:
- zenpy>=2.0.56
- openai>=1.63.0
- anthropic>=0.49.0
- pymongo>=4.11.3
- flask>=3.0.0
- requests>=2.32.0

See [requirements.txt](requirements.txt) for the complete list of dependencies.

## Troubleshooting

If you encounter any issues:

1. Run the prerequisites checker: `python check_prerequisites.py`
2. Check the error logs (usually in the console output)
3. Verify your MongoDB connection and API keys
4. See [INSTALLATION.md](INSTALLATION.md) for common issues and solutions
5. Open an issue on the GitHub repository with detailed information

## Design Philosophy

This application follows a read-only design philosophy where tickets are analyzed but never modified. All analysis results are stored in the database for reporting and analytics purposes. This approach provides:

1. **Non-Intrusive Analysis**: Analyze tickets without modifying them
2. **Historical Tracking**: Store analysis results for trend analysis
3. **Comprehensive Reporting**: Generate detailed sentiment reports
4. **Safety**: Prevent unintended modifications to production tickets

By keeping the system read-only, it can safely be used in production environments without risk of interfering with support workflows.

## License

MIT

## Last Updated

March 30, 2025
