# Multi-View Reporting

This document explains the multi-view reporting feature that allows comparison of data across different Zendesk views.

## Overview

Multi-view reporting enables support teams to compare sentiment metrics, priority levels, and other key performance indicators across different support queues or organizational views. This provides deeper insights into support trends and helps identify areas that need attention.

## Usage

To generate a multi-view report, use the following command:

```bash
python -m src.main report --type multi-view --view-ids 12345,67890 --days 7
```

Or by view names:

```bash
python -m src.main report --type multi-view --view-names "Support :: Pending,Support :: Open" --days 7
```

Additional options include:

```bash
# Generate enhanced multi-view report
python -m src.main report --type multi-view --view-ids 12345,67890 --enhanced

# Generate multi-view report with specific output format
python -m src.main report --type multi-view --view-names "Support :: Pending,Support :: Open" --format html

# Generate multi-view report and save to a specific file
python -m src.main report --type multi-view --view-ids 12345,67890 --output multi_view_report.txt
```

## Report Content

The multi-view report includes:

### 1. Overall Summary

An overview of all analyzed views with aggregate metrics:

```
MULTI-VIEW SENTIMENT ANALYSIS REPORT
-----------------------------------
Report generated: 2025-04-12 15:30:45
Total views: 3
Total tickets analyzed: 152

Overall Sentiment Distribution:
  - Positive: 34 (22.4%)
  - Negative: 58 (38.2%)
  - Neutral: 60 (39.5%)

Business Impact Detected: 87 (57.2%)
```

### 2. Per-View Analysis

Detailed metrics for each view included in the report:

```
View: Support :: Pending
-----------------------
Tickets analyzed: 67

Sentiment Distribution:
  - Positive: 12 (17.9%)
  - Negative: 32 (47.8%)
  - Neutral: 23 (34.3%)

Business Impact Detected: 45 (67.2%)
Average Priority Score: 6.8
```

### 3. Comparative Metrics

When using enhanced format, additional comparative metrics are included:

```
COMPARATIVE METRICS
-----------------
Average Priority Score by View:
  - Support :: Pending: 6.8
  - Support :: Open: 5.2
  - Support :: Solved: 3.5

Business Impact Percentage by View:
  - Support :: Pending: 67.2%
  - Support :: Open: 43.8%
  - Support :: Solved: 22.5%
```

### 4. Top Issues by View

Identifies the most common issues in each view:

```
TOP ISSUES BY VIEW
----------------
Support :: Pending:
  - GPU Failures: 15 tickets (22.4%)
  - Memory Issues: 12 tickets (17.9%)
  - System Crashes: 8 tickets (11.9%)

Support :: Open:
  - Network Problems: 14 tickets (21.9%)
  - Software Compatibility: 11 tickets (17.2%)
  - Driver Issues: 8 tickets (12.5%)
```

## Benefits

Multi-view reporting provides several key benefits:

1. **Queue Comparison**: Identify which support queues have the highest priority or most negative sentiment
2. **Team Performance**: Compare resolution metrics across different support teams
3. **Resource Allocation**: Determine which areas need additional support resources
4. **Trend Analysis**: Track how sentiment changes as tickets move through different queues
5. **Customer Segment Analysis**: Compare sentiment across different customer segments by view

## Implementation Details

Multi-view reporting is implemented in the reporter modules within the `src/presentation/reporters` directory. The `generate_multi_view_report` method in each reporter handles the comparison of data across multiple views.

The implementation follows Clean Architecture principles:

1. The command handler (`generate_report_command.py`) receives the request for a multi-view report
2. It calls the appropriate use case with the specified views
3. The use case fetches data for all views and passes it to the reporter
4. The reporter generates comparative analysis and formats the report
5. The command handler displays or saves the resulting report

## Common Use Cases

### Support Queue Health Check

Compare metrics across all active support queues to identify bottlenecks:

```bash
python -m src.main report --type multi-view --view-names "Support :: New,Support :: Open,Support :: Pending,Support :: Solved" --enhanced
```

### Team Performance Comparison

Compare metrics across different team views to evaluate performance:

```bash
python -m src.main report --type multi-view --view-names "Team A :: All,Team B :: All,Team C :: All" --days 30
```

### Customer Segment Analysis

Compare metrics across different customer segment views:

```bash
python -m src.main report --type multi-view --view-names "Enterprise Customers,SMB Customers,Individual Customers"
```

### Hardware vs. Software Issue Comparison

Compare metrics between hardware and software issue queues:

```bash
python -m src.main report --type multi-view --view-names "Hardware Issues,Software Issues"
```