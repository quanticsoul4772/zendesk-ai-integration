# Zendesk AI Integration

This application integrates Zendesk support tickets with AI services (OpenAI and Anthropic Claude) to provide automated sentiment analysis, categorization, and reporting while maintaining a read-only approach to customer tickets.

## Features

- **Read-only sentiment analysis** - analyzes tickets without modifying them
- **Multi-LLM Support**:
  - OpenAI's advanced GPT-4o model
  - Anthropic's Claude models
- **Enhanced sentiment analysis** with urgency, frustration, and business impact detection:
  - Contextual examples for better sentiment classification
  - Temperature-controlled variance for more nuanced analysis
  - Urgency level detection (1-5 scale)
  - Frustration level detection (1-5 scale)
  - Business impact assessment
  - Technical expertise estimation
  - Priority score calculation (1-10 scale)
  - Key phrase extraction
  - Emotion detection
- **Intuitive reporting** with descriptive labels and contextual information:
  - Executive summary highlighting critical issues
  - Descriptive labels for numerical scales
  - Percentage values for all metrics
  - Summaries and alerts for significant findings
  - Top components analysis
- **Hardware component detection** in tickets
- **MongoDB database** for analytics and reporting
- **Enhanced security features**:
  - IP whitelisting for webhook endpoints
  - HMAC signature verification
  - Robust error handling
- **Performance optimizations**:
  - Caching system for Zendesk data with TTL
  - Parallel batch processing for ticket analysis
  - See [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for details
- **Multiple operation modes**:
  - One-time batch analysis
  - Real-time webhook analysis
  - Scheduled daily/weekly analysis
  - View-based reporting and analytics
  - Multi-view aggregated analysis
- **Comprehensive sentiment reporting**:
  - Sentiment distribution analysis
  - Urgency and frustration level reporting
  - Business impact assessment
  - High-priority ticket identification

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up MongoDB database
6. Configure environment variables in `.env` file

## Configuration

Create a `.env` file with the following variables:

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
DISABLE_TAG_UPDATES=false
```

### Security Configuration

- **WEBHOOK_SECRET_KEY**: A secure random key used to verify webhook signatures from Zendesk
- **ALLOWED_IPS**: Comma-separated list of IP addresses or CIDR ranges allowed to access the webhook

You can generate a secure webhook key with this command:
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

This will reprocess all tickets from the last 7 days with the enhanced sentiment model.

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

### Generate Summary

Create a summary of ticket data:

```bash
python src/zendesk_ai_app.py --mode summary --status solved --days 7
```

### View-Based Reporting

Generate a report for a specific Zendesk view:

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support"
```

### Enhanced Reporting

Generate reports with descriptive labels and more intuitive formatting:

```bash
python src/zendesk_ai_app.py --mode sentiment --days 7 --format enhanced
```

For multi-view enhanced reports:

```bash
python src/zendesk_ai_app.py --mode sentiment --views 18002932412055,25973272172823 --format enhanced
```

See [ENHANCED_REPORTS.md](ENHANCED_REPORTS.md) for more information on the enhanced reporting feature.

This will generate a comprehensive report of all tickets in the specified view, including status distribution, hardware component analysis, and detailed ticket information.

If you want to limit the number of tickets in the report:

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support" --limit 10
```

### List Available Views

To see all available Zendesk views:

```bash
python src/zendesk_ai_app.py --mode list-views
```

### Hardware Component Reports

Generate a hardware-focused report for a specific view:

```bash
python src/zendesk_ai_app.py --mode run --view [VIEW_ID] --component-report
```

### Multi-View Analysis

Analyze tickets from multiple views at once:

```bash
python src/zendesk_ai_app.py --mode sentiment --views 18002932412055,25973272172823 --output multi_view_report.txt
```

Or use view names instead of IDs:

```bash
python src/zendesk_ai_app.py --mode sentiment --view-names "Support :: Pending Customer,Support :: Pending RMA" --output multi_view_report.txt
```

See [MULTI_VIEW.md](MULTI_VIEW.md) for detailed documentation on multi-view analysis.

## Documentation

- [README.md](README.md) - Main documentation
- [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) - Webhook configuration instructions
- [REPORTING.md](REPORTING.md) - Detailed reporting documentation
- [JSON_PARSING.md](JSON_PARSING.md) - JSON parsing enhancements
- [SENTIMENT_ANALYSIS.md](SENTIMENT_ANALYSIS.md) - Sentiment analysis methodology
- [MULTI_VIEW.md](MULTI_VIEW.md) - Multi-view analysis documentation
- [ENHANCED_REPORTS.md](ENHANCED_REPORTS.md) - Enhanced reporting documentation
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - Performance optimization features

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
- `src/modules/reporters/` - Contains report generators:
  - `hardware_report.py` - Generates hardware component reports
  - `pending_report.py` - Generates pending support reports
  - `sentiment_report.py` - Generates sentiment analysis reports

### AI Services
- `src/ai_service.py` - OpenAI integration with error handling
- `src/enhanced_sentiment.py` - Enhanced OpenAI sentiment analysis implementation
- `src/claude_service.py` - Anthropic Claude integration with error handling
- `src/claude_enhanced_sentiment.py` - Enhanced Claude sentiment analysis implementation
- `src/security.py` - Security-related functions and decorators

## Design Philosophy

This application follows a read-only design philosophy where tickets are analyzed but never modified. All analysis results are stored in the database for reporting and analytics purposes. This approach provides:

1. **Non-Intrusive Analysis**: Analyze tickets without modifying them
2. **Historical Tracking**: Store analysis results for trend analysis
3. **Comprehensive Reporting**: Generate detailed sentiment reports
4. **Safety**: Prevent unintended modifications to production tickets

By keeping the system read-only, it can safely be used in production environments without risk of interfering with support workflows.

## License

MIT