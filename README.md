# Zendesk AI Integration

This application integrates Zendesk support tickets with OpenAI to provide automatic categorization and sentiment analysis.

## Features

- Automatic ticket categorization using AI
- Sentiment analysis for customer communications
- PostgreSQL database for analytics and reporting
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
ZENDESK_EMAIL=your_email@company.com
ZENDESK_API_TOKEN=your_zendesk_api_token
ZENDESK_SUBDOMAIN=your_zendesk_subdomain
OPENAI_API_KEY=your_openai_api_key
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zendesk_analytics
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Usage

### One-time Analysis

```bash
python src/zendesk_ai_app.py --mode run --status open --limit 5
```

### Webhook Server

```bash
python src/zendesk_ai_app.py --mode webhook
```

### Scheduled Analysis

```bash
python src/zendesk_ai_app.py --mode schedule
```

## License

MIT
