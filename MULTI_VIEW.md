# Multi-View Analysis

The Multi-View Analysis feature allows you to process tickets from multiple Zendesk views in a single command, generating consolidated reports that provide insights across different support queues.

## Use Cases

- **Cross-Queue Analysis**: Compare sentiment metrics across different support queues
- **Comprehensive Reporting**: Generate organization-wide sentiment analysis reports
- **Status Overview**: Get a snapshot of all support queues at once
- **Workload Distribution**: Identify which views have the most high-priority tickets
- **Business Impact Assessment**: Find critical issues across multiple views
- **Hardware Trend Analysis**: Identify which components are causing issues across different queues

## Using Multi-View Analysis

### Specifying Multiple Views by ID

To analyze tickets from multiple views using their IDs:

```bash
python src/zendesk_ai_app.py --mode multi-view --views 18002932412055,25973272172823,25764222686871 --output multi_view_report.txt
```

### Specifying Multiple Views by Name

To analyze tickets from multiple views using their names:

```bash
python src/zendesk_ai_app.py --mode multi-view --view-names "Support :: Escalated Tickets,Support :: Pending Customer" --output multi_view_report.txt
```

This feature is now fully functional in all modes. The system will match view names exactly when possible, and fall back to partial matching if needed.

### Additional Options

You can customize the multi-view analysis with additional parameters:

- `--status all`: Include tickets of all statuses (default is "open")
- `--limit 100`: Limit the number of tickets per view
- `--format enhanced`: Use enhanced reporting with component analysis and more detailed information
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
- Top affected components analysis (new feature)
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

### Enhanced Sentiment Analysis Across Multiple Views

```bash
python src/zendesk_ai_app.py --mode multi-view --views 18002932412055,25973272172823,25764222686871 --format enhanced --output enhanced_multi_view_report.txt
```

### Hardware Component Analysis Using View Names

```bash
python src/zendesk_ai_app.py --mode multi-view --view-names "Support :: Pending Customer,Support :: Pending RMA" --format enhanced --output component_analysis_report.txt
```

### Full Status Analysis (All Ticket Statuses)

```bash
python src/zendesk_ai_app.py --mode multi-view --views 18002932412055,25973272172823,25764222686871 --status all --format enhanced --output full_status_report.txt
```

## Top Components Analysis

The multi-view report now includes a TOP AFFECTED COMPONENTS section that provides insight into which hardware components are causing the most issues across all views:

```
TOP AFFECTED COMPONENTS
---------------------
gpu: 22 (36.7%)
drive: 7 (11.7%)
boot: 5 (8.3%)
ipmi: 4 (6.7%)
display: 4 (6.7%)
network: 4 (6.7%)
bios: 3 (5.0%)
power_supply: 3 (5.0%)
memory: 3 (5.0%)
motherboard: 3 (5.0%)
cooling: 1 (1.7%)
software: 1 (1.7%)
```

This section helps identify patterns in hardware issues that may require systematic attention or proactive maintenance across different support queues.

## High Priority Tickets Display

The enhanced multi-view report now displays up to 10 high-priority tickets (increased from 5) with detailed information:

```
HIGH PRIORITY TICKETS
--------------------
Found 62 high priority tickets (priority 7-10)

#26572 - Server Hardware Issues.
  Priority: 9/10 - Critical Priority (Urgent action needed, significant business impact)
  Sentiment: Negative
  Urgency: 5/5 - Critical emergency with major business impact
  Frustration: 4/5 - Highly frustrated
  Business Impact: Production system completely down, losing critical Splunk indexers for a classified network
  Emotions: anger, frustration, worry
  Component: motherboard
  Category: hardware_issue

#27993 - Re: [Exxact Corporation] Ticket #26415 - Re: Consistent Machine Freezing Issue
  Priority: 9/10 - Critical Priority (Urgent action needed, significant business impact)
  Sentiment: Negative
  Urgency: 4/5 - Serious issues requiring prompt resolution
  Frustration: 5/5 - Extremely frustrated
  Business Impact: Production system down, significant productivity loss, risk of missing deadlines and contract obligations
  Emotions: anger, frustration, urgency
  Category: hardware_issue
```

This expanded view ensures that the most important tickets across multiple queues are visible to support management.

## Performance Considerations

When analyzing multiple views with many tickets, the process may take longer due to:

1. Multiple API calls to Zendesk (one per view)
2. AI analysis of each ticket (which involves API calls to OpenAI or Claude)
3. Report generation across all tickets

For large views, consider using the `--limit` parameter to restrict the number of tickets processed per view.

## Cache Reliability Features

The multi-view analysis mode includes improved cache handling to prevent stale data issues:

### Automatic Cache Refresh

When running in multi-view mode, the system automatically refreshes the views cache before fetching tickets:

```python
# Force refresh the views cache to ensure we have fresh data
zendesk_client.cache.force_refresh_views()
logger.info("Forced refresh of views cache before fetching tickets")
```

### Empty View Detection and Recovery

If no valid views are found, the system will automatically refresh the cache for next time:

```python
if not valid_views:
    logger.warning("None of the specified views exist or are accessible")
    # Force refresh the views cache for next time
    self.cache.force_refresh_views()
    return []
```

### Troubleshooting Cache Issues

If you encounter persistent cache issues, try running these commands in sequence:

```bash
# First list views to refresh the cache
python src/zendesk_ai_app.py --mode list-views

# Then run your multi-view analysis
python src/zendesk_ai_app.py --mode multi-view --views VIEW_IDS
```

This sequence ensures the system has fresh view data before attempting to fetch tickets from multiple views.
