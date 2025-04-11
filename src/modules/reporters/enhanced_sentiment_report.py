"""
Enhanced Sentiment Report Module

This module generates more intuitive reports with descriptive labels
for sentiment analysis results.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from .reporter_base import ReporterBase

# Set up logging
logger = logging.getLogger(__name__)

# Import statistics module
import statistics

class EnhancedSentimentReporter(ReporterBase):
    """Generates enhanced reports focused on sentiment analysis results."""
    
    def __init__(self, db_repository=None):
        """Initialize the reporter."""
        # Initialize the parent class
        super().__init__()
        
        # Set db_repository
        self.db_repository = db_repository
        
        # Define descriptive labels for various scales
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
        self, analyses=None, zendesk_client=None, db_repository=None, days=None, view=None, views=None, 
        status="all", output_file=None, format="enhanced", limit=None, 
        view_name=None, view_names=None, title=None
    ):
        """
        Generate an enhanced sentiment analysis report.
        
        Args:
            analyses: List of analysis results (optional)
            zendesk_client: ZendeskClient instance (optional)
            db_repository: DBRepository instance (optional)
            days: Number of days to look back (optional)
            view: View ID or name (optional)
            views: List of view IDs or names (optional)
            status: Ticket status (optional)
            output_file: File to write the report to (optional)
            format: Report format (enhanced or standard) (optional)
            limit: Maximum number of tickets to include (optional)
            view_name: View name (alternative to view) (optional)
            view_names: List of view names (alternative to views) (optional)
            title: Report title (optional)
            
        Returns:
            The generated report as a string
        """
        # Set up output file
        self.output_file = output_file
        
        # If direct analyses are provided, use them
        if analyses:
            report_title = title or "Enhanced Sentiment Analysis Report"
            report_content = self._generate_full_report(analyses, report_title)
            
            # Output the report
            self.output(report_content, output_file)
            
            return report_content
        
        # Get ticket analyses from database if available
        if db_repository:
            # Get ticket analyses based on parameters
            start_date, time_period = self._calculate_time_period(days, view, views)
            
            # Find analyses in database
            if days:
                # Calculate date range
                from datetime import datetime, timedelta
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Find analyses in date range
                fetched_analyses = db_repository.find_analyses_between(start_date, end_date)
            else:
                # Default to 7 days if not specified
                from datetime import datetime, timedelta
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                fetched_analyses = db_repository.find_analyses_between(start_date, end_date)
            
            if fetched_analyses:
                report_title = title or f"Enhanced Sentiment Analysis Report - {time_period}"
                report_content = self._generate_full_report(fetched_analyses, report_title)
                
                # Output the report
                self.output(report_content, output_file)
                
                return report_content
        
        # If no analyses were found or provided
        report = "No analyses found for the specified time period."
        self.output(report, output_file)
        return report
    
    def _generate_full_report(self, analyses, title=None):
        """Generate the full enhanced sentiment report."""
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"ENHANCED SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Count sentiment polarities for statistics
        sentiment_distribution = self._count_sentiment_polarities(analyses)
        
        # Create stats dictionary for executive summary
        stats = {
            "count": len(analyses),
            "sentiment_distribution": sentiment_distribution,
            "average_urgency": self._calculate_average_urgency(analyses),
            "average_frustration": self._calculate_average_frustration(analyses),
            "average_priority": self._calculate_average_priority(analyses),
            "business_impact_count": self._count_business_impact(analyses),
            "business_impact_percentage": (self._count_business_impact(analyses) / len(analyses) * 100) if len(analyses) > 0 else 0
        }
        
        # Add executive summary
        report += self._generate_executive_summary(stats, analyses)
        report += "\n"
            
        # Add basic statistics
        report += f"Total tickets analyzed: {len(analyses)}\n\n"
            
        # Add sentiment distribution with descriptive labels
        report += "SENTIMENT DISTRIBUTION\n---------------------\n"
        for sentiment, count in sorted(sentiment_distribution.items()):
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            label = sentiment.capitalize()
            report += f"{label}: {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add priority score distribution with descriptive labels
        report += "PRIORITY DISTRIBUTION\n--------------------\n"
        for category, (min_val, max_val) in self.priority_groups.items():
            count = self._count_priority_range(analyses, min_val, max_val)
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            report += f"{category} ({min_val}-{max_val}): {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Add component analysis section
        components = self._extract_components(analyses)
        if components:
            report += "TOP AFFECTED COMPONENTS\n---------------------\n"
            total = sum(components.values())
            for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True)[:12]:
                if component != "none":
                    percentage = (count / total) * 100 if total > 0 else 0
                    report += f"{component}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Business impact section
        business_impact_tickets = self._filter_business_impact_tickets(analyses)
        if business_impact_tickets:
            report += "BUSINESS IMPACT DETECTED\n-----------------------\n"
            report += f"Business impact detected in {len(business_impact_tickets)} tickets ({(len(business_impact_tickets) / len(analyses)) * 100:.1f}%)\n\n"
            
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
        high_priority_tickets = self._filter_high_priority_tickets(analyses)
        if high_priority_tickets:
            report += "HIGH PRIORITY TICKETS\n--------------------\n"
            report += f"Found {len(high_priority_tickets)} high priority tickets (priority 7-10)\n\n"
            
            # Add details for up to 10 highest priority tickets (increased from 5)
            for i, analysis in enumerate(sorted(high_priority_tickets, key=lambda x: x.get('priority_score', 0), reverse=True)[:10]):
                report += self._format_ticket_details(analysis) + "\n"
            report += "\n"
        
        # Add general statistics
        avg_urgency = self._calculate_average_urgency(analyses)
        avg_frustration = self._calculate_average_frustration(analyses)
        avg_priority = self._calculate_average_priority(analyses)
        
        report += f"AVERAGE METRICS\n--------------\n"
        report += f"Urgency: {avg_urgency:.2f}/5\n"
        report += f"Frustration: {avg_frustration:.2f}/5\n"
        report += f"Priority: {avg_priority:.2f}/10\n\n"
        
        return report
    
    def _extract_components(self, analyses):
        """Extract and count component types from analyses."""
        components = {}
        
        for analysis in analyses:
            component = analysis.get('component', 'none')
            if component and component != "none":
                components[component] = components.get(component, 0) + 1
        
        return components
    
    def _generate_executive_summary(self, stats, analyses=None):
        """Generate an executive summary of the sentiment analysis."""
        # Example implementation
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
    
    def _format_urgency_level(self, level):
        """Format urgency level with descriptive label."""
        if not level:
            return "Unknown"
            
        try:
            level = int(level)
        except (ValueError, TypeError):
            return str(level)
            
        # Descriptive labels for levels
        labels = {
            1: "Very Low",
            2: "Low",
            3: "Medium",
            4: "High",
            5: "Critical"
        }
        
        # Calculate percentage
        percentage = (level / 5) * 100
        
        return f"{level} - {labels.get(level, 'Unknown')} ({percentage:.0f}%)"
    
    def _format_frustration_level(self, level):
        """Format frustration level with descriptive label."""
        if not level:
            return "Unknown"
            
        try:
            level = int(level)
        except (ValueError, TypeError):
            return str(level)
            
        # Descriptive labels for levels
        labels = {
            1: "None",
            2: "Slight",
            3: "Moderate",
            4: "High",
            5: "Extreme"
        }
        
        # Calculate percentage
        percentage = (level / 5) * 100
        
        return f"{level} - {labels.get(level, 'Unknown')} ({percentage:.0f}%)"
    
    def _extract_emotions(self, analyses):
        """Extract and count emotions from analyses."""
        emotions_counter = {}
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                emotions = analysis['sentiment'].get('emotions', [])
                if emotions:
                    for emotion in emotions:
                        emotions_counter[emotion] = emotions_counter.get(emotion, 0) + 1
        
        return emotions_counter

    def _extract_key_phrases(self, analyses):
        """Extract key phrases from analyses."""
        phrases = []
        
        for analysis in analyses:
            if 'sentiment' in analysis and isinstance(analysis['sentiment'], dict):
                key_phrases = analysis['sentiment'].get('key_phrases', [])
                if key_phrases:
                    phrases.extend(key_phrases)
        
        # Return top phrases
        return phrases[:10]
    
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
                    
                # Increment the count for this polarity
                polarity_counts[polarity] = polarity_counts.get(polarity, 0) + 1
        
        return polarity_counts
        
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
    
    def save_report(self, report, output_file=None):
        """Save the report to a file."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_file = f"sentiment_analysis_report_{timestamp}.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        return output_file
    
    def _format_percentage(self, part, total):
        """Format a percentage with 1 decimal place."""
        if total == 0:
            return "0.0%"
        return f"{(part / total) * 100:.1f}%"
