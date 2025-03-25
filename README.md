# Zendesk AI Integration

This application integrates Zendesk support tickets with OpenAI to provide automatic categorization and sentiment analysis. It also includes reporting functionality for Zendesk views.

## Features

- Automatic ticket categorization using AI
- Sentiment analysis for customer communications
- Hardware component detection in tickets
- MongoDB database for analytics and reporting
- Enhanced security features:
  - IP whitelisting for webhook endpoints
  - HMAC signature verification
  - Robust error handling
- Multiple operation modes:
  - One-time batch processing
  - Real-time webhook processing
  - Scheduled daily/weekly analysis
  - View-based reporting and analytics

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

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key

# MongoDB configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=zendesk_analytics
MONGODB_COLLECTION_NAME=ticket_analysis

# Slack integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Security settings
WEBHOOK_SECRET_KEY=your_secure_random_key_here
ALLOWED_IPS=127.0.0.1,10.0.0.0/24
```

### Security Configuration

- **WEBHOOK_SECRET_KEY**: A secure random key used to verify webhook signatures from Zendesk
- **ALLOWED_IPS**: Comma-separated list of IP addresses or CIDR ranges allowed to access the webhook

You can generate a secure webhook key with this command:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

### One-time Analysis

Process a batch of tickets:

```bash
python src/zendesk_ai_app.py --mode run --status open --limit 5
```

### Webhook Server

Start a webhook server for real-time processing:

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

## Documentation

- [README.md](README.md) - Main documentation
- [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) - Webhook configuration instructions
- [REPORTING.md](REPORTING.md) - Detailed reporting documentation

## Project Structure

- `src/zendesk_ai_app.py` - Main application file
- `src/ai_service.py` - OpenAI integration with error handling
- `src/mongodb_helper.py` - MongoDB database connection and queries
- `src/security.py` - Security-related functions and decorators

## License

MIT
