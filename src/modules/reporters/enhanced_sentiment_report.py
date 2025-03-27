"""
Enhanced Sentiment Report Module

This module generates more intuitive reports with descriptive labels
for sentiment analysis results.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

# Set up logging
logger = logging.getLogger(__name__)

class EnhancedSentimentReporter:
    """Generates enhanced reports focused on sentiment analysis results."""
    
    def __init__(self, db_repository=None):
        """Initialize the reporter."""
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
    
    def generate_report(self, analyses: List[Dict], title: Optional[str] = None) -> str:
        """
        Generate an enhanced sentiment analysis report with descriptive labels.
        
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
        report += f"ENHANCED SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        # Executive Summary section
        report += self._generate_executive_summary(analyses)
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Business impact first (since it's most critical)
        business_impact_count = self._count_business_impact(analyses)
        report += "BUSINESS IMPACT\n--------------\n"
        report += "A ticket is flagged as having business impact when it indicates:\n"
        report += "- Production system downtime (non-functional systems)\n"
        report += "- Revenue loss (financial impact)\n"
        report += "- Missed deadlines (time-sensitive deliverables at risk)\n"
        report += "- Customer-facing issues (visible to clients)\n"
        report += "- Contractual obligations at risk (legal/agreement compliance)\n\n"
        report += f"Tickets with business impact: {business_impact_count}\n"
        impact_percentage = (business_impact_count / len(analyses)) * 100
        report += f"Percentage of total: {impact_percentage:.2f}%\n"
        if impact_percentage > 75:
            report += f"ALERT: High percentage of tickets have business impact!\n"
            report += "This indicates a significant number of tickets are affecting core business operations.\n"
        report += "\n"
        
        # Priority score distribution with grouped scores
        report += self._generate_priority_distribution(analyses)
        
        # Urgency distribution with descriptive labels
        report += self._generate_urgency_distribution(analyses)
        
        # Frustration distribution with descriptive labels
        report += self._generate_frustration_distribution(analyses)
        
        # Sentiment distribution
        polarity_counts = self._count_sentiment_polarities(analyses)
        report += "SENTIMENT DISTRIBUTION\n--------------------\n"
        for polarity, count in sorted(polarity_counts.items()):
            percentage = (count / len(analyses)) * 100
            report += f"{polarity}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Component distribution (top first)
        component_counts = self._count_components(analyses)
        if component_counts:
            report += "TOP AFFECTED COMPONENTS\n---------------------\n"
            # Sort by count descending, exclude 'none'
            sorted_components = {k: v for k, v in sorted(
                component_counts.items(), 
                key=lambda item: item[1], 
                reverse=True
            ) if k != "none"}
            
            # Calculate the total number of components (excluding 'none')
            total_components = sum(sorted_components.values())
            
            # Show all components with percentages
            for component, count in sorted_components.items():
                if total_components > 0:
                    percentage = (count / total_components) * 100
                    report += f"{component}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Category distribution
        category_counts = self._count_categories(analyses)
        report += "CATEGORY DISTRIBUTION\n--------------------\n"
        # Sort by count descending
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        total_tickets = len(analyses)
        for category, count in sorted_categories:
            percentage = (count / total_tickets) * 100
            report += f"{category}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Calculate and show averages
        avg_urgency = self._calculate_average_urgency(analyses)
        avg_frustration = self._calculate_average_frustration(analyses)
        avg_priority = self._calculate_average_priority(analyses)
        
        report += "AVERAGES\n--------\n"
        
        # For urgency, show average and interpretation
        report += f"Average Urgency Level: {avg_urgency:.2f}/5"
        if avg_urgency >= 4:
            report += " (Requires Prompt Resolution)"
        elif avg_urgency >= 3:
            report += " (Moderately Urgent)"
        else:
            report += " (Low Urgency)"
        report += "\n"
        
        # For frustration, show average and interpretation
        report += f"Average Frustration Level: {avg_frustration:.2f}/5"
        if avg_frustration >= 4:
            report += " (High Customer Frustration)"
        elif avg_frustration >= 3:
            report += " (Noticeable Frustration)"
        else:
            report += " (Low Frustration)"
        report += "\n"
        
        # For priority, show average and interpretation
        report += f"Average Priority Score: {avg_priority:.2f}/10"
        if avg_priority >= 8:
            report += " (Critical Priority)"
        elif avg_priority >= 6:
            report += " (High Priority)"
        elif avg_priority >= 4:
            report += " (Medium Priority)"
        else:
            report += " (Low Priority)"
        report += "\n\n"
        
        # Ticket age distribution (if available)
        age_distribution = self._calculate_age_distribution(analyses)
        if age_distribution:
            report += "TICKET AGE DISTRIBUTION\n---------------------\n"
            for age_range, count in age_distribution.items():
                report += f"{age_range}: {count}\n"
            report += "\n"
        
        # High priority tickets
        high_priority_tickets = self._get_high_priority_tickets(analyses)
        if high_priority_tickets:
            report += "HIGH PRIORITY TICKETS\n-------------------\n"
            report += "These tickets require immediate attention based on their priority score:\n\n"
            for analysis in high_priority_tickets:
                ticket_id = analysis.get("ticket_id", "Unknown")
                subject = analysis.get("subject", "No Subject")
                priority = analysis.get("priority_score", 0)
                
                # Determine priority label
                priority_label = "Unknown"
                for label, (min_val, max_val) in self.priority_groups.items():
                    if min_val <= priority <= max_val:
                        priority_label = label
                        break
                
                report += f"#{ticket_id} - {subject} (Priority: {priority}/10 - {priority_label})\n"
            report += "\n"
        
        # Business impact tickets
        business_impact_tickets = self._get_business_impact_tickets(analyses)
        if business_impact_tickets:
            report += "BUSINESS IMPACT TICKETS\n----------------------\n"
            report += "These tickets have critical business impact that may affect production systems, revenue, or deadlines:\n\n"
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
    
    def _generate_executive_summary(self, analyses: List[Dict]) -> str:
        """Generate an executive summary section for the report."""
        business_impact_count = self._count_business_impact(analyses)
        business_impact_percentage = (business_impact_count / len(analyses)) * 100
        
        # Count high priority tickets (7-10)
        priority_counts = self._count_priority_scores(analyses)
        high_priority_count = sum(count for score, count in priority_counts.items() if score >= 7)
        high_priority_percentage = (high_priority_count / len(analyses)) * 100
        
        # Count high urgency tickets (4-5)
        urgency_counts = self._count_urgency_levels(analyses)
        high_urgency_count = sum(count for level, count in urgency_counts.items() if level >= 4)
        high_urgency_percentage = (high_urgency_count / len(analyses)) * 100
        
        # Count high frustration tickets (4-5)
        frustration_counts = self._count_frustration_levels(analyses)
        high_frustration_count = sum(count for level, count in frustration_counts.items() if level >= 4)
        high_frustration_percentage = (high_frustration_count / len(analyses)) * 100
        
        # Build the summary
        summary = "EXECUTIVE SUMMARY\n----------------\n"
        
        if business_impact_count > 0:
            summary += f"Business Impact: {business_impact_count} of {len(analyses)} tickets ({business_impact_percentage:.1f}%) affect business operations\n"
            summary += "These tickets indicate system downtime, revenue impact, missed deadlines, or contract risks\n"
        
        if high_priority_count > 0:
            summary += f"High Priority Items: {high_priority_count} tickets ({high_priority_percentage:.1f}%) are high priority (scores 7-10)\n"
        
        if high_urgency_count > 0:
            summary += f"Urgency Alert: {high_urgency_count} tickets ({high_urgency_percentage:.1f}%) require prompt resolution (Levels 4-5)\n"
        
        if high_frustration_count > 0:
            summary += f"Customer Satisfaction Risk: {high_frustration_count} customers ({high_frustration_percentage:.1f}%) are highly frustrated (Levels 4-5)\n"
        
        summary += "\n"
        return summary
    
    def _generate_priority_distribution(self, analyses: List[Dict]) -> str:
        """Generate a priority score distribution section with grouped scores."""
        priority_counts = self._count_priority_scores(analyses)
        
        # Group scores
        grouped_counts = {}
        for group_name, (min_val, max_val) in self.priority_groups.items():
            group_count = sum(count for score, count in priority_counts.items() if min_val <= score <= max_val)
            grouped_counts[group_name] = group_count
        
        # Build the priority distribution section
        section = "PRIORITY SCORE DISTRIBUTION\n--------------------------\n"
        
        # Add a priority scoring system explanation
        section += "PRIORITY SCORING SYSTEM\n" + "-" * 22 + "\n"
        section += "Our system scores tickets from 1-10 based on urgency, frustration, business impact and technical expertise:\n\n"
        section += "10 = Critical Emergency (Immediate action required, major business impact)\n"
        section += "8-9 = High Priority (Requires attention within 24 hours, significant impact)\n"
        section += "6-7 = Medium-High Priority (Address within 48 hours)\n"
        section += "4-5 = Medium Priority (Address within this week)\n"
        section += "1-3 = Low Priority (Address when resources permit)\n\n"
        
        # First, show the grouped counts
        section += "GROUPED PRIORITY LEVELS\n" + "-" * 22 + "\n"
        for group_name, count in grouped_counts.items():
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            section += f"{group_name}: {count} tickets ({percentage:.1f}%)\n"
        
        # Then provide a detailed breakdown sorted from highest to lowest priority
        section += "\nDETAILED PRIORITY BREAKDOWN\n" + "-" * 26 + "\n"
        
        # Get all scores that have tickets
        active_scores = [score for score, count in priority_counts.items() if count > 0]
        
        # Sort scores in descending order (highest priority first)
        for score in sorted(active_scores, reverse=True):
            count = priority_counts[score]
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            description = self.priority_descriptions.get(score, "Unknown priority level")
            section += f"Score {score} ({description}): {count} tickets ({percentage:.1f}%)\n"
        
        # Add explanation for missing scores
        all_scores = set(range(1, 11))
        missing_scores = all_scores - set(active_scores)
        if missing_scores:
            missing_str = ", ".join(str(s) for s in sorted(missing_scores))
            section += f"\nNo tickets with scores {missing_str} in current dataset\n"
        
        # Add summary/alert if significant percentage is high priority
        high_priority_count = grouped_counts.get("High Priority", 0) + grouped_counts.get("Critical Priority", 0)
        high_priority_percentage = (high_priority_count / len(analyses)) * 100 if len(analyses) > 0 else 0
        
        if high_priority_percentage >= 50:
            section += f"\nALERT: {high_priority_percentage:.1f}% of tickets are High or Critical Priority\n"
            section += "This indicates a significant number of tickets requiring immediate attention.\n"
        
        section += "\n"
        return section
    
    def _generate_urgency_distribution(self, analyses: List[Dict]) -> str:
        """Generate an urgency level distribution section with descriptive labels."""
        urgency_counts = self._count_urgency_levels(analyses)
        
        section = "URGENCY LEVEL DISTRIBUTION\n------------------------\n"
        
        for level, count in sorted(urgency_counts.items()):
            label = self.urgency_labels.get(level, "Unknown level")
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            section += f"Level {level} ({label}): {count} ({percentage:.1f}%)\n"
        
        # Add summary with highest urgency level
        highest_urgency_level = max(urgency_counts.items(), key=lambda x: x[0] if x[1] > 0 else 0)[0] if urgency_counts else 0
        if highest_urgency_level >= 4:
            highest_count = urgency_counts.get(highest_urgency_level, 0)
            highest_percentage = (highest_count / len(analyses)) * 100 if len(analyses) > 0 else 0
            section += f"\nSUMMARY: {highest_percentage:.1f}% of tickets require PROMPT RESOLUTION (Level {highest_urgency_level})\n"
        
        section += "\n"
        return section
    
    def _generate_frustration_distribution(self, analyses: List[Dict]) -> str:
        """Generate a frustration level distribution section with descriptive labels."""
        frustration_counts = self._count_frustration_levels(analyses)
        
        section = "FRUSTRATION LEVEL DISTRIBUTION\n----------------------------\n"
        
        for level, count in sorted(frustration_counts.items()):
            label = self.frustration_labels.get(level, "Unknown level")
            percentage = (count / len(analyses)) * 100 if len(analyses) > 0 else 0
            section += f"Level {level} ({label}): {count} ({percentage:.1f}%)\n"
        
        # Add summary with highest frustration level
        highest_frustration_level = max(frustration_counts.items(), key=lambda x: x[0] if x[1] > 0 else 0)[0] if frustration_counts else 0
        if highest_frustration_level >= 4:
            highest_count = frustration_counts.get(highest_frustration_level, 0)
            highest_percentage = (highest_count / len(analyses)) * 100 if len(analyses) > 0 else 0
            section += f"\nSUMMARY: {highest_percentage:.1f}% of customers are HIGHLY FRUSTRATED (Level {highest_frustration_level})\n"
        
        section += "\n"
        return section
    
    def _calculate_age_distribution(self, analyses: List[Dict]) -> Dict[str, int]:
        """Calculate the age distribution of tickets."""
        # Skip if "created_at" is not available in the analyses
        if not analyses or "created_at" not in analyses[0]:
            return {}
        
        age_counts = {
            "New (0-1 days)": 0,
            "Active (2-7 days)": 0,
            "Aging (8-14 days)": 0,
            "At Risk (15+ days)": 0
        }
        
        now = datetime.now()
        
        for analysis in analyses:
            created_at = analysis.get("created_at")
            
            # Skip if created_at is not available
            if not created_at:
                continue
            
            # Convert to datetime if it's a string
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
            
            # Calculate age in days
            delta = now - created_at
            age_days = delta.days
            
            # Assign to appropriate bucket
            if age_days <= 1:
                age_counts["New (0-1 days)"] += 1
            elif age_days <= 7:
                age_counts["Active (2-7 days)"] += 1
            elif age_days <= 14:
                age_counts["Aging (8-14 days)"] += 1
            else:
                age_counts["At Risk (15+ days)"] += 1
        
        return age_counts
    
    def generate_multi_view_report(self, analyses: List[Dict], view_map: Dict = None, title: Optional[str] = None) -> str:
        """
        Generate an enhanced sentiment analysis report for tickets from multiple views.
        
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
        report += f"ENHANCED MULTI-VIEW SENTIMENT ANALYSIS REPORT ({now.strftime('%Y-%m-%d %H:%M')})\n"
        report += f"{'='*60}\n\n"
        
        # Executive Summary for all views combined
        report += self._generate_executive_summary(analyses)
        
        if title:
            report += f"{title}\n{'-' * len(title)}\n\n"
        
        # Overview section
        report += "OVERVIEW\n--------\n"
        report += f"Total Tickets Analyzed: {len(analyses)}\n"
        report += f"Total Views: {len(view_analyses)}\n\n"
        
        # Views summary section with percentages
        report += "TICKETS BY VIEW\n--------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            percentage = (len(view_tickets) / len(analyses)) * 100
            report += f"{view_name}: {len(view_tickets)} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Combined sentiment analysis
        report += "COMBINED SENTIMENT ANALYSIS\n-------------------------\n"
        
        # Business impact first
        business_impact_count = self._count_business_impact(analyses)
        report += "Business Impact:\n"
        report += "A ticket is flagged as having business impact when it indicates:\n"
        report += "- Production system downtime (non-functional systems)\n"
        report += "- Revenue loss (financial impact)\n"
        report += "- Missed deadlines (time-sensitive deliverables at risk)\n"
        report += "- Customer-facing issues (visible to clients)\n"
        report += "- Contractual obligations at risk (legal/agreement compliance)\n\n"
        report += f"Tickets with business impact: {business_impact_count}\n"
        impact_percentage = (business_impact_count / len(analyses)) * 100
        report += f"Percentage of total: {impact_percentage:.2f}%\n"
        if impact_percentage > 75:
            report += f"ALERT: High percentage of tickets have business impact!\n"
            report += "This indicates a significant number of tickets are affecting core business operations.\n"
        report += "\n"
        
        # Sentiment distribution
        polarity_counts = self._count_sentiment_polarities(analyses)
        report += "Sentiment Distribution:\n"
        for polarity, count in sorted(polarity_counts.items()):
            percentage = (count / len(analyses)) * 100
            report += f"{polarity}: {count} ({percentage:.1f}%)\n"
        report += "\n"
        
        # Priority distribution with groups
        report += "Priority Distribution:\n"
        report += "Our system scores tickets from 1-10 based on urgency, frustration, business impact and technical expertise:\n"
        priority_counts = self._count_priority_scores(analyses)
        
        # Group scores
        grouped_counts = {}
        for group_name, (min_val, max_val) in self.priority_groups.items():
            group_count = sum(count for score, count in priority_counts.items() if min_val <= score <= max_val)
            if group_count > 0:
                percentage = (group_count / len(analyses)) * 100
                grouped_counts[group_name] = (group_count, percentage)
        
        # Show grouped counts
        for group_name, (count, percentage) in grouped_counts.items():
            report += f"{group_name}: {count} tickets ({percentage:.1f}%)\n"
        
        # Get active scores
        active_scores = [score for score, count in priority_counts.items() if count > 0]
        
        # Add details for highest priority scores (top 3)
        if active_scores:
            report += "\nHighest priority tickets:\n"
            for score in sorted(active_scores, reverse=True)[:3]:  # Show top 3 highest priority scores
                count = priority_counts[score]
                percentage = (count / len(analyses)) * 100
                description = self.priority_descriptions.get(score, "Unknown priority level")
                report += f"Score {score} ({description}): {count} tickets ({percentage:.1f}%)\n"
        report += "\n"
        
        # Calculate averages
        avg_urgency = self._calculate_average_urgency(analyses)
        avg_frustration = self._calculate_average_frustration(analyses)
        avg_priority = self._calculate_average_priority(analyses)
        
        report += "Averages:\n"
        report += f"Average Urgency Level: {avg_urgency:.2f}/5\n"
        report += f"Average Frustration Level: {avg_frustration:.2f}/5\n"
        report += f"Average Priority Score: {avg_priority:.2f}/10\n\n"
        
        # Component distribution (if available)
        component_counts = self._count_components(analyses)
        if component_counts:
            sorted_components = {k: v for k, v in sorted(
                component_counts.items(), 
                key=lambda item: item[1], 
                reverse=True
            ) if k != "none" and v > 0}
            
            if sorted_components:
                report += "Top Components:\n"
                for component, count in list(sorted_components.items())[:5]:  # Show top 5
                    percentage = (count / sum(sorted_components.values())) * 100
                    report += f"{component}: {count} ({percentage:.1f}%)\n"
                report += "\n"
        
        # Per-view sentiment analysis
        report += "PER-VIEW SENTIMENT ANALYSIS\n--------------------------\n"
        for view_id, view_tickets in view_analyses.items():
            view_name = view_map.get(view_id, f"View ID: {view_id}") if view_map else f"View ID: {view_id}"
            report += f"\n{view_name}\n{'-' * len(view_name)}\n"
            
            # Get sentiment distribution for this view
            polarity_counts = self._count_sentiment_polarities(view_tickets)
            report += "Sentiment Distribution:\n"
            for polarity, count in sorted(polarity_counts.items()):
                percentage = (count / len(view_tickets)) * 100 if view_tickets else 0
                report += f"  {polarity}: {count} ({percentage:.1f}%)\n"
            
            # Get priority distribution for this view
            priority_counts = self._count_priority_scores(view_tickets)
            
            # Group by priority levels
            high_priority = sum(count for score, count in priority_counts.items() if score >= 7)
            high_percentage = (high_priority / len(view_tickets)) * 100 if view_tickets else 0
            report += f"High Priority Tickets (7-10): {high_priority} ({high_percentage:.1f}%)\n"
            
            # Get business impact for this view
            business_impact_count = self._count_business_impact(view_tickets)
            impact_percentage = (business_impact_count / len(view_tickets)) * 100 if view_tickets else 0
            report += f"Business Impact Tickets: {business_impact_count} ({impact_percentage:.1f}%)\n"
            
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
            filename = f"enhanced_sentiment_report_{timestamp}.txt"
        
        try:
            with open(filename, "w") as file:
                file.write(report)
            logger.info(f"Enhanced sentiment analysis report saved to {filename}")
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
            title = f"Enhanced Sentiment Analysis Report - {period_name}"
            
        return self.generate_report(analyses, title)
