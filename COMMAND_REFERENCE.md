# Zendesk AI Integration Command Reference

This document provides a comprehensive reference for all commands and options available in the Zendesk AI Integration tool.

## Main Commands

```bash
python -m src.main [command] [options]
```

### Available Commands:

1. **views** - List all available Zendesk views
   ```bash
   python -m src.main views [options]
   ```
   Options:
   - `--format [text|json|csv]` - Output format (default: text)
   - `--output [filepath]` - Output file path (default: print to console)
   - `--flat` - Display as a flat list instead of a hierarchy
   - `--include-inactive` - Include inactive views
   - `--filter [string]` - Filter views by name (case-insensitive)

2. **analyze** - Analyze tickets
   ```bash
   python -m src.main analyze [options]
   ```
   Options:
   - `--ticket-id [id]` - Analyze a specific ticket by ID
   - `--view-id [id]` - Analyze tickets from a specific view
   - `--view-name [name]` - Analyze tickets from a view by name
   - `--ticket-query [query]` - Zendesk search query to find tickets to analyze
   - `--limit [number]` - Maximum number of tickets to analyze
   - `--days [number]` - Number of days back to analyze tickets (default: 7)
   - `--add-tags` - Add analysis tags to tickets
   - `--add-comment` - Add analysis comments to tickets
   - `--format [text|json]` - Output format (default: text)
   - `--reanalyze` - Reanalyze tickets that have already been analyzed
   - `--use-openai` - Use OpenAI instead of Claude for analysis

3. **report** - Generate reports
   ```bash
   python -m src.main report [options]
   ```
   Options:
   - `--type [sentiment|enhanced-sentiment|hardware|pending|multi-view]` - Report type
   - `--days [number]` - Number of days to include in the report
   - `--view-id [id]` - Generate report for a specific view
   - `--view-name [name]` - Name of the view to include in the report
   - `--view-ids [ids]` - Comma-separated list of view IDs
   - `--view-names [names]` - Comma-separated list of view names
   - `--output [filepath]` - Output file path
   - `--format [text|html|csv|json]` - Output format
   - `--enhanced` - Use enhanced format with more details (alternatively use --type enhanced-sentiment)
   - `--limit [number]` - Maximum number of tickets to include

4. **interactive** - Launch interactive mode
   ```bash
   python -m src.main interactive
   ```

5. **webhook** - Manage webhooks
   ```bash
   python -m src.main webhook [options]
   ```
   Options:
   - `--start` - Start the webhook server
   - `--stop` - Stop the webhook server
   - `--status` - Check webhook server status
   - `--host [hostname]` - Webhook server hostname (default: 0.0.0.0)
   - `--port [port]` - Webhook server port (default: 8000)

6. **schedule** - Manage scheduled tasks
   ```bash
   python -m src.main schedule [options]
   ```
   Options:
   - `--list` - List all scheduled tasks
   - `--add` - Add a new scheduled task
   - `--remove [id]` - Remove a scheduled task
   - `--type [analyze|report]` - Task type
   - `--interval [minutes]` - Task interval in minutes
   - `--view-id [id]` - View ID to process
   - `--report-type [sentiment|enhanced-sentiment|hardware|pending|multi-view]` - Report type for report tasks

## Global Options

These options can be used with any command:

- `--config [filepath]` - Path to configuration file
- `--log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]` - Logging level (default: INFO)
- `--log-file [filepath]` - Path to log file

## Helper Scripts

1. **show_commands.py** - Display all available commands and options
   ```bash
   python show_commands.py
   ```

2. **simple_views.py** - Simple script to list all Zendesk views directly
   ```bash
   python simple_views.py
   ```

3. **test_views.py** - Test script for the views command
   ```bash
   python test_views.py
   ```

## Examples

```bash
# List all active views in hierarchical format
python -m src.main views

# List all views including inactive ones in a flat list
python -m src.main views --flat --include-inactive

# Analyze a specific ticket
python -m src.main analyze --ticket-id 12345

# Analyze tickets from a view
python -m src.main analyze --view-id 67890 --limit 10

# Generate a sentiment report
python -m src.main report --type sentiment --days 7

# Generate an enhanced sentiment report
python -m src.main report --type enhanced-sentiment --days 7
# OR
python -m src.main report --type sentiment --enhanced --days 7

# Generate a multi-view report
python -m src.main report --type multi-view --view-ids 12345,67890 --days 7
# OR
python -m src.main report --type multi-view --view-names "Support :: Pending,Support :: Open" --days 7

# Start webhook server
python -m src.main webhook --start --host 0.0.0.0 --port 8000

# List scheduled tasks
python -m src.main schedule --list
```