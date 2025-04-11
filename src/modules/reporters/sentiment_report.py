"""
Sentiment Reporter Module

This module provides functionality to generate reports about ticket sentiment.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from .base_reporter import BaseReporter

logger = logging.getLogger(__name__)

class SentimentReporter(BaseReporter):
    """Reporter class for sentiment analysis reports."""
    
    def __init__(self):
        """Initialize the sentiment reporter."""
        super().__init__()
        self.report_name = "Sentiment Analysis Report"
    
    def generate_report(self, analyses=None, zendesk_client=None, ai_analyzer=None, db_repository=None, 
                       days=None, view=None, title=None, verbose=False):
        """
        Generate a sentiment analysis report for tickets.
        
        Args:
            analyses: Optional pre-analyzed data (if provided, other params not needed)
            zendesk_client: Zendesk client for fetching tickets
            ai_analyzer: AI analyzer for processing tickets
            db_repository: Database repository
            days: Number of days to look back
            view: Optional view ID to fetch tickets from
            title: Optional report title
            verbose: Whether to include detailed information
            
        Returns:
            Report content as a string
        """
        # If we have pre-analyzed data, use that
        if analyses is not None:
            return self._generate_report_from_analyses(analyses, title)
            
        # Otherwise, we need to fetch and analyze data
        if not zendesk_client or not ai_analyzer:
            return "Error: ZendeskClient and AIAnalyzer are required when analyses are not provided."
        
        # Calculate the time period for the report
        start_date, time_period = self._calculate_time_period(
            days=days if days is not None else 30, 
            view=view, 
            zendesk_client=zendesk_client
        )
        
        # Fetch tickets
        tickets = []
        if view:
            view_name = self._lookup_view_name(view, zendesk_client)
            logger.info(f"Fetching tickets from view: {view_name}")
            tickets = zendesk_client.fetch_tickets_from_view(view)
        else:
            logger.info("Fetching all tickets")
            tickets = zendesk_client.fetch_tickets(status="all")
        
        # Filter by date
        tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
        
        if not tickets:
            return f"No tickets found for {time_period}"
        
        # Analyze tickets
        analyses = ai_analyzer.analyze_tickets_batch(tickets)
        
        # Generate the report using the analyses
        report_title = title or f"Sentiment Analysis Report for {time_period}"
        return self._generate_report_from_analyses(analyses, report_title)
    
    def _generate_report_from_analyses(self, analyses, title=None):
        """Generate a report from pre-analyzed data."""
        # Convert analyses to a list if it's a dictionary
        if isinstance(analyses, dict):
            analyses_list = list(analyses.values())
        else:
            analyses_list = analyses
        
        # Compile sentiment statistics
        sentiment_counts = Counter()
        urgency_counts = Counter()
        priority_scores = []
        categories = Counter()
        
        for analysis in analyses_list:
            # Extract sentiment
            sentiment = analysis.get("sentiment", {})
            
            # Handle different sentiment formats
            if isinstance(sentiment, dict):
                polarity = sentiment.get("polarity", "neutral")
                urgency = sentiment.get("urgency_level", "medium")
            else:
                polarity = sentiment or "neutral"
                urgency = "medium"
            
            # Track sentiment
            sentiment_counts[polarity] += 1
            urgency_counts[urgency] += 1
            
            # Track priority
            priority_score = analysis.get("priority_score", 0)
            priority_scores.append(priority_score)
            
            # Track categories
            category = analysis.get("category", "uncategorized")
            categories[category] += 1
        
        # Calculate average priority
        avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 0
        
        # Build the report
        report = [
            self._create_report_header(),
            title or "Sentiment Analysis Report",
            f"Total tickets analyzed: {len(analyses_list)}",
            "",
            "Sentiment Overview:"
        ]
        
        # Add sentiment counts
        for polarity in ["positive", "neutral", "negative"]:
            count = sentiment_counts[polarity]
            percentage = (count / len(analyses_list)) * 100 if len(analyses_list) > 0 else 0
            report.append(f"  {polarity.capitalize()}: {count} ({percentage:.1f}%)")
        
        report.append("")
        report.append("Urgency Levels:")
        
        # Add urgency counts for high, medium, low
        for urgency_name, level in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            count = urgency_counts[level]
            percentage = (count / len(analyses_list)) * 100 if len(analyses_list) > 0 else 0
            report.append(f"  {urgency_name}: {count} ({percentage:.1f}%)")
        
        report.append("")
        report.append(f"Average Priority Score: {avg_priority:.1f}/10")
        report.append("")
        report.append("Top Categories:")
        
        # Add category breakdown
        for category, count in categories.most_common(5):
            percentage = (count / len(analyses_list)) * 100 if len(analyses_list) > 0 else 0
            report.append(f"  {category}: {count} ({percentage:.1f}%)")
        
        report.append("")
        report.append(self._create_report_footer())
        
        return "\n".join(report)
    
    def generate_trend_report(self, zendesk_client, ai_analyzer, days: int = 90, 
                             interval: str = "week") -> str:
        """
        Generate a sentiment trend report for tickets over time.
        
        Args:
            zendesk_client: Zendesk client for fetching tickets
            ai_analyzer: AI analyzer for processing tickets
            days: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            
        Returns:
            Report content as a string
        """
        # Calculate the time period
        start_date = datetime.now() - timedelta(days=days)
        
        # Fetch tickets
        tickets = zendesk_client.fetch_tickets(status="all")
        
        # Filter by date
        tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
        
        if not tickets:
            return f"No tickets found for the last {days} days"
        
        # Analyze tickets
        analyses = ai_analyzer.analyze_tickets_batch(tickets)
        
        # Group tickets by time interval
        time_groups = defaultdict(list)
        
        for ticket in tickets:
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
                # Default to week
                group_key = f"{created_at.isocalendar()[0]}-W{created_at.isocalendar()[1]}"
                
            time_groups[group_key].append(ticket.id)
        
        # Build the report
        report = [
            self._create_report_header(),
            f"Sentiment Trend Report for the last {days} days",
            f"Grouped by: {interval}",
            f"Total tickets analyzed: {len(tickets)}",
            "",
            f"{'Period':<12} | {'Count':<6} | {'Positive':<9} | {'Neutral':<9} | {'Negative':<9} | {'Avg Priority':<12}",
            f"{'-'*12} | {'-'*6} | {'-'*9} | {'-'*9} | {'-'*9} | {'-'*12}"
        ]
        
        # Process each time period
        for period, ticket_ids in sorted(time_groups.items()):
            # Get analyses for this period's tickets
            period_analyses = {tid: analyses.get(tid, {}) for tid in ticket_ids if tid in analyses}
            
            # Count sentiments
            sentiment_counts = Counter()
            priority_scores = []
            
            for analysis in period_analyses.values():
                sentiment = analysis.get("sentiment", {})
                sentiment_counts[sentiment.get("polarity", "neutral")] += 1
                
                priority_score = analysis.get("priority_score", 0)
                priority_scores.append(priority_score)
            
            # Calculate metrics
            total = len(period_analyses)
            if total == 0:
                continue
                
            pos_pct = sentiment_counts["positive"] / total if total > 0 else 0
            neu_pct = sentiment_counts["neutral"] / total if total > 0 else 0
            neg_pct = sentiment_counts["negative"] / total if total > 0 else 0
            
            avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 0
            
            # Add to report
            report.append(
                f"{period:<12} | {total:<6} | {self._format_percentage(pos_pct):<9} | "
                f"{self._format_percentage(neu_pct):<9} | {self._format_percentage(neg_pct):<9} | "
                f"{avg_priority:.1f}/10"
            )
        
        report.append("")
        report.append(self._create_report_footer())
        
        return "\n".join(report)
        
    # Additional methods for the enhanced reporters to use
    def _count_sentiment_polarities(self, analyses):
        """Count sentiment polarities in analyses."""
        polarity_counts = {}
        
        for analysis in analyses:
            if 'sentiment' in analysis:
                if isinstance(analysis['sentiment'], dict):
                    # Enhanced sentiment
                    polarity = analysis['sentiment'].get('polarity', 'unknown')
                else:
                    # Basic sentiment
                    polarity = analysis['sentiment'] or 'unknown'
                    
                # Initialize if this polarity is not already counted
                if polarity not in polarity_counts:
                    polarity_counts[polarity] = 0
                    
                # Increment the count for this polarity
                polarity_counts[polarity] += 1
        
        return polarity_counts
        
    def _calculate_average_urgency(self, analyses):
        """Calculate average urgency level."""
        urgency_levels = []
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                urgency = analysis['sentiment'].get('urgency_level')
                if urgency is not None:
                    urgency_levels.append(urgency)
        
        if urgency_levels:
            return sum(urgency_levels) / len(urgency_levels)
        return 0
    
    def _calculate_average_frustration(self, analyses):
        """Calculate average frustration level."""
        frustration_levels = []
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                frustration = analysis['sentiment'].get('frustration_level')
                if frustration is not None:
                    frustration_levels.append(frustration)
        
        if frustration_levels:
            return sum(frustration_levels) / len(frustration_levels)
        return 0
    
    def _calculate_average_priority(self, analyses):
        """Calculate average priority score."""
        priority_scores = []
        
        for analysis in analyses:
            priority = analysis.get('priority_score')
            if priority is not None:
                priority_scores.append(priority)
        
        if priority_scores:
            return sum(priority_scores) / len(priority_scores)
        return 0
    
    def _count_business_impact(self, analyses):
        """Count analyses with business impact."""
        count = 0
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                business_impact = analysis['sentiment'].get('business_impact', {})
                if business_impact and business_impact.get('detected', False):
                    count += 1
        
        return count
