# Sentiment Analysis Features

This document describes the sentiment analysis capabilities in the Zendesk AI Integration.

## Overview

The enhanced sentiment analysis engine provides a multidimensional analysis of customer tickets, going beyond basic positive/negative classification to provide actionable insights without modifying tickets.

## Key Sentiment Dimensions

### Polarity
Traditional sentiment classification:
- **Positive**: Customer is satisfied or expressing positive emotions
- **Negative**: Customer is dissatisfied or expressing negative emotions
- **Neutral**: Customer is neither clearly positive nor negative
- **Unknown**: Unable to determine sentiment

### Urgency Level (1-5 scale)
How time-sensitive the ticket appears to be:
- **1**: No urgency, routine inquiry
- **2**: Mild urgency, would like a response soon
- **3**: Moderate urgency, needs attention this week
- **4**: High urgency, needs prompt attention
- **5**: Critical emergency, needs immediate attention

### Frustration Level (1-5 scale)
How frustrated the customer appears to be:
- **1**: No frustration, neutral tone
- **2**: Mild frustration, slight annoyance
- **3**: Moderate frustration, clear dissatisfaction
- **4**: High frustration, significantly upset
- **5**: Extreme frustration, angry or very upset

### Technical Expertise (1-5 scale)
The customer's apparent technical knowledge level:
- **1**: Basic user, limited technical knowledge
- **2**: Some technical knowledge
- **3**: Moderate technical understanding
- **4**: Advanced technical skills
- **5**: Expert with detailed technical understanding

### Business Impact
Whether the issue affects the customer's business operations:
- **Detected**: Yes/No
- **Description**: Brief explanation of the business impact

### Priority Score (1-10 scale)
Automatically calculated based on:
- Urgency level (35% weight)
- Frustration level (30% weight)
- Business impact (25% weight)
- Technical expertise (10% weight, inverse relationship)

## Running Sentiment Analysis

### Analyze Tickets Without Modifying Them

```bash
python src/zendesk_ai_app.py --mode run --status open
```

This analyzes open tickets, stores the analysis in MongoDB, but does not make any changes to the tickets.

### Generate a Sentiment Report from Database

```bash
python src/zendesk_ai_app.py --mode sentiment --days 7
```

This generates a comprehensive sentiment report based on analyses stored in the database from the last 7 days.

### Analyze a Specific View

```bash
python src/zendesk_ai_app.py --mode sentiment --view "Support :: Pending Support"
```

This analyzes tickets in the specified view and generates a sentiment report.

### Save Report to File

```bash
python src/zendesk_ai_app.py --mode sentiment --days 30 --output "monthly_sentiment.txt"
```

This analyzes data from the last 30 days and saves the report to the specified file.

## Report Contents

A typical sentiment analysis report includes:

1. **Overview**: Total tickets analyzed
2. **Sentiment Distribution**: Count of positive, negative, neutral, and unknown sentiments
3. **Urgency Distribution**: Count of tickets at each urgency level (1-5)
4. **Frustration Distribution**: Count of tickets at each frustration level (1-5)
5. **Business Impact**: Count and percentage of tickets with business impact
6. **Priority Score Distribution**: Count of tickets at each priority level (1-10)
7. **Averages**: Average urgency, frustration, and priority scores
8. **Category Distribution**: Count of tickets in each category
9. **Component Distribution**: Count of tickets for each hardware component
10. **High Priority Tickets**: List of tickets with priority score above threshold
11. **Business Impact Tickets**: List of tickets with business impact detected

## Using Reports for Decision Making

The sentiment reports can help support teams:

1. **Prioritize Resources**: Focus on high priority tickets first
2. **Identify Trends**: Track sentiment changes over time
3. **Detect Pain Points**: Identify common issues causing frustration
4. **Allocate Staff**: Assign technically complex issues to more experienced staff
5. **Measure Impact**: See how support initiatives affect sentiment metrics

## Technical Implementation

The sentiment analysis system consists of:

1. **Enhanced Sentiment Analysis**: Provided by `enhanced_sentiment.py` and `claude_enhanced_sentiment.py`
   - Uses OpenAI's GPT-4o model or Claude's models with temperature=0.3 for consistent responses
   - Includes concrete examples for each sentiment dimension
   - Provides detailed prompting for accurate classification
   - Handles various JSON response formats (direct JSON or code blocks)
2. **Database Storage**: All analyses are stored in MongoDB
3. **Reporting Engine**: `sentiment_report.py` generates detailed reports
4. **CLI Interface**: `--mode sentiment` command provides various reporting options

### JSON Response Handling

Both OpenAI and Claude may return responses in different formats:

1. Direct JSON objects
2. JSON wrapped in markdown code blocks (```json...```)
3. Text with embedded JSON

The system handles all these cases automatically, extracting valid JSON from any format.

### Confidence Value Handling

Confidence values may be returned as either numeric values (0.0-1.0) or text descriptions:

- "high" → 0.9
- "medium" → 0.7
- "low" → 0.5
- "very high" → 1.0
- "very low" → 0.3

These are normalized internally to ensure consistent scoring.

For more details on the JSON parsing enhancements, see [JSON_PARSING.md](JSON_PARSING.md).

## Extending the System

To add new sentiment metrics:

1. Modify `enhanced_sentiment.py` to extract additional dimensions
2. Update the database schema (no changes needed for MongoDB)
3. Enhance `sentiment_report.py` to include the new metrics in reports
4. Update this documentation to explain the new metrics

## Troubleshooting

### No Data in Reports

If reports show no data:
1. Ensure tickets have been analyzed with `--mode run` first
2. Check MongoDB connection settings
3. Verify the date range with `--days` parameter
4. Try running with a specific view using `--view`

### Low Quality Analysis

If sentiment analysis seems inaccurate:
1. Ensure using enhanced sentiment (`--basic-sentiment` is NOT used)
2. Check that ticket content has sufficient information
3. Verify your OpenAI API key has access to the GPT-4o model
4. Try the reanalysis mode to reprocess tickets with updated settings:

```bash
python src/zendesk_ai_app.py --mode run --reanalyze --days 7
```

This will reprocess all tickets from the last 7 days with the improved sentiment analysis.
