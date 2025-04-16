"""
Zendesk Report Generator Module

This module provides functionality to generate summary reports from Zendesk tickets,
including AI-powered analysis of ticket categories, sentiment, and priority.
"""

import logging
from datetime import datetime, timedelta
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

def generate_summary_report(zendesk_client, ai_analyzer, view_id=None, days=30, include_sentiment=True):
    """
    Generate a summary report for tickets from a specific view and time period.
    
    Args:
        zendesk_client: An instance of ZendeskClient for fetching tickets
        ai_analyzer: An instance of AI analyzer for ticket analysis
        view_id: The ID of the view to fetch tickets from (or None for all tickets)
        days: Number of days to look back for tickets
        include_sentiment: Whether to include sentiment analysis in the report
    
    Returns:
        A dictionary containing the report data
    """
    # Initialize report structure
    report = {
        "timestamp": datetime.now().isoformat(),
        "view_name": "All Tickets",
        "ticket_count": 0,
        "categories": defaultdict(int),
        "priorities": {
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "sentiment_summary": {
            "positive": 0,
            "neutral": 0, 
            "negative": 0
        },
        "urgency_levels": {
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "average_priority_score": 0,
    }
    
    # Get view name if a view ID was provided
    if view_id:
        try:
            view = zendesk_client.get_view_by_id(view_id)
            if view:
                report["view_name"] = view.title
            else:
                logger.warning(f"View with ID {view_id} not found")
        except Exception as e:
            logger.error(f"Error fetching view name for ID {view_id}: {str(e)}")
    
    # Calculate the start date for ticket filtering
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch tickets from the specified view or all tickets
    tickets = []
    if view_id:
        tickets = zendesk_client.fetch_tickets_from_view(view_id)
    else:
        tickets = zendesk_client.fetch_tickets(status="all")
    
    # Filter tickets by date if needed
    if days > 0:
        tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
    
    # Update ticket count
    report["ticket_count"] = len(tickets)
    
    if not tickets:
        logger.warning("No tickets found for report generation")
        return report
    
    # Process tickets in batches for efficiency
    analyses = ai_analyzer.analyze_tickets_batch(tickets)
    
    # Compile statistics from analyses
    priority_scores = []
    for ticket_id, analysis in analyses.items():
        # Track categories
        category = analysis.get("category", "uncategorized")
        report["categories"][category] += 1
        
        # Track priorities
        priority_score = analysis.get("priority_score", 0)
        priority_scores.append(priority_score)
        
        if priority_score >= 7:
            report["priorities"]["high"] += 1
        elif priority_score >= 4:
            report["priorities"]["medium"] += 1
        else:
            report["priorities"]["low"] += 1
        
        # Track sentiment if included
        if include_sentiment and "sentiment" in analysis:
            sentiment = analysis["sentiment"]
            polarity = sentiment.get("polarity", "neutral")
            urgency = sentiment.get("urgency_level", "medium")
            
            report["sentiment_summary"][polarity] += 1
            report["urgency_levels"][urgency] += 1
    
    # Calculate average priority score
    if priority_scores:
        report["average_priority_score"] = sum(priority_scores) / len(priority_scores)
    
    # Convert defaultdict to regular dict for categories
    report["categories"] = dict(report["categories"])
    
    # Add top category
    if report["categories"]:
        top_category = max(report["categories"].items(), key=lambda x: x[1])
        report["top_category"] = top_category[0]
    else:
        report["top_category"] = "none"
    
    logger.info(f"Generated report for {report['view_name']} with {report['ticket_count']} tickets")
    return report


def generate_ticket_breakdown_report(zendesk_client, ai_analyzer, days=30, group_by="category"):
    """
    Generate a breakdown report of tickets grouped by a specific attribute.
    
    Args:
        zendesk_client: An instance of ZendeskClient for fetching tickets
        ai_analyzer: An instance of AI analyzer for ticket analysis
        days: Number of days to look back for tickets
        group_by: The attribute to group tickets by (category, priority, sentiment)
    
    Returns:
        A dictionary containing the breakdown report data
    """
    # Calculate the start date for ticket filtering
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch all tickets within the time period
    tickets = zendesk_client.fetch_tickets(status="all")
    tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
    
    # Process tickets with AI analyzer
    analyses = ai_analyzer.analyze_tickets_batch(tickets)
    
    # Group tickets based on the specified attribute
    groups = defaultdict(list)
    
    for ticket_id, analysis in analyses.items():
        if group_by == "category":
            group_key = analysis.get("category", "uncategorized")
        elif group_by == "priority":
            priority_score = analysis.get("priority_score", 0)
            if priority_score >= 7:
                group_key = "high"
            elif priority_score >= 4:
                group_key = "medium"
            else:
                group_key = "low"
        elif group_by == "sentiment":
            sentiment = analysis.get("sentiment", {})
            group_key = sentiment.get("polarity", "neutral")
        else:
            group_key = "unknown"
        
        # Add the ticket ID to the appropriate group
        groups[group_key].append(ticket_id)
    
    # Create the report structure
    report = {
        "timestamp": datetime.now().isoformat(),
        "days": days,
        "group_by": group_by,
        "total_tickets": len(tickets),
        "groups": {}
    }
    
    # Add group data to the report
    for group_key, ticket_ids in groups.items():
        report["groups"][group_key] = {
            "count": len(ticket_ids),
            "percentage": (len(ticket_ids) / len(tickets)) * 100 if tickets else 0,
            "ticket_ids": ticket_ids
        }
    
    logger.info(f"Generated breakdown report by {group_by} with {len(tickets)} tickets")
    return report


def generate_trend_report(zendesk_client, ai_analyzer, days=30, interval="day"):
    """
    Generate a trend report showing how ticket metrics change over time.
    
    Args:
        zendesk_client: An instance of ZendeskClient for fetching tickets
        ai_analyzer: An instance of AI analyzer for ticket analysis
        days: Number of days to include in the report
        interval: Time interval for grouping (day, week, month)
    
    Returns:
        A dictionary containing the trend report data
    """
    # Calculate the start date for ticket filtering
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch all tickets within the time period
    tickets = zendesk_client.fetch_tickets(status="all")
    
    # Filter tickets by date
    filtered_tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
    
    # Process tickets with AI analyzer
    analyses = ai_analyzer.analyze_tickets_batch(filtered_tickets)
    
    # Group tickets by time interval
    time_groups = defaultdict(list)
    
    for ticket in filtered_tickets:
        created_at = getattr(ticket, 'created_at', datetime.now())
        
        if interval == "day":
            # Group by day
            group_key = created_at.strftime("%Y-%m-%d")
        elif interval == "week":
            # Group by ISO week
            group_key = f"{created_at.isocalendar()[0]}-W{created_at.isocalendar()[1]}"
        elif interval == "month":
            # Group by month
            group_key = created_at.strftime("%Y-%m")
        else:
            # Default to day
            group_key = created_at.strftime("%Y-%m-%d")
        
        time_groups[group_key].append(ticket.id)
    
    # Create the report structure
    report = {
        "timestamp": datetime.now().isoformat(),
        "days": days,
        "interval": interval,
        "total_tickets": len(filtered_tickets),
        "time_periods": []
    }
    
    # Generate metrics for each time period
    for period, ticket_ids in sorted(time_groups.items()):
        period_analyses = {tid: analyses.get(tid, {}) for tid in ticket_ids if tid in analyses}
        
        # Calculate metrics for this period
        categories = Counter()
        sentiment_counts = Counter()
        priority_scores = []
        
        for analysis in period_analyses.values():
            categories[analysis.get("category", "uncategorized")] += 1
            
            sentiment = analysis.get("sentiment", {})
            sentiment_counts[sentiment.get("polarity", "neutral")] += 1
            
            priority_score = analysis.get("priority_score", 0)
            priority_scores.append(priority_score)
        
        # Calculate top category
        top_category = categories.most_common(1)[0][0] if categories else "none"
        
        # Calculate average priority
        avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 0
        
        # Add period data to the report
        period_data = {
            "period": period,
            "ticket_count": len(ticket_ids),
            "top_category": top_category,
            "sentiment": {
                "positive": sentiment_counts["positive"],
                "neutral": sentiment_counts["neutral"],
                "negative": sentiment_counts["negative"]
            },
            "average_priority": avg_priority
        }
        
        report["time_periods"].append(period_data)
    
    logger.info(f"Generated trend report over {days} days with {interval} interval")
    return report
