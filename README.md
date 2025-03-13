# Zendesk AI Integration

This application integrates Zendesk support tickets with OpenAI to provide automatic categorization and sentiment analysis.

## Features

- Automatic ticket categorization using AI
- Sentiment analysis for customer communications
- PostgreSQL database for analytics and reporting
- Enhanced security features:
  - IP whitelisting for webhook endpoints
  - HMAC signature verification
  - Robust error handling
- Multiple operation modes:
  - One-time batch processing
  - Real-time webhook processing
  - Scheduled daily/weekly analysis

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up PostgreSQL database
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

# Database configuration
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zendesk_analytics

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

## Webhook Configuration

See [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) for detailed instructions on setting up Zendesk webhooks.

## Project Structure

- `src/zendesk_ai_app.py` - Main application file
- `src/security.py` - Security-related functions and decorators
- `src/ai_service.py` - OpenAI integration with error handling

## License

MIT
