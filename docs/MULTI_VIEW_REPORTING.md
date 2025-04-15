# Multi-View Reporting

This document explains the Multi-View Reporting functionality that allows you to generate reports across multiple Zendesk views simultaneously with a clear understanding of view contents.

## Overview

The Multi-View Reporting feature provides an improved interface for selecting multiple Zendesk views and generating comprehensive reports that analyze tickets across these views. It addresses several limitations in the previous implementation:

1. It allows selecting multiple views in a single operation
2. It provides detailed information about ticket counts and statuses within each view
3. It offers a more intuitive selection interface
4. It generates comprehensive reports that compare metrics across views

## Key Features

### 1. Detailed View Status Information

Views are displayed with detailed status information:

- **[Empty]**: View has no tickets
- **[5 tickets]**: View has 5 tickets in total
- **[10 total, 3 pending]**: View has 10 tickets, 3 of which are pending

This gives you immediate insight into view contents before attempting operations.

### 2. Multiple View Selection

The interface allows you to:

- Select individual views by number
- Select ranges of views (e.g., "5-8")
- Select multiple specific views (e.g., "1,3,7")
- Select all views at once with the 'all' command
- Clear your selection with the 'clear' command

### 3. Categorized View Display

Views are organized by category based on their naming conventions. For example, views named "Support :: Pending" and "Support :: Open" will be grouped under the "Support" category, making it easier to find related views.

### 4. Comprehensive Cross-View Reports

Reports generated with multiple views selected will include:

- **Overview statistics** for all selected views combined
- **Per-view breakdowns** showing metrics for each individual view
- **Comparison data** highlighting differences between views

## How to Use

### Running the Multi-View Report Generator

1. Run the multi-view reports script:
   ```
   multi_view_reports.bat
   ```

2. Select the type of report you want to generate:
   ```
   Please select a report type:
   1. Pending Report
   2. Basic Sentiment Analysis
   3. Enhanced Sentiment Analysis
   ```

3. The view selector will display all available views with their status:
   ```
   ==========================================
   Select views for Pending Report
   ==========================================
   Select multiple views using numbers (e.g. 1,3,5-7)
   Enter 'all' to select all views
   Enter 'clear' to clear selection
   Enter 'done' when finished selecting
   --------------------------------------------------

   Support:
     1. Support :: Escalated Tickets [5 tickets]
     2. Support :: Escalated to Support [3 tickets]
     3. Support :: On Customer Hold [7 tickets]
     4. Support :: Pending Customer [4 tickets]
     5. Support :: Pending RMA [Empty]
     6. Support :: Pending Support [2 tickets]
     7. Support :: RMA Pending Response to Customer [1 tickets]

   Uncategorized:
     8. Scrub Queue [3 tickets]
     9. Tickets Over 7 Days [Empty]
    10. Tickets Requiring Update [Empty]

   Current selection: None
   ```

4. Select the views you want to include:
   ```
   Select views (or 'done'): 1,4,8
   Current selection: Support :: Escalated Tickets, Support :: Pending Customer, Scrub Queue
   ```

5. When you're done selecting views, enter 'done':
   ```
   Select views (or 'done'): done
   ```

6. The system will generate the report across all selected views:
   ```
   Generating pending report for 3 views:
   - Support :: Escalated Tickets
   - Support :: Pending Customer
   - Scrub Queue

   Fetching tickets for multiple views... This may take a while.

   =============================================================
   MULTI-VIEW ANALYSIS REPORT (2025-04-04 08:30)
   =============================================================

   Multi-View Pending Analysis Report
   ---------------------------------

   OVERVIEW
   --------
   Total Tickets Analyzed: 12
   Total Views: 3

   TICKETS BY VIEW
   --------------
   Support :: Escalated Tickets: 5 tickets
   Support :: Pending Customer: 4 tickets
   Scrub Queue: 3 tickets

   ... [detailed report content] ...

   Report saved to: multi_view_pending_report_20250404_0830.txt
   ```

### Command-Line Usage

You can also specify the report type directly from the command line:

```bash
multi_view_reports.bat --mode pending
multi_view_reports.bat --mode sentiment
multi_view_reports.bat --mode enhanced
```

## Report Types

### 1. Pending Report

The pending report shows tickets that are in pending status across all selected views:

- Tickets waiting for customer response
- Tickets pending internal actions
- Tickets pending RMA processing

### 2. Basic Sentiment Analysis

The basic sentiment report provides sentiment analysis across all selected views:

- Sentiment distribution (positive, negative, neutral)
- Overall sentiment metrics
- Per-view sentiment breakdown

### 3. Enhanced Sentiment Analysis

The enhanced sentiment report provides detailed sentiment metrics across all selected views:

- Sentiment polarity (positive, negative, neutral)
- Urgency levels (1-5 scale)
- Frustration levels (1-5 scale)
- Business impact assessment
- Priority scoring (1-10 scale)
- Key phrases and detected emotions

## Advantages Over Previous Implementation

The Multi-View Reporting feature offers several advantages over the previous implementation:

1. **Better Visibility**: Detailed status information shows exactly what's in each view before you select it
2. **Time Savings**: No more wasted time attempting to generate reports for empty views
3. **More Comprehensive Reports**: Compare metrics across multiple views in a single report
4. **Easier Selection**: Intuitive interface for selecting multiple views
5. **Categorized Organization**: Views grouped by category for easier navigation

## Technical Implementation

The Multi-View Reporting feature consists of these components:

1. **MultiViewSelector**: Core class that provides view selection and status checking
2. **multi_view_reports.py**: Main script that ties everything together
3. **multi_view_reports.bat**: Convenience launcher for Windows

The implementation leverages the existing reporting modules but enhances them with:

- More detailed status checking
- Multiple view selection capabilities
- Combined report generation

## Troubleshooting

### No Views Displayed

If no views are displayed, make sure:
- Your Zendesk credentials are correctly configured in the .env file
- You have permission to access views in your Zendesk account
- The Zendesk API is not experiencing connectivity issues

### Empty Reports

If you receive an empty report:
- Ensure that the selected views contain tickets matching the report criteria
- For pending reports, ensure the views contain tickets in pending status
- For sentiment reports, ensure the views contain tickets that have been analyzed

### Error Messages

Common error messages and their solutions:

- **"AI Analyzer not available"**: Make sure your AI API keys are configured correctly in .env
- **"Report modules not available"**: Make sure the required report modules are in the correct directory
- **"No tickets found in selected views"**: The selected views don't contain any tickets

## Next Steps

Planned enhancements for the Multi-View Reporting feature:

1. **Saved Selections**: Save and load view selections for frequent use
2. **Report Scheduling**: Schedule regular multi-view reports
3. **Report Comparison**: Compare reports over time to identify trends
4. **Custom Report Types**: Create customized report types with selected metrics
