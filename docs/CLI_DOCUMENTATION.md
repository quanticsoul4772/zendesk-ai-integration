# CLI Documentation

This document provides detailed information about using the command-line interface for the Zendesk AI Integration tool.

## Overview

The Zendesk AI Integration tool provides a command-line interface (CLI) built using the Command pattern, which allows for clean separation of concerns and easy extension with new commands.

## Command Structure

All commands follow this general structure:

```
python -m src.main [COMMAND] [OPTIONS]
```

Where `[COMMAND]` is one of the available commands and `[OPTIONS]` are command-specific options.

## Available Commands

### Analyze Command

Analyzes tickets using AI services.

```
python -m src.main analyze [OPTIONS]
```

#### Options

- `--ticket-id INTEGER`: Analyze a specific ticket by ID
- `--view-id INTEGER`: Analyze all tickets in a specific view
- `--ai-provider [openai|claude]`: AI provider to use (default: claude)
- `--days INTEGER`: Limit to tickets created in the last X days
- `--limit INTEGER`: Maximum number of tickets to analyze
- `--add-comments`: Add analysis results as comments to tickets
- `--add-tags`: Add analysis-based tags to tickets
- `--output [json|text]`: Output format (default: text)
- `--output-file TEXT`: File to save output (optional)

#### Examples

```bash
# Analyze a specific ticket
python -m src.main analyze --ticket-id 12345

# Analyze tickets in a view
python -m src.main analyze --view-id 67890 --limit 10

# Analyze tickets using OpenAI
python -m src.main analyze --view-id 67890 --ai-provider openai

# Analyze and add comments
python -m src.main analyze --ticket-id 12345 --add-comments
```

### Report Command

Generates various reports based on ticket analysis.

```
python -m src.main report [OPTIONS]
```

#### Options

- `--type [sentiment|hardware|pending]`: Type of report to generate (required)
- `--view-id INTEGER`: Generate report for a specific view
- `--days INTEGER`: Include tickets from the last X days
- `--start-date TEXT`: Start date for report (format: YYYY-MM-DD)
- `--end-date TEXT`: End date for report (format: YYYY-MM-DD)
- `--format [text|html|json|csv]`: Output format (default: text)
- `--output-file TEXT`: File to save report (optional)
- `--compare-views`: Compare multiple views (use with multiple --view-id)
- `--enhanced`: Use enhanced analysis for sentiment reports

#### Examples

```bash
# Generate a sentiment report
python -m src.main report --type sentiment --days 7

# Generate a hardware report for a specific view
python -m src.main report --type hardware --view-id 12345

# Generate an enhanced sentiment report as HTML
python -m src.main report --type sentiment --enhanced --format html --output-file report.html

# Compare sentiment across views
python -m src.main report --type sentiment --view-id 123 --view-id 456 --compare-views
```

### Interactive Command

Launches an interactive menu for easier navigation.

```
python -m src.main interactive
```

This command has no options. It launches a text-based menu system that allows you to:
- Browse views
- Analyze tickets
- Generate reports
- Configure settings
- View recent analysis results

### Webhook Command

Manages the webhook server for real-time ticket processing.

```
python -m src.main webhook [OPTIONS]
```

#### Options

- `--start`: Start the webhook server
- `--stop`: Stop the webhook server
- `--status`: Check webhook server status
- `--host TEXT`: Host address to bind (default: 127.0.0.1)
- `--port INTEGER`: Port to listen on (default: 8000)
- `--endpoint TEXT`: Webhook endpoint path (default: /webhook)
- `--auto-analyze`: Automatically analyze new tickets
- `--ai-provider [openai|claude]`: AI provider for auto-analysis

#### Examples

```bash
# Start webhook server
python -m src.main webhook --start --host 0.0.0.0 --port 8000

# Start with auto-analysis
python -m src.main webhook --start --auto-analyze --ai-provider claude

# Check status
python -m src.main webhook --status

# Stop server
python -m src.main webhook --stop
```

### Schedule Command

Manages scheduled tasks for periodic processing.

```
python -m src.main schedule [OPTIONS]
```

#### Options

- `--list`: List all scheduled tasks
- `--add`: Add a new scheduled task
- `--remove`: Remove a scheduled task
- `--task [analyze_pending|generate_report]`: Task type
- `--view-id INTEGER`: View ID for task
- `--time TEXT`: Time to run (format: HH:MM)
- `--interval [daily|weekly|monthly]`: Frequency (default: daily)
- `--params TEXT`: Additional JSON-formatted parameters
- `--id INTEGER`: Task ID (for --remove)

#### Examples

```bash
# List scheduled tasks
python -m src.main schedule --list

# Schedule daily analysis of pending tickets
python -m src.main schedule --add --task analyze_pending --view-id 12345 --time "08:00"

# Schedule weekly sentiment report
python -m src.main schedule --add --task generate_report --params '{"type":"sentiment","days":7}' --interval weekly --time "07:00"

# Remove a scheduled task
python -m src.main schedule --remove --id 3
```

### Views Command

Lists available Zendesk views.

```
python -m src.main views [OPTIONS]
```

#### Options

- `--active`: Show only active views
- `--shared`: Show only shared views
- `--output [json|text]`: Output format (default: text)
- `--output-file TEXT`: File to save output (optional)

#### Examples

```bash
# List all views
python -m src.main views

# List active views in JSON format
python -m src.main views --active --output json
```

## Global Options

These options are available for all commands:

- `--help`: Show help message and exit
- `--verbose`: Enable verbose output
- `--quiet`: Suppress all output except errors
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Set logging level
- `--log-file TEXT`: Log file path
- `--config-file TEXT`: Configuration file path

## Using Environment Variables

You can also configure the tool using environment variables:

- `ZENDESK_EMAIL`: Your Zendesk email address
- `ZENDESK_API_TOKEN`: Your Zendesk API token
- `ZENDESK_SUBDOMAIN`: Your Zendesk subdomain
- `MONGODB_URI`: MongoDB connection string
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_API_KEY`: Anthropic Claude API key

## Return Codes

The CLI returns the following exit codes:

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: API error
- `4`: Database error
- `5`: Command validation error

## Further Information

For more detailed information about specific features, see:
- [Webhook Setup](WEBHOOK_SETUP.md)
- [Reporting](REPORTING.md)
- [Sentiment Analysis](SENTIMENT_ANALYSIS.md)
