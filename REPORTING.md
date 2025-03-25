# Zendesk AI Integration Reporting Guide

This guide explains how to use the reporting features of the Zendesk AI Integration application to gain insights into your support tickets.

## Overview

The reporting functionality allows you to:

1. Generate comprehensive reports from any Zendesk view
2. See ticket status, priority, and age distributions
3. Get hardware component analysis from ticket content
4. View detailed information about each ticket
5. Save reports to text files for sharing or archiving

## Available Reports

### View-Based Reports

The most powerful reporting feature is the ability to generate reports based on any Zendesk view.

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support"
```

This command will:
- Find the named view in your Zendesk instance
- Fetch all tickets from that view
- Generate a comprehensive report
- Save the report to a text file

The report includes:
- Total ticket count
- Status distribution
- Priority distribution
- Hardware component distribution
- Customer distribution
- Ticket age analysis
- Detailed listing of all tickets with their metadata

### Hardware Component Reports

For hardware-specific analysis, you can use the component report mode:

```bash
python src/zendesk_ai_app.py --mode run --view 15990417987223 --component-report
```

This specialized report focuses on hardware components mentioned in tickets and provides deeper analysis of hardware-related issues.

### Finding Available Views

To see all available Zendesk views that you can report on:

```bash
python src/zendesk_ai_app.py --mode list-views
```

This displays a list of all views with their IDs and names.

## Limiting Report Size

If you want to limit the number of tickets in a report:

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support" --limit 10
```

By default, reports include all tickets in the view.

## Report Output

Reports are:
1. Displayed in the console
2. Saved to a text file in the current directory (named with a timestamp)

To specify a custom output file:

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support" --output my_report.txt
```

## Component Detection

The application automatically detects hardware components mentioned in tickets by:
1. Checking for component-specific tags
2. Analyzing ticket subject lines for component keywords

Detected components include:
- GPU
- CPU
- Drive/Storage
- Memory/RAM
- Power Supply
- Motherboard
- Cooling
- Display
- Network
- BIOS
- IPMI/BMC

## Examples

### Daily Support Queue Report

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "Support :: Pending Support"
```

### Weekly Hardware Issues Report

```bash
python src/zendesk_ai_app.py --mode run --view 15990417987223 --component-report --output weekly_hardware_report.txt
```

### Open RMA Tickets Report

```bash
python src/zendesk_ai_app.py --mode pending --pending-view "RMA :: Pending RTV Approval"
```

## Troubleshooting

### View Not Found

If you receive "View not found" error:
- Use `--mode list-views` to see all available views
- Check for exact spelling and capitalization of view names

### Empty Reports

If your report shows no tickets:
- Verify the view contains tickets in Zendesk
- Check your Zendesk API credentials
- Ensure your API token has sufficient permissions

### Component Detection Issues

If components aren't being detected properly:
- Review your ticket tagging process
- Consider adding more component keywords in the `generate_pending_support_report` function
- Make sure ticket subjects use standardized component nomenclature