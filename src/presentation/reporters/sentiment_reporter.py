"""
Sentiment Reporter Implementation

This module provides an implementation of the SentimentReporter interface.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.domain.entities.ticket_analysis import TicketAnalysis
from src.domain.interfaces.reporter_interfaces import SentimentReporter

# Set up logging
logger = logging.getLogger(__name__)


class SentimentReporterImpl(SentimentReporter):
    """
    Implementation of the SentimentReporter interface.
    
    This reporter generates reports based on sentiment analysis of tickets.
    """
    
    def generate_report(self, analyses: List[TicketAnalysis], **kwargs) -> str:
        """
        Generate a sentiment analysis report.
        
        Args:
            analyses: List of ticket analyses to include in the report
            **kwargs: Additional arguments (title, format, etc.)
            
        Returns:
            Report text
        """
        title = kwargs.get('title', "Sentiment Analysis Report")
        
        # Calculate sentiment distribution
        sentiment_distribution = self.calculate_sentiment_distribution(analyses)
        
        # Calculate priority distribution
        priority_distribution = self.calculate_priority_distribution(analyses)
        
        # Calculate business impact count
        business_impact_count = self.calculate_business_impact_count(analyses)
        
        # Build the report
        report = f"{title}\n"
        report += f"{'-' * len(title)}\n\n"
        
        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total tickets analyzed: {len(analyses)}\n\n"
        
        # Sentiment distribution section
        report += "Sentiment Distribution:\n"
        for sentiment, count in sentiment_distribution.items():
            percentage = (count / len(analyses)) * 100 if analyses else 0
            report += f"  - {sentiment.capitalize()}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Priority distribution section
        report += "Priority Distribution:\n"
        for score, count in sorted(priority_distribution.items(), reverse=True):
            percentage = (count / len(analyses)) * 100 if analyses else 0
            priority_level = "High" if score >= 7 else "Medium" if score >= 4 else "Low"
            report += f"  - Score {score} ({priority_level}): {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Business impact section
        if business_impact_count > 0:
            percentage = (business_impact_count / len(analyses)) * 100 if analyses else 0
            report += f"Business Impact Detected: {business_impact_count} ({percentage:.1f}%)\n\n"
        
        # High priority tickets section
        high_priority_analyses = [a for a in analyses if a.priority_score >= 7]
        if high_priority_analyses:
            report += "High Priority Tickets:\n"
            for analysis in high_priority_analyses:
                report += f"  - Ticket {analysis.ticket_id}: {analysis.subject}\n"
                report += f"    Priority: {analysis.priority}, Sentiment: {analysis.sentiment.polarity}, Score: {analysis.priority_score}\n"
        
        return report
    
    def generate_multi_view_report(self, analyses: List[TicketAnalysis], view_map: Dict[int, str], title: str = "Multi-View Sentiment Analysis Report") -> str:
        """
        Generate a multi-view sentiment analysis report.
        
        Args:
            analyses: List of ticket analyses to include in the report
            view_map: Dictionary mapping view IDs to view names
            title: Report title
            
        Returns:
            Report text
        """
        # Group analyses by view
        analyses_by_view: Dict[int, List[TicketAnalysis]] = {}
        for analysis in analyses:
            if analysis.source_view_id is not None:
                if analysis.source_view_id not in analyses_by_view:
                    analyses_by_view[analysis.source_view_id] = []
                analyses_by_view[analysis.source_view_id].append(analysis)
        
        # Build the report
        report = f"{title}\n"
        report += f"{'-' * len(title)}\n\n"
        
        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total views: {len(analyses_by_view)}\n"
        report += f"Total tickets analyzed: {len(analyses)}\n\n"
        
        # Overall sentiment distribution
        sentiment_distribution = self.calculate_sentiment_distribution(analyses)
        
        report += "Overall Sentiment Distribution:\n"
        for sentiment, count in sentiment_distribution.items():
            percentage = (count / len(analyses)) * 100 if analyses else 0
            report += f"  - {sentiment.capitalize()}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Overall business impact
        business_impact_count = self.calculate_business_impact_count(analyses)
        if business_impact_count > 0:
            percentage = (business_impact_count / len(analyses)) * 100 if analyses else 0
            report += f"Business Impact Detected: {business_impact_count} ({percentage:.1f}%)\n\n"
        
        # Report for each view
        for view_id, view_analyses in analyses_by_view.items():
            view_name = view_map.get(view_id, f"View {view_id}")
            
            report += f"View: {view_name}\n"
            report += f"{'-' * (len(view_name) + 6)}\n"
            report += f"Tickets analyzed: {len(view_analyses)}\n\n"
            
            # Sentiment distribution for this view
            view_sentiment_distribution = self.calculate_sentiment_distribution(view_analyses)
            
            report += "Sentiment Distribution:\n"
            for sentiment, count in view_sentiment_distribution.items():
                percentage = (count / len(view_analyses)) * 100 if view_analyses else 0
                report += f"  - {sentiment.capitalize()}: {count} ({percentage:.1f}%)\n"
            
            # Business impact for this view
            view_business_impact_count = self.calculate_business_impact_count(view_analyses)
            if view_business_impact_count > 0:
                percentage = (view_business_impact_count / len(view_analyses)) * 100 if view_analyses else 0
                report += f"Business Impact Detected: {view_business_impact_count} ({percentage:.1f}%)\n"
            
            report += "\n"
        
        return report
    
    def calculate_sentiment_distribution(self, analyses: List[TicketAnalysis]) -> Dict[str, int]:
        """
        Calculate sentiment distribution.
        
        Args:
            analyses: List of ticket analyses
            
        Returns:
            Dictionary mapping sentiment polarities to counts
        """
        distribution = {"positive": 0, "negative": 0, "neutral": 0, "unknown": 0}
        
        for analysis in analyses:
            polarity = analysis.sentiment.polarity
            distribution[polarity] = distribution.get(polarity, 0) + 1
        
        return distribution
    
    def calculate_priority_distribution(self, analyses: List[TicketAnalysis]) -> Dict[int, int]:
        """
        Calculate priority distribution.
        
        Args:
            analyses: List of ticket analyses
            
        Returns:
            Dictionary mapping priority scores to counts
        """
        distribution: Dict[int, int] = {}
        
        for analysis in analyses:
            score = analysis.priority_score
            distribution[score] = distribution.get(score, 0) + 1
        
        return distribution
    
    def calculate_business_impact_count(self, analyses: List[TicketAnalysis]) -> int:
        """
        Calculate the number of tickets with business impact.
        
        Args:
            analyses: List of ticket analyses
            
        Returns:
            Count of tickets with business impact
        """
        return sum(1 for a in analyses if a.has_business_impact)
    
    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """
        Save a report to a file.
        
        Args:
            report: Report text
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to the saved report file
        """
        if not filename:
            # Generate a filename based on the current date and time
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            # Always use .txt extension for default text reports
            filename = f"sentiment_report_{timestamp}.txt"
        
        try:
            # Ensure the reports directory exists
            reports_dir = os.environ.get("REPORTS_DIR", "reports")
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # Save the report to the file
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"Saved report to {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error saving report to {filename}: {str(e)}")
            
            # Try to save in the current directory as a fallback
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                
                logger.info(f"Saved report to {filename} in current directory")
                
                return filename
            except Exception as e2:
                logger.error(f"Error saving report to current directory: {str(e2)}")
                return ""
