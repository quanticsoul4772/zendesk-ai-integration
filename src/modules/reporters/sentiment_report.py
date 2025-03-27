"""
Sentiment Report Module

This module generates detailed reports about sentiment analysis results.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

# Set up logging
logger = logging.getLogger(__name__)

class SentimentReporter:
    """Generates reports focused on sentiment analysis results."""
    
    def __init__(self, db_repository=None):
        """Initialize the reporter."""
        self.db_repository = db_repository
    
    def generate_report(self, analyses: List[Dict], title: Optional[str] = None) -> str:
        """
        Generate a comprehensive sentiment analysis report.
        
        Args:
            analyses: List of analysis results
            title: Optional title for the report
            
        Returns:
            Formatted report text.
        """
        if not analyses:
            return "No analyses found for reporting."
        
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total Tickets Analyzed: {len(analyses)}\n\n"
        
        # Sentiment distribution
        polarity_counts = self._count_sentiment_polarities(analyses)
        report += "SENTIMENT DISTRIBUTION\n--------------------\n"
        for polarity, count in sorted(polarity_counts.items()):
            report += f"{polarity}: {count}\n"
        report += "\n"
        
        # Urgency distribution
        urgency_counts = self._count_urgency_levels(analyses)
        report += "URGENCY LEVEL DISTRIBUTION\n------------------------\n"
        for level, count in sorted(urgency_counts.items()):
            report += f"Level {level}: {count}\n"
        report += "\n"
        
        # Frustration distribution
        frustration_counts = self._count_frustration_levels(analyses)
        report += "FRUSTRATION LEVEL DISTRIBUTION\n----------------------------\n"
        for level, count in sorted(frustration_counts.items()):
            report += f"Level {level}: {count}\n"
        report += "\n"
        
        # Business impact
        business_impact_count = self._count_business_impact(analyses)
        report += "BUSINESS IMPACT\n--------------\n"
        report += f"Tickets with business impact: {business_impact_count}\n"
        report += f"Percentage of total: {(business_impact_count / len(analyses)) * 100:.2f}%\n\n"
        
        # Priority score distribution
        priority_counts = self._count_priority_scores(analyses)
        report += "PRIORITY SCORE DISTRIBUTION\n--------------------------\n"
        for score, count in sorted(priority_counts.items()):
            report += f"Score {score}: {count}\n"
        report += "\n"
        
        # Calculate averages
        avg_urgency = self._calculate_average_urgency(analyses)
        avg_frustration = self._calculate_average_frustration(analyses)
        avg_priority = self._calculate_average_priority(analyses)
        
        report += "AVERAGES\n--------\n"
        report += f"Average Urgency Level: {avg_urgency:.2f}/5\n"
        report += f"Average Frustration Level: {avg_frustration:.2f}/5\n"
        report += f"Average Priority Score: {avg_priority:.2f}/10\n\n"
        
        # Category distribution
        category_counts = self._count_categories(analyses)
        report += "CATEGORY DISTRIBUTION\n--------------------\n"
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"{category}: {count}\n"
        report += "\n"
        
        # Component distribution
        component_counts = self._count_components(analyses)
        if component_counts:
            report += "COMPONENT DISTRIBUTION\n---------------------\n"
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
                if component != "none":
                    report += f"{component}: {count}\n"
            report += "\n"
        
        # High priority tickets
        high_priority_tickets = self._get_high_priority_tickets(analyses)
        if high_priority_tickets:
            report += "HIGH PRIORITY TICKETS\n-------------------\n"
            for analysis in high_priority_tickets:
                ticket_id = analysis.get("ticket_id", "Unknown")
                subject = analysis.get("subject", "No Subject")
                priority = analysis.get("priority_score", 0)
                report += f"#{ticket_id} - {subject} (Priority: {priority}/10)\n"
            report += "\n"
        
        # Business impact tickets
        business_impact_tickets = self._get_business_impact_tickets(analyses)
        if business_impact_tickets:
            report += "BUSINESS IMPACT TICKETS\n----------------------\n"
            for analysis in business_impact_tickets:
                ticket_id = analysis.get("ticket_id", "Unknown")
                subject = analysis.get("subject", "No Subject")
                sentiment = analysis.get("sentiment", {})
                if isinstance(sentiment, dict):
                    business_impact = sentiment.get("business_impact", {})
                    description = business_impact.get("description", "Detected") if business_impact else "Detected"
                    report += f"#{ticket_id} - {subject}\n"
                    report += f"  Impact: {description}\n"
            report += "\n"
        
        return report
    
    def generate_multi_view_report(self, analyses: List[Dict], view_map: Dict = None, title: Optional[str] = None) -> str:
        """
        Generate a sentiment analysis report for tickets from multiple views.
        
        Args:
            analyses: List of analysis results with source_view_id attributes
            view_map: Dict mapping view IDs to view names
            title: Optional title for the report
            
        Returns:
            Formatted report text.
        """
        if not analyses:
            return "No analyses found for reporting."
        
        # Group analyses by view
        view_analyses = {}
        for analysis in analyses:
            view_id = analysis.get('source_view_id', 'unknown')
            if view_id not in view_analyses:
                view_analyses[view_id] = []
            view_analyses[view_id].append(analysis)
        
        now = datetime.now()
        report = f"\n{'='*60}\n"
        report += f"MULTI-VIEW SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total Tickets Analyzed: {len(analyses)}\n"
        report += f"Total Views: {len(view_analyses)}\n\n"
        
        # Views summary section
        report += "TICKETS BY VIEW\n--------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"{view_name}: {len(view_tickets)} tickets\n"
        report += "\n"
        
        # Combined sentiment analysis
        report += "COMBINED SENTIMENT ANALYSIS\n-------------------------\n"
        
        # Sentiment distribution
        polarity_counts = self._count_sentiment_polarities(analyses)
        report += "Sentiment Distribution:\n"
        for polarity, count in sorted(polarity_counts.items()):
            report += f"{polarity}: {count}\n"
        report += "\n"
        
        # Priority distribution
        priority_counts = self._count_priority_scores(analyses)
        report += "Priority Score Distribution:\n"
        for score, count in sorted(priority_counts.items()):
            if count > 0:  # Only show scores that have tickets
                report += f"Score {score}: {count}\n"
        report += "\n"
        
        # Calculate averages
        avg_urgency = self._calculate_average_urgency(analyses)
        avg_frustration = self._calculate_average_frustration(analyses)
        avg_priority = self._calculate_average_priority(analyses)
        
        report += "Averages:\n"
        report += f"Average Urgency Level: {avg_urgency:.2f}/5\n"
        report += f"Average Frustration Level: {avg_frustration:.2f}/5\n"
        report += f"Average Priority Score: {avg_priority:.2f}/10\n\n"
        
        # Business impact
        business_impact_count = self._count_business_impact(analyses)
        report += "Business Impact:\n"
        report += f"Tickets with business impact: {business_impact_count}\n"
        report += f"Percentage of total: {(business_impact_count / len(analyses)) * 100:.2f}%\n\n"
        
        # Per-view sentiment analysis
        report += "PER-VIEW SENTIMENT ANALYSIS\n--------------------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            
            # Get sentiment distribution for this view
            polarity_counts = self._count_sentiment_polarities(view_tickets)
            report += "Sentiment Distribution:\n"
            for polarity, count in sorted(polarity_counts.items()):
                report += f"  {polarity}: {count}\n"
            
            # Get priority distribution for this view
            priority_counts = self._count_priority_scores(view_tickets)
            high_priority = sum(count for score, count in priority_counts.items() if score >= 7)
            report += f"High Priority Tickets (7-10): {high_priority}\n"
            
            # Get business impact for this view
            business_impact_count = self._count_business_impact(view_tickets)
            report += f"Business Impact Tickets: {business_impact_count}\n"
            
            # Calculate averages for this view
            avg_urgency = self._calculate_average_urgency(view_tickets)
            avg_frustration = self._calculate_average_frustration(view_tickets)
            avg_priority = self._calculate_average_priority(view_tickets)
            
            report += f"Average Urgency: {avg_urgency:.2f}/5\n"
            report += f"Average Frustration: {avg_frustration:.2f}/5\n"
            report += f"Average Priority: {avg_priority:.2f}/10\n"
            
            # Add high priority tickets for this view
            high_priority_tickets = self._get_high_priority_tickets(view_tickets)
            if high_priority_tickets:
                report += "High Priority Tickets:\n"
                for analysis in high_priority_tickets[:5]:  # Show only top 5 per view to keep report readable
                    ticket_id = analysis.get("ticket_id", "Unknown")
                    subject = analysis.get("subject", "No Subject")
                    priority = analysis.get("priority_score", 0)
                    report += f"  #{ticket_id} - {subject} (Priority: {priority}/10)\n"
                
                if len(high_priority_tickets) > 5:
                    report += f"  ... and {len(high_priority_tickets) - 5} more\n"
        
        return report
    
    def _count_sentiment_polarities(self, analyses: List[Dict]) -> Dict[str, int]:
        """Count the distribution of sentiment polarities."""
        counts = {}
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                polarity = sentiment.get("polarity", "unknown")
            else:
                polarity = sentiment
            counts[polarity] = counts.get(polarity, 0) + 1
        return counts
    
    def _count_urgency_levels(self, analyses: List[Dict]) -> Dict[int, int]:
        """Count the distribution of urgency levels."""
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                level = sentiment.get("urgency_level", 1)
                counts[level] = counts.get(level, 0) + 1
        return counts
    
    def _count_frustration_levels(self, analyses: List[Dict]) -> Dict[int, int]:
        """Count the distribution of frustration levels."""
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                level = sentiment.get("frustration_level", 1)
                counts[level] = counts.get(level, 0) + 1
        return counts
    
    def _count_business_impact(self, analyses: List[Dict]) -> int:
        """Count tickets with business impact detected."""
        count = 0
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                business_impact = sentiment.get("business_impact", {})
                if business_impact and business_impact.get("detected", False):
                    count += 1
        return count
    
    def _count_priority_scores(self, analyses: List[Dict]) -> Dict[int, int]:
        """Count the distribution of priority scores."""
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0}
        for analysis in analyses:
            score = analysis.get("priority_score", 1)
            counts[score] = counts.get(score, 0) + 1
        return counts
    
    def _count_categories(self, analyses: List[Dict]) -> Dict[str, int]:
        """Count the distribution of categories."""
        counts = {}
        for analysis in analyses:
            category = analysis.get("category", "uncategorized")
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _count_components(self, analyses: List[Dict]) -> Dict[str, int]:
        """Count the distribution of hardware components."""
        counts = {}
        for analysis in analyses:
            component = analysis.get("component", "none")
            counts[component] = counts.get(component, 0) + 1
        return counts
    
    def _calculate_average_urgency(self, analyses: List[Dict]) -> float:
        """Calculate the average urgency level."""
        urgency_levels = []
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                level = sentiment.get("urgency_level", 1)
                urgency_levels.append(level)
        return statistics.mean(urgency_levels) if urgency_levels else 0
    
    def _calculate_average_frustration(self, analyses: List[Dict]) -> float:
        """Calculate the average frustration level."""
        frustration_levels = []
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                level = sentiment.get("frustration_level", 1)
                frustration_levels.append(level)
        return statistics.mean(frustration_levels) if frustration_levels else 0
    
    def _calculate_average_priority(self, analyses: List[Dict]) -> float:
        """Calculate the average priority score."""
        priority_scores = []
        for analysis in analyses:
            score = analysis.get("priority_score", 1)
            priority_scores.append(score)
        return statistics.mean(priority_scores) if priority_scores else 0
    
    def _get_high_priority_tickets(self, analyses: List[Dict], threshold: int = 7) -> List[Dict]:
        """Get high priority tickets above the threshold."""
        high_priority = []
        for analysis in analyses:
            score = analysis.get("priority_score", 0)
            if score >= threshold:
                high_priority.append(analysis)
        return sorted(high_priority, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    def _get_business_impact_tickets(self, analyses: List[Dict]) -> List[Dict]:
        """Get tickets with business impact detected."""
        impact_tickets = []
        for analysis in analyses:
            sentiment = analysis.get("sentiment", {})
            if isinstance(sentiment, dict):
                business_impact = sentiment.get("business_impact", {})
                if business_impact and business_impact.get("detected", False):
                    impact_tickets.append(analysis)
        return impact_tickets
    
    def save_report(self, report: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Save the report to a file.
        
        Args:
            report: Report content to save
            filename: Filename to use (if None, generates a timestamp-based name)
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"sentiment_analysis_report_{timestamp}.txt"
        
        try:
            with open(filename, "w") as file:
                file.write(report)
            logger.info(f"Sentiment analysis report saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            return None
    
    def generate_time_period_report(self, time_period: str = "week", title: Optional[str] = None) -> str:
        """
        Generate a report for a specific time period.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            title: Optional title for the report
            
        Returns:
            Formatted report text.
        """
        if not self.db_repository:
            return "Error: No database repository available for time period reporting."
        
        # Calculate the date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        
        if time_period == "day":
            start_date = end_date - timedelta(days=1)
            period_name = "Last 24 Hours"
        elif time_period == "week":
            start_date = end_date - timedelta(days=7)
            period_name = "Last 7 Days"
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
            period_name = "Last 30 Days"
        elif time_period == "year":
            start_date = end_date - timedelta(days=365)
            period_name = "Last 365 Days"
        else:
            start_date = end_date - timedelta(days=7)
            period_name = "Last 7 Days"
        
        # Get analyses for the time period
        analyses = self.db_repository.find_analyses_between(start_date, end_date)
        
        if not analyses:
            return f"No analyses found for the {period_name}."
        
        # Use the regular report generator with the time period analyses
        if not title:
            title = f"Sentiment Analysis Report - {period_name}"
            
        return self.generate_report(analyses, title)
