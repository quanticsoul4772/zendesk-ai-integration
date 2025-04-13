# Reporting Features

This document describes the reporting features available in the Zendesk AI Integration.

## Available Reports

### Sentiment Analysis Report

Generate a detailed sentiment analysis report:

```bash
python -m src.main generatereport --type sentiment --days 7
```

This report provides comprehensive sentiment analytics:
- Distribution of sentiment polarity (positive, negative, neutral)
- Urgency level distribution (1-5 scale)
- Frustration level distribution (1-5 scale)
- Business impact analysis
- Priority score distribution
- Average metrics
- High-priority ticket identification

You can generate reports for different time periods:
```bash
python -m src.main generatereport --type sentiment --days 1   # Last 24 hours
python -m src.main generatereport --type sentiment --days 7   # Last week
python -m src.main generatereport --type sentiment --days 30  # Last month
```

Or focus on specific views:
```bash
python -m src.main generatereport --type sentiment --view-name "Support Queue"
python -m src.main generatereport --type sentiment --view-id 12345
```

### Enhanced Sentiment Analysis Report

Generate a more detailed and intuitive sentiment report with descriptive labels:

```bash
python -m src.main generatereport --type enhanced-sentiment --days 7
# OR
python -m src.main generatereport --type sentiment --enhanced --days 7
```

The enhanced report includes:
- Executive summary with key metrics
- Descriptive labels for numerical scales
- Business impact analysis with clear criteria
- Enhanced priority breakdown with meaningful descriptions
- Top components analysis
- Detailed high-priority ticket display

### Pending Support Report

Generate a detailed report of tickets in the Pending Support view:

```bash
python -m src.main generatereport --type pending --view-name "Support :: Pending Support"
```

This report includes:
- Total ticket count
- Status distribution
- Priority distribution
- Hardware component analysis
- Customer distribution
- Ticket age analysis
- Detailed information about each ticket

### Hardware Component Report

Generate a report focused on hardware component issues:

```bash
python -m src.main generatereport --type hardware --view-id 12345
```

This report analyzes tickets for hardware component mentions and provides:
- Component distribution
- Status breakdown
- Customer segment analysis
- Detailed listing of hardware-related tickets

### Multi-View Reports

Generate reports that compare data across multiple views:

```bash
python -m src.main generatereport --type multi-view --view-ids 12345,67890
# OR
python -m src.main generatereport --type multi-view --view-names "Support :: Pending,Support :: Open"
```

Multi-view reports provide:
- Comparative analysis across different support queues
- Overall sentiment distribution
- View-specific metrics
- Comparative performance indicators
- Trend analysis across different queues

## Understanding Sentiment Metrics

### Urgency Level (1-5 scale)
- **1**: No urgency, routine inquiry
- **2**: Mild urgency, would like a response soon
- **3**: Moderate urgency, needs attention this week
- **4**: High urgency, needs prompt attention
- **5**: Critical emergency, needs immediate attention

### Frustration Level (1-5 scale)
- **1**: No frustration, neutral tone
- **2**: Mild frustration, slight annoyance
- **3**: Moderate frustration, clear dissatisfaction
- **4**: High frustration, significantly upset
- **5**: Extreme frustration, angry or very upset

### Technical Expertise (1-5 scale)
- **1**: Basic user, limited technical knowledge
- **2**: Some technical knowledge
- **3**: Moderate technical understanding
- **4**: Advanced technical skills
- **5**: Expert with detailed technical understanding

### Business Impact
- **Detected**: Whether business operations are impacted
- **Description**: Brief explanation of the business impact

### Priority Score (1-10 scale)
Automatically calculated based on:
- Urgency level (35% weight)
- Frustration level (30% weight)
- Business impact (25% weight)
- Technical expertise (10% weight, inverse relationship)

### Interpretation

- **Priority Scores 8-10**: Critical issues needing immediate attention
- **Priority Scores 5-7**: Important issues with moderate urgency
- **Priority Scores 1-4**: Routine issues with normal priority

## Report Implementation

The reporting functionality is implemented using Clean Architecture principles:

### Reporter Components

Report generators are located in the `src/presentation/reporters` directory:

- `hardware_reporter.py` - Implements hardware component reports
- `pending_reporter.py` - Implements pending support reports
- `sentiment_reporter.py` - Implements sentiment analysis reports

Each reporter follows the Single Responsibility Principle and focuses on one type of report.

### Report Generation Process

1. The CLI command handler (`generate_report_command.py`) receives the request
2. It calls the appropriate use case for report generation
3. The use case utilizes the reporter implementation to generate the report
4. The command handler formats and displays or saves the report

### Customizing Reports

To customize existing reports:

1. Locate the appropriate reporter in `src/presentation/reporters/`
2. Modify the report generation method (e.g., `generate_report()`)
3. Update the formatting as needed

### Creating New Report Types

To add a new report type:

1. Create a new reporter in `src/presentation/reporters/` 
2. Implement the necessary interfaces
3. Update the generate_report_command.py file to handle the new report type
4. Add appropriate test coverage

## Finding Zendesk Views

To list all available Zendesk views:

```bash
python -m src.main views
```

This command displays all views with their IDs and names, allowing you to identify the correct view for reporting.

## Troubleshooting

### Dates Not Formatted Correctly

The application uses python-dateutil to parse dates from Zendesk. If your dates are not formatted correctly in reports, ensure:

1. python-dateutil is installed: `pip install -r requirements.txt`
2. Zendesk is returning date values (rather than null)

### Missing Sentiment Data

If enhanced sentiment data is missing from reports, check:

1. MongoDB connection is working
2. The API key for the AI model is correctly configured in your .env file
3. The tickets have been properly analyzed before generating the report

### View Not Found

If a view cannot be found, verify:

1. The exact name of the view from the `views` command
2. You've enclosed view names with spaces in quotes
3. You have permission to access the view in Zendesk

### Module Import Errors

If you encounter module import errors:

1. Make sure you're running the application from the project root directory
2. Check that your virtual environment is activated
3. Verify that all required packages are installed: `pip install -r requirements.txt`