"""
Unified Sentiment Reporter Module

This module provides functionality to generate reports about ticket sentiment
with support for both standard and enhanced reporting modes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from .unified_reporter_base import UnifiedReporterBase

logger = logging.getLogger(__name__)

class SentimentReporter(UnifiedReporterBase):
    """Reporter class for sentiment analysis reports with support for standard and enhanced modes."""
    
    def __init__(self, db_repository=None, enhanced_mode=True):
        """
        Initialize the sentiment reporter.
        
        Args:
            db_repository: Optional database repository for database queries
            enhanced_mode: Whether to use enhanced reporting format (default: True)
        """
        super().__init__()
        self.report_name = "Sentiment Analysis Report"
        self.db_repository = db_repository
        self.enhanced_mode = enhanced_mode
        
        # Define descriptive labels for various scales (used in enhanced mode)
        self.urgency_labels = {
            1: "Non-urgent inquiries",
            2: "Minor issues without significant impact",
            3: "Moderate issues affecting productivity",
            4: "Serious issues requiring prompt resolution",
            5: "Critical emergency with major business impact"
        }
        
        self.frustration_labels = {
            1: "Satisfied customers",
            2: "Mildly concerned",
            3: "Noticeably frustrated",
            4: "Highly frustrated",
            5: "Extremely frustrated"
        }
        
        self.priority_groups = {
            "Low Priority": (1, 3),
            "Medium Priority": (4, 6),
            "High Priority": (7, 8),
            "Critical Priority": (9, 10)
        }
        
        # Detailed explanations for each priority score
        self.priority_descriptions = {
            10: "Critical Emergency (Immediate action required, major business impact)",
            9: "Critical Priority (Urgent action needed, significant business impact)",
            8: "High Priority (Requires attention within 24 hours, significant impact)",
            7: "High Priority (Address within 48 hours, important issue)",
            6: "Medium-High Priority (Address within this week)",
            5: "Medium Priority (Address within this week)",
            4: "Medium Priority (Address when higher priorities are handled)",
            3: "Low Priority (Address when resources permit)",
            2: "Low Priority (Non-critical issue)",
            1: "Very Low Priority (Minor issue, can be deferred)"
        }
    
    def generate_report(
        self, analyses=None, zendesk_client=None, ai_analyzer=None, db_repository=None, 
        days=None, view=None, views=None, status="all", output_file=None, 
        format=None, limit=None, view_name=None, view_names=None, title=None,
        verbose=False
    ):
        """
        Generate a sentiment analysis report.
        
        Args:
            analyses: List of analysis results (optional)
            zendesk_client: ZendeskClient instance (optional)
            ai_analyzer: AIAnalyzer instance (optional)
            db_repository: DBRepository instance (optional)
            days: Number of days to look back (optional)
            view: View ID or name (optional)
            views: List of view IDs or names (optional)
            status: Ticket status (optional)
            output_file: File to write the report to (optional)
            format: Report format ("standard" or "enhanced") (optional)
            limit: Maximum number of tickets to include (optional)
            view_name: View name (alternative to view) (optional)
            view_names: List of view names (alternative to views) (optional)
            title: Report title (optional)
            verbose: Whether to include detailed information (optional)
            
        Returns:
            The generated report as a string
        """
        # Set report format based on parameter or instance setting
        if format == "standard":
            enhanced_mode = False
        elif format == "enhanced":
            enhanced_mode = True
        else:
            enhanced_mode = self.enhanced_mode
            
        # Set db_repository if provided
        if db_repository:
            self.db_repository = db_repository
        
        # If direct analyses are provided, use them
        if analyses:
            report_title = title or self.report_name
            if enhanced_mode:
                report_content = self._generate_enhanced_report(analyses, report_title)
            else:
                report_content = self._generate_standard_report(analyses, report_title)
            
            # Output the report
            self.output(report_content, output_file)
            
            return report_content
            
        # Otherwise, we need to query the database or analyze tickets
        
        # Get ticket analyses from database if available
        if self.db_repository or db_repository:
            db_repo = self.db_repository or db_repository
            
            # Get ticket analyses based on parameters
            start_date, time_period = self._calculate_time_period(days, view, views, zendesk_client)
            
            # Find analyses in database
            if days:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Find analyses in date range
                fetched_analyses = db_repo.find_analyses_between(start_date, end_date)
            else:
                # Default to 7 days if not specified
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                fetched_analyses = db_repo.find_analyses_between(start_date, end_date)
            
            if fetched_analyses:
                report_title = title or f"{self.report_name} - {time_period}"
                if enhanced_mode:
                    report_content = self._generate_enhanced_report(fetched_analyses, report_title)
                else:
                    report_content = self._generate_standard_report(fetched_analyses, report_title)
                
                # Output the report
                self.output(report_content, output_file)
                
                return report_content
        
        # If we reach here and have zendesk_client and ai_analyzer, analyze tickets
        if zendesk_client and ai_analyzer:
            # Calculate date range
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
                tickets = zendesk_client.fetch_tickets(status=status)
            
            # Filter by date
            tickets = [t for t in tickets if getattr(t, 'created_at', datetime.now()) >= start_date]
            
            if not tickets:
                return f"No tickets found for {time_period}"
            
            # Analyze tickets
            analyses = ai_analyzer.analyze_tickets_batch(tickets)
            
            # Generate the report using the analyses
            report_title = title or f"{self.report_name} for {time_period}"
            if enhanced_mode:
                report_content = self._generate_enhanced_report(analyses, report_title)
            else:
                report_content = self._generate_standard_report(analyses, report_title)
            
            # Output the report
            self.output(report_content, output_file)
            
            return report_content
                
        # If no analyses were found or provided
        report = "No analyses found for the specified time period."
        self.output(report, output_file)
        return report
        
    def _generate_standard_report(self, analyses, title=None):
        """Generate a standard sentiment analysis report."""
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
            self._create_report_header(title),
            "Total tickets analyzed: {0}".format(len(analyses_list)),
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
        
        # Add urgency counts
        urgency_mapping = {
            1: "Low", 2: "Low-Medium", 3: "Medium", 4: "High", 5: "Critical",
            "low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"
        }
        
        # Process numeric urgency levels (1-5)
        for level in range(1, 6):
            count = urgency_counts[level]
            if count > 0:
                percentage = (count / len(analyses_list)) * 100
                urgency_name = urgency_mapping.get(level, str(level))
                report.append(f"  {urgency_name}: {count} ({percentage:.1f}%)")
        
        # Process string urgency levels (for backward compatibility)
        for level in ["low", "medium", "high", "critical"]:
            count = urgency_counts[level]
            if count > 0:
                percentage = (count / len(analyses_list)) * 100
                urgency_name = urgency_mapping.get(level, level.capitalize())
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
    
    def _generate_enhanced_report(self, analyses, title=None):
        """Generate an enhanced sentiment analysis report with detailed metrics."""
        # Convert analyses to a list if it's a dictionary
        if isinstance(analyses, dict):
            analyses_list = list(analyses.values())
        else:
            analyses_list = analyses
            
        # Build the report
        report = self._create_report_header(title)
        
        # Count sentiment polarities for statistics
        sentiment_distribution = self._count_sentiment_polarities(analyses_list)
        
        # Create stats dictionary for executive summary
        stats = {
            "count": len(analyses_list),
            "sentiment_distribution": sentiment_distribution,
            "average_urgency": self._calculate_average_urgency(analyses_list),
            "average_frustration": self._calculate_average_frustration(analyses_list),
            "average_priority": self._calculate_average_priority(analyses_list),
            "business_impact_count": self._count_business_impact(analyses_list),
            "business_impact_percentage": (self._count_business_impact(analyses_list) / len(analyses_list) * 100) if len(analyses_list) > 0 else 0
        }
        
        # Add executive summary
        report += self._generate_executive_summary(stats, analyses_list)
        report += "\n"
            
        # Add basic statistics
        report += f"Total tickets analyzed: {len(analyses_list)}\n\n"
            
        # Add sentiment distribution with descriptive labels
        report += "SENTIMENT DISTRIBUTION\n---------------------\n"
        for sentiment, count in sorted(sentiment_distribution.items()):
            percentage = (count / len(analyses_list)) * 100 if len(analyses_list) > 0 else 0
            label = sentiment.capitalize()
            report += f"{label}: {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add priority score distribution with descriptive labels
        report += "PRIORITY DISTRIBUTION\n--------------------\n"
        for category, (min_val, max_val) in self.priority_groups.items():
            count = self._count_priority_range(analyses_list, min_val, max_val)
            percentage = (count / len(analyses_list)) * 100 if len(analyses_list) > 0 else 0
            report += f"{category} ({min_val}-{max_val}): {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add component analysis section
        components = self._extract_components(analyses_list)
        if components:
            report += "TOP AFFECTED COMPONENTS\n---------------------\n"
            total = sum(components.values())
            for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True)[:12]:
                if component != "none":
                    percentage = (count / total) * 100 if total > 0 else 0
                    report += f"{component}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Business impact section
        business_impact_tickets = self._filter_business_impact_tickets(analyses_list)
        if business_impact_tickets:
            report += "BUSINESS IMPACT DETECTED\n-----------------------\n"
            report += f"Business impact detected in {len(business_impact_tickets)} tickets ({(len(business_impact_tickets) / len(analyses_list)) * 100:.1f}%)\n\n"
            
            # Add a few examples
            report += "Examples:\n"
            for i, analysis in enumerate(business_impact_tickets[:3]):
                report += f"- Ticket #{analysis.get('ticket_id', 'Unknown')}: {analysis.get('subject', 'No Subject')}\n"
                if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                    business_impact = analysis['sentiment'].get('business_impact', {})
                    if business_impact and business_impact.get('description'):
                        report += f"  Impact: {business_impact.get('description')}\n"
            report += "\n"
        
        # High priority tickets section
        high_priority_tickets = self._filter_high_priority_tickets(analyses_list)
        if high_priority_tickets:
            report += "HIGH PRIORITY TICKETS\n--------------------\n"
            report += f"Found {len(high_priority_tickets)} high priority tickets (priority 7-10)\n\n"
            
            # Add details for up to 5 highest priority tickets
            for i, analysis in enumerate(sorted(high_priority_tickets, key=lambda x: x.get('priority_score', 0), reverse=True)[:5]):
                report += self._format_ticket_details(analysis) + "\n"
            report += "\n"
        
        # Add general statistics
        avg_urgency = self._calculate_average_urgency(analyses_list)
        avg_frustration = self._calculate_average_frustration(analyses_list)
        avg_priority = self._calculate_average_priority(analyses_list)
        
        report += f"AVERAGE METRICS\n--------------\n"
        report += f"Urgency: {avg_urgency:.2f}/5\n"
        report += f"Frustration: {avg_frustration:.2f}/5\n"
        report += f"Priority: {avg_priority:.2f}/10\n\n"
        
        report += self._create_report_footer()
        
        return report
    
    def generate_trend_report(self, zendesk_client, ai_analyzer, days: int = 90, 
                             interval: str = "week", enhanced_mode=None) -> str:
        """
        Generate a sentiment trend report for tickets over time.
        
        Args:
            zendesk_client: Zendesk client for fetching tickets
            ai_analyzer: AI analyzer for processing tickets
            days: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            enhanced_mode: Override enhanced mode setting
            
        Returns:
            Report content as a string
        """
        # Use instance mode if not specified
        use_enhanced = self.enhanced_mode if enhanced_mode is None else enhanced_mode
        
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
            self._create_report_header(f"Sentiment Trend Report - Last {days} Days"),
            f"Grouped by: {interval}",
            f"Total tickets analyzed: {len(tickets)}",
            "",
            f"{'Period':<12} | {'Count':<6} | {'Positive':<9} | {'Neutral':<9} | {'Negative':<9} | {'Avg Priority':<12}",
            f"{'-'*12} | {'-'*6} | {'-'*9} | {'-'*9} | {'-'*9} | {'-'*12}"
        ]
        
        # Process each time period
        for period, ticket_ids in sorted(time_groups.items()):
            # Get analyses for this period's tickets
            period_analyses = []
            for analysis in analyses:
                if analysis.get('ticket_id') in ticket_ids:
                    period_analyses.append(analysis)
            
            # Count sentiments
            sentiment_counts = Counter()
            priority_scores = []
            
            for analysis in period_analyses:
                sentiment = analysis.get("sentiment", {})
                if isinstance(sentiment, dict):
                    polarity = sentiment.get("polarity", "neutral")
                else:
                    polarity = sentiment or "neutral"
                    
                sentiment_counts[polarity] += 1
                
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
    
    def _generate_executive_summary(self, stats, analyses=None):
        """Generate an executive summary of the sentiment analysis."""
        summary = "EXECUTIVE SUMMARY\n"
        summary += "=================\n\n"
        
        # Add overall stats
        if hasattr(stats, 'get'):
            total_tickets = stats.get('count', 0) if 'count' in stats else len(analyses) if analyses else 0
            
            # Calculate high priority tickets
            high_priority = sum(1 for a in analyses if a.get('priority_score', 0) >= 7) if analyses else stats.get('high_priority_count', 0)
            
            # Calculate business impact
            business_impact = sum(1 for a in analyses if 'sentiment' in a and isinstance(a['sentiment'], dict) 
                              and a['sentiment'].get('business_impact', {}).get('detected', False)) \
                              if analyses else stats.get('business_impact_count', 0)
            
            # Add statistics
            summary += f"Total Tickets Analyzed: {total_tickets}\n"
            summary += f"High Priority Tickets: {high_priority} ({self._format_percentage(high_priority, total_tickets)})\n"
            summary += f"Business Impact Detected: {business_impact} ({self._format_percentage(business_impact, total_tickets)})\n\n"
            
            # Add key insights
            if high_priority > 0:
                summary += "Key Insights:\n"
                summary += "- High priority tickets should be addressed immediately\n"
                
            if business_impact > 0:
                summary += "- {0} of tickets indicate business impact\n".format(self._format_percentage(business_impact, total_tickets))
        
        return summary
    
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
    
    def _extract_components(self, analyses):
        """Extract and count component types from analyses."""
        components = {}
        
        for analysis in analyses:
            component = analysis.get('component', 'none')
            if component and component != "none":
                components[component] = components.get(component, 0) + 1
        
        return components
        
    def _count_priority_range(self, analyses, min_val, max_val):
        """Count priority scores within a specific range."""
        count = 0
        
        for analysis in analyses:
            score = analysis.get('priority_score')
            if score is not None and min_val <= score <= max_val:
                count += 1
                
        return count

    def _filter_business_impact_tickets(self, analyses):
        """Filter tickets with business impact."""
        business_impact = []
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                impact = analysis['sentiment'].get('business_impact', {})
                if impact and impact.get('detected', False):
                    business_impact.append(analysis)
                
        return business_impact

    def _filter_high_priority_tickets(self, analyses, threshold=7):
        """Filter tickets with priority scores above the threshold."""
        high_priority = []
        
        for analysis in analyses:
            score = analysis.get('priority_score')
            if score is not None and score >= threshold:
                high_priority.append(analysis)
                
        return high_priority

    def _format_ticket_details(self, analysis):
        """Format details for a single ticket with enhanced descriptive labels."""
        ticket_id = analysis.get('ticket_id', 'Unknown')
        subject = analysis.get('subject', 'No Subject')
        
        # Format basic ticket info
        ticket_info = f"#{ticket_id} - {subject}\n"
        
        # Add priority score with description
        priority = analysis.get('priority_score')
        if priority:
            desc = self.priority_descriptions.get(priority, "")
            ticket_info += f"  Priority: {priority}/10 - {desc}\n"
        
        # Add sentiment information with enhanced labels
        sentiment = analysis.get('sentiment')
        if isinstance(sentiment, dict):
            # Enhanced sentiment
            polarity = sentiment.get('polarity', 'unknown')
            ticket_info += f"  Sentiment: {polarity.capitalize()}\n"
            
            # Add urgency and frustration with descriptive labels
            if 'urgency_level' in sentiment:
                urgency = sentiment['urgency_level']
                label = self.urgency_labels.get(urgency, "")
                ticket_info += f"  Urgency: {urgency}/5 - {label}\n"
                
            if 'frustration_level' in sentiment:
                frustration = sentiment['frustration_level']
                label = self.frustration_labels.get(frustration, "")
                ticket_info += f"  Frustration: {frustration}/5 - {label}\n"
                
            # Add business impact if detected
            business_impact = sentiment.get('business_impact', {})
            if business_impact and business_impact.get('detected', False):
                description = business_impact.get('description', 'Business impact detected')
                ticket_info += f"  Business Impact: {description}\n"
                
            # Add emotions if available
            emotions = sentiment.get('emotions', [])
            if emotions:
                ticket_info += f"  Emotions: {', '.join(emotions)}\n"
        else:
            # Basic sentiment
            ticket_info += f"  Sentiment: {sentiment}\n"
        
        # Add component if available
        component = analysis.get('component')
        if component and component != "none":
            ticket_info += f"  Component: {component}\n"
        
        # Add category
        category = analysis.get('category', 'uncategorized')
        ticket_info += f"  Category: {category}\n"
        
        return ticket_info

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
