"""
Sentiment Reporter Module

Generates reports about sentiment analysis of support tickets.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from .reporter_base import ReporterBase

# Set up logging
logger = logging.getLogger(__name__)

class SentimentReporter(ReporterBase):
    """
    Generates reports focused on sentiment analysis of support tickets.
    """
    
    def __init__(self):
        """Initialize the sentiment reporter."""
        # Initialize the parent class
        super().__init__()
        
        # Define sentiment categories
        self.sentiment_categories = {
            'positive': 'Positive',
            'neutral': 'Neutral',
            'negative': 'Negative',
            'unknown': 'Unknown'
        }
        
        # Define priority score categories
        self.priority_categories = {
            'Low': (1, 3),
            'Medium': (4, 6),
            'High': (7, 8),
            'Critical': (9, 10)
        }
    
    def generate_report(
        self, analyses=None, zendesk_client=None, db_repository=None, days=None, view=None, views=None, 
        status="all", output_file=None, format="standard", limit=None, 
        view_name=None, view_names=None, title=None
    ):
        """
        Generate a sentiment analysis report.
        
        Args:
            zendesk_client: ZendeskClient instance
            db_repository: DBRepository instance
            days: Number of days to look back
            view: View ID or name
            views: List of view IDs or names
            status: Ticket status
            output_file: File to write the report to
            format: Report format
            limit: Maximum number of tickets to include
            view_name: View name (alternative to view)
            view_names: List of view names (alternative to views)
            
        Returns:
            The generated report as a string
        """
        # Convert view_name/view_names to view/views if provided
        if view_name and not view:
            view = view_name
        if view_names and not views:
            views = view_names
            
        # Set up output file
        self.output_file = output_file
        
        # If direct analyses are provided, use them
        if analyses is not None:
            time_period = "provided analyses"
            report_title = title or f"Sentiment Analysis Report - {time_period}"
            
            # Look up view information
            if view and zendesk_client:
                view_obj = self._get_view_by_id_or_name(view, zendesk_client)
                if view_obj and hasattr(view_obj, 'title'):
                    report_title += f" for view '{view_obj.title}'"
                else:
                    report_title += f" for view '{view}'"

            # Create the report with header
            report = f"\n{'='*60}\n"
            report += f"SENTIMENT ANALYSIS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            report += f"{'='*60}\n\n"
            
            if title:
                report += f"{title}\n{'-' * len(title)}\n\n"
                
            if len(analyses) == 0:
                report += f"No analysis data found for {time_period}.\n"
            else:
                # Generate the full report with data
                report = self._generate_report_content(analyses, report_title)
        else:
            # Get ticket analyses based on parameters
            start_date, time_period = self._calculate_time_period(days, view, views, zendesk_client)
            
            # Here we would normally query the database for analyses
            # For testing purposes, use an empty list if no database is provided
            if db_repository:
                # This would be the actual database query in a real implementation
                # For now, leave it as a placeholder
                fetched_analyses = []
            else:
                fetched_analyses = []
            
            if not fetched_analyses:
                report = f"No sentiment analysis data found for {time_period}."
            else:
                # Generate the actual report
                report = self._generate_report_content(fetched_analyses, f"Sentiment Analysis Report - {time_period}")
        
        # Output the report
        self.output(report, output_file)
        
        return report
    
    def _generate_report_content(self, analyses, title=None):
        """Generate the sentiment analysis report content."""
        # Check if analyses is empty
        if len(analyses) == 0:
            report = f"\n{'='*60}\n"
            report += f"SENTIMENT ANALYSIS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            report += f"{'='*60}\n\n"
            if title:
                report += f"{title}\n{'-' * len(title)}\n\n"
            report += "No analysis data found. Please check your search criteria or ensure that sentiment analysis has been run.\n"
            return report
            
        # Create the report header
        report = f"\n{'='*60}\n"
        report += f"SENTIMENT ANALYSIS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Add summary section
        report += f"Total tickets analyzed: {len(analyses)}\n\n"
        
        # Add sentiment distribution
        sentiment_distribution = self._count_sentiment(analyses)
        report += "SENTIMENT DISTRIBUTION\n---------------------\n"
        for sentiment, count in sorted(sentiment_distribution.items()):
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            label = self.sentiment_categories.get(sentiment, 'Unknown')
            report += f"{label}: {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add priority score distribution if available
        priority_distribution = self._count_priority_scores(analyses)
        if priority_distribution:
            report += "PRIORITY DISTRIBUTION\n--------------------\n"
            for category, (min_val, max_val) in self.priority_categories.items():
                count = sum(priority_distribution.get(score, 0) for score in range(min_val, max_val + 1))
                percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
                report += f"{category} Priority ({min_val}-{max_val}): {count} tickets ({percentage:.1f}%)\n"
            report += "\n"
        
        # Add high priority tickets section
        high_priority_tickets = self._filter_high_priority_tickets(analyses)
        if high_priority_tickets:
            report += "HIGH PRIORITY TICKETS\n--------------------\n"
            report += "The following tickets have high priority scores (7-10):\n\n"
            for analysis in high_priority_tickets:
                report += self._format_ticket_details(analysis) + "\n"
            report += "\n"
        
        return report
    
    def _count_sentiment(self, analyses):
        """Count sentiment distribution in analyses."""
        sentiment_counts = Counter()
        
        for analysis in analyses:
            sentiment = analysis.get('sentiment')
            if isinstance(sentiment, dict):
                # Enhanced sentiment contains polarity
                polarity = sentiment.get('polarity', 'unknown')
                sentiment_counts[polarity] += 1
            else:
                # Simple sentiment
                sentiment_counts[sentiment or 'unknown'] += 1
                
        return dict(sentiment_counts)
    
    def _count_priority_scores(self, analyses):
        """Count priority score distribution in analyses."""
        priority_counts = Counter()
        
        for analysis in analyses:
            score = analysis.get('priority_score')
            if score:
                priority_counts[score] += 1
                
        return dict(priority_counts)
    
    def _filter_high_priority_tickets(self, analyses, threshold=7):
        """Filter tickets with priority scores above the threshold."""
        high_priority = []
        
        for analysis in analyses:
            score = analysis.get('priority_score')
            if score and score >= threshold:
                high_priority.append(analysis)
                
        return sorted(high_priority, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    def _format_ticket_details(self, analysis):
        """Format details for a single ticket."""
        ticket_id = analysis.get('ticket_id', 'Unknown')
        subject = analysis.get('subject', 'No Subject')
        
        # Format basic ticket info
        ticket_info = f"#{ticket_id} - {subject}\n"
        
        # Add sentiment information
        sentiment = analysis.get('sentiment')
        if isinstance(sentiment, dict):
            # Enhanced sentiment
            polarity = sentiment.get('polarity', 'unknown')
            ticket_info += f"  Sentiment: {polarity}\n"
            
            # Add urgency and frustration if available
            if 'urgency_level' in sentiment:
                ticket_info += f"  Urgency: {sentiment['urgency_level']}/5\n"
            if 'frustration_level' in sentiment:
                ticket_info += f"  Frustration: {sentiment['frustration_level']}/5\n"
                
            # Add business impact if detected
            business_impact = sentiment.get('business_impact', {})
            if business_impact and business_impact.get('detected', False):
                description = business_impact.get('description', 'Business impact detected')
                ticket_info += f"  Business Impact: {description}\n"
        else:
            # Simple sentiment
            ticket_info += f"  Sentiment: {sentiment}\n"
        
        # Add priority score if available
        priority = analysis.get('priority_score')
        if priority:
            ticket_info += f"  Priority: {priority}/10\n"
            
        # Add component if available
        component = analysis.get('component')
        if component and component != 'none':
            ticket_info += f"  Component: {component}\n"
            
        # Add category
        category = analysis.get('category', 'uncategorized')
        ticket_info += f"  Category: {category}\n"
        
        return ticket_info
        
    def save_report(self, report, filename=None):
        """
        Save a report to a file.
        
        Args:
            report: The report content to save
            filename: The filename to save to, or None for auto-generated name
            
        Returns:
            The filename used
        """
        if not filename:
            # Generate a filename based on timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"sentiment_analysis_report_{timestamp}.txt"
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report to {filename}: {e}")
            return None
            
    def _count_sentiment_polarities(self, analyses):
        """
        Count sentiment polarities in the analyses.
        Used for multi-view reports.
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Dictionary mapping polarities to counts
        """
        return self._count_sentiment(analyses)
        
    def _calculate_average_urgency(self, analyses):
        """
        Calculate average urgency level from analyses.
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Float representing average urgency
        """
        urgency_values = []
        for analysis in analyses:
            sentiment = analysis.get('sentiment', {})
            if isinstance(sentiment, dict) and 'urgency_level' in sentiment:
                urgency_values.append(sentiment['urgency_level'])
                
        return sum(urgency_values) / len(urgency_values) if urgency_values else 0.0
        
    def _calculate_average_frustration(self, analyses):
        """
        Calculate average frustration level from analyses.
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Float representing average frustration
        """
        frustration_values = []
        for analysis in analyses:
            sentiment = analysis.get('sentiment', {})
            if isinstance(sentiment, dict) and 'frustration_level' in sentiment:
                frustration_values.append(sentiment['frustration_level'])
                
        return sum(frustration_values) / len(frustration_values) if frustration_values else 0.0
        
    def _calculate_average_priority(self, analyses):
        """
        Calculate average priority score from analyses.
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Float representing average priority
        """
        priority_values = []
        for analysis in analyses:
            priority = analysis.get('priority_score')
            if priority is not None:
                priority_values.append(priority)
                
        return sum(priority_values) / len(priority_values) if priority_values else 0.0
        
    def _count_business_impact(self, analyses):
        """
        Count analyses with business impact detected.
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Integer count of business impact cases
        """
        count = 0
        for analysis in analyses:
            sentiment = analysis.get('sentiment', {})
            if isinstance(sentiment, dict):
                business_impact = sentiment.get('business_impact', {})
                if business_impact and business_impact.get('detected', False):
                    count += 1
        return count
