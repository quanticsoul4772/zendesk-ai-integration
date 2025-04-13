# Enhanced Reporting

This document explains the enhanced reporting feature that adds more intuitive and meaningful data to sentiment analysis reports.

## Overview

The enhanced reporting feature makes sentiment analysis reports more intuitive by adding descriptive labels to numerical scales and organizing information in a more actionable way. It also provides additional data points and context to help support teams better understand the state of their tickets.

## Usage

To generate an enhanced sentiment report, use either of these commands:

```bash
python -m src.main report --type enhanced-sentiment --days 7
# OR
python -m src.main report --type sentiment --enhanced --days 7
```

Additional options include:

```bash
# Generate enhanced report for a specific view
python -m src.main report --type enhanced-sentiment --view-id 12345

# Generate enhanced report for a view by name
python -m src.main report --type enhanced-sentiment --view-name "Support :: Pending Customer"

# Generate enhanced report for multiple views
python -m src.main report --type enhanced-sentiment --view-ids 12345,67890
# OR
python -m src.main report --type enhanced-sentiment --view-names "Support :: Pending Customer,Support :: Pending RMA"

# Generate enhanced report and save to a specific file
python -m src.main report --type enhanced-sentiment --output enhanced_report.txt
```

## Key Improvements

### 1. Descriptive Labels for Numerical Scales

The enhanced report adds descriptive labels to make numerical scales more intuitive:

#### Urgency Levels (1-5):
- **Level 1**: Non-urgent inquiries
- **Level 2**: Minor issues without significant impact
- **Level 3**: Moderate issues affecting productivity
- **Level 4**: Serious issues requiring prompt resolution
- **Level 5**: Critical emergency with major business impact

#### Frustration Levels (1-5):
- **Level 1**: Satisfied customers
- **Level 2**: Mildly concerned
- **Level 3**: Noticeably frustrated
- **Level 4**: Highly frustrated
- **Level 5**: Extremely frustrated

#### Priority Scores (1-10):
- **Low Priority (1-3)**: Non-critical issues that can be addressed when time permits
- **Medium Priority (4-6)**: Important issues that should be addressed soon
- **High Priority (7-8)**: Critical issues requiring prompt attention
- **Critical Priority (9-10)**: Urgent issues that need immediate resolution

### 2. Executive Summary

The enhanced report includes an executive summary section at the top that provides a quick overview of the most critical information with clear explanations:

```
EXECUTIVE SUMMARY
----------------
Business Impact: 61 of 67 tickets (91.0%) affect business operations
These tickets indicate system downtime, revenue impact, missed deadlines, or contract risks
High Priority Items: 59 tickets (88.1%) are high priority (scores 7-10)
Urgency Alert: 57 tickets (85.1%) require prompt resolution (Levels 4-5)
Customer Satisfaction Risk: 32 customers (47.8%) are highly frustrated (Levels 4-5)
```

### 3. Improved Data Organization

The enhanced report reorganizes information to present the most critical data first:

1. Executive Summary
2. Business Impact Section with Clear Criteria
3. Priority Score Distribution
4. Urgency and Frustration Levels
5. Detailed Ticket List (organized by priority)

### 4. Intuitive Priority Scoring

The enhanced report includes a clear explanation of the priority scoring system:

```
PRIORITY SCORING SYSTEM
----------------------
Our system scores tickets from 1-10 based on urgency, frustration, business impact and technical expertise:

10 = Critical Emergency (Immediate action required, major business impact)
8-9 = High Priority (Requires attention within 24 hours, significant impact)
6-7 = Medium-High Priority (Address within 48 hours)
4-5 = Medium Priority (Address within this week)
1-3 = Low Priority (Address when resources permit)
```

### 5. Top Components Analysis

The enhanced report highlights the top affected components:

```
TOP AFFECTED COMPONENTS
---------------------
gpu: 23 tickets (34.3%)
memory: 15 tickets (22.4%)
cpu: 12 tickets (17.9%)
motherboard: 8 tickets (11.9%)
network: 5 tickets (7.5%)
```

This section provides a quick overview of which hardware components are causing the most support issues, helping teams identify patterns and potential systematic problems.

### 6. Business Impact Tickets

The enhanced report clearly identifies business impact tickets with explanations:

```
BUSINESS IMPACT TICKETS
----------------------
These tickets have critical business impact that may affect production systems, revenue, or deadlines:

#27147 - RMA Request for ZD26946 - 4622111082
  Impact: System down, potential production impact
#26860 - RMA33756-C | RMA Request for ZD26455 - 4622117819
  Impact: System crashes and GPU failure are impacting productivity and could lead to potential revenue loss if not resolved quickly
```

### 7. Enhanced High Priority Tickets Display

The latest version shows up to 10 high-priority tickets with detailed information:

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
```

## Benefits

The enhanced reporting provides several benefits:

1. **Faster Comprehension**: Team members can quickly understand the meaning of numerical scores
2. **Better Prioritization**: The executive summary and reorganized data help focus on the most critical issues
3. **Actionable Insights**: Percentage values and contextual information help identify trends
4. **Improved Communication**: Descriptive labels make it easier to discuss findings with non-technical stakeholders
5. **Hardware Trend Analysis**: The component breakdown helps identify recurring hardware issues
6. **Comprehensive High Priority View**: With up to 10 high-priority tickets displayed, nothing critical is missed

## Implementation Details

The enhanced reporting feature is implemented using Clean Architecture principles. Within the `src/presentation/reporters` directory, the sentiment reporter supports enhanced formatting via the `enhanced` parameter.

When generating a report, you can either:
1. Specify `--type enhanced-sentiment` as the report type
2. Use `--type sentiment --enhanced` to enable enhanced formatting

The implementation provides:
- Component analysis to track hardware trends
- Extended high-priority ticket display (10 tickets instead of 5)
- Better formatting of percentage values and metrics
- Descriptive labels for numerical values
- Executive summary with actionable insights

## Multi-View Enhanced Reports

Enhanced reporting also works with multi-view reports, allowing you to compare sentiment metrics across different support queues with the same improved formatting and clarity:

```bash
python -m src.main report --type multi-view --view-ids 12345,67890 --enhanced
```

This provides comparative insights across different support queues with the enhanced formatting.