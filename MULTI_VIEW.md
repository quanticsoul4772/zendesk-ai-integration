# Multi-View Analysis

The Multi-View Analysis feature allows you to process tickets from multiple Zendesk views in a single command, generating consolidated reports that provide insights across different support queues.

## Use Cases

- **Cross-Queue Analysis**: Compare sentiment metrics across different support queues
- **Comprehensive Reporting**: Generate organization-wide sentiment analysis reports
- **Status Overview**: Get a snapshot of all support queues at once
- **Workload Distribution**: Identify which views have the most high-priority tickets
- **Business Impact Assessment**: Find critical issues across multiple views

## Using Multi-View Analysis

### Specifying Multiple Views by ID

To analyze tickets from multiple views using their IDs:

```bash
python src/zendesk_ai_app.py --mode sentiment --views 18002932412055,25973272172823,25764222686871 --output multi_view_report.txt
```

### Specifying Multiple Views by Name

To analyze tickets from multiple views using their names:

```bash
python src/zendesk_ai_app.py --mode sentiment --view-names "Support :: Escalated Tickets,Support :: Pending Customer" --output multi_view_report.txt
```

### Additional Options

You can customize the multi-view analysis with additional parameters:

- `--status all`: Include tickets of all statuses (default is "open")
- `--limit 100`: Limit the number of tickets per view
- `--basic-sentiment`: Use basic sentiment analysis instead of enhanced
- `--use-openai`: Use OpenAI instead of Claude for analysis

## Report Structure

The multi-view report includes:

### Overview Section
- Total tickets analyzed
- Number of views included
- Tickets per view breakdown

### Combined Analysis
- Overall sentiment distribution
- Priority score distribution
- Average urgency, frustration, and priority scores
- Business impact assessment

### Per-View Analysis
For each view, the report includes:
- Sentiment distribution
- High-priority ticket count
- Business impact ticket count
- Average metrics (urgency, frustration, priority)
- Top high-priority tickets

## Example Commands

### Sentiment Analysis Across Multiple Views

```bash
python src/zendesk_ai_app.py --mode sentiment --views 18002932412055,25973272172823,25764222686871 --output sentiment_report.txt
```

### Hardware Component Analysis Across Multiple Views

```bash
python src/zendesk_ai_app.py --mode report --views 18002932412055,25973272172823,25764222686871 --output hardware_report.txt
```

### Pending Support Analysis Across Multiple Views

```bash
python src/zendesk_ai_app.py --mode pending --view-names "Support :: Pending Customer,Support :: Pending RMA" --output pending_report.txt
```

## Direct Multi-View Mode

You can also use the dedicated multi-view mode:

```bash
python src/zendesk_ai_app.py --mode multi-view --views 18002932412055,25973272172823,25764222686871 --output multi_view_report.txt
```

This mode is optimized for multi-view analysis and provides the most comprehensive cross-view reporting.

## Performance Considerations

When analyzing multiple views with many tickets, the process may take longer due to:

1. Multiple API calls to Zendesk (one per view)
2. AI analysis of each ticket (which involves API calls to OpenAI or Claude)
3. Report generation across all tickets

For large views, consider using the `--limit` parameter to restrict the number of tickets processed per view.
