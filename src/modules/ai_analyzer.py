"""
AI Analyzer Module

This module is responsible for analyzing ticket content using AI services.
It handles both basic and enhanced sentiment analysis.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

# Import AI services with absolute imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import both OpenAI and Claude services
from ai_service import analyze_ticket_content as openai_analyze_ticket_content
from enhanced_sentiment import enhanced_analyze_ticket_content as openai_enhanced_analyze_ticket_content

# Import Claude services
from claude_service import analyze_ticket_content as claude_analyze_ticket_content
from claude_enhanced_sentiment import enhanced_analyze_ticket_content as claude_enhanced_analyze_ticket_content

# Set up logging
logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    Handles AI analysis of support ticket content.
    """
    
    def analyze_ticket(self, ticket_id: str, subject: str, description: str, 
                      use_enhanced: bool = True, use_claude: bool = True) -> Dict[str, Any]:
        """
        Analyze ticket content using AI.
        
        Args:
            ticket_id: ID of the ticket being analyzed
            subject: Ticket subject
            description: Ticket description/content
            use_enhanced: Whether to use enhanced sentiment analysis
            
        Returns:
            Dictionary with analysis results
        """
        # Combine subject and description for analysis
        content = f"{subject}\n\n{description}"
        
        # Perform analysis based on chosen method and service
        try:
            # Choose between Claude and OpenAI
            if use_claude:
                logger.info(f"Using Claude for analysis of ticket {ticket_id}")
                if use_enhanced:
                    analysis = claude_enhanced_analyze_ticket_content(content)
                else:
                    analysis = claude_analyze_ticket_content(content)
            else:
                logger.info(f"Using OpenAI for analysis of ticket {ticket_id}")
                if use_enhanced:
                    analysis = openai_enhanced_analyze_ticket_content(content)
                else:
                    analysis = openai_analyze_ticket_content(content)
            
            # Add ticket reference to the analysis
            analysis["ticket_id"] = ticket_id
            analysis["subject"] = subject
            analysis["timestamp"] = datetime.utcnow()
            
            logger.info(f"Successfully analyzed ticket {ticket_id}")
            return analysis
            
        except Exception as e:
            logger.exception(f"Error analyzing ticket {ticket_id}: {e}")
            return self._create_error_analysis(ticket_id, subject, str(e))
    
    def _create_error_analysis(self, ticket_id: str, subject: str, error: str) -> Dict[str, Any]:
        """Create an analysis result for error cases."""
        return {
            "ticket_id": ticket_id,
            "subject": subject,
            "timestamp": datetime.utcnow(),
            "sentiment": "unknown",
            "category": "uncategorized",
            "component": "none",
            "confidence": 0.0,
            "error": error,
            "error_type": "AnalysisError"
        }
    
    # Tag extraction method removed - no longer modifying tickets
    
    def format_analysis_for_display(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results for human-readable display in reports and console output.
        
        Args:
            analysis: Analysis results dictionary
        
        Returns:
            Formatted text representation of the analysis.
        """
        comment = "AI Analysis Results:\n\n"
        
        # Add sentiment information
        if "sentiment" in analysis:
            if isinstance(analysis["sentiment"], dict):
                # Enhanced sentiment
                comment += "Sentiment Analysis:\n"
                comment += f"- Polarity: {analysis['sentiment'].get('polarity', 'unknown')}\n"
                comment += f"- Urgency Level: {analysis['sentiment'].get('urgency_level', 'n/a')}/5\n"
                comment += f"- Frustration Level: {analysis['sentiment'].get('frustration_level', 'n/a')}/5\n"
                
                # Business impact
                business_impact = analysis['sentiment'].get('business_impact', {})
                if business_impact and business_impact.get('detected', False):
                    comment += f"- Business Impact: {business_impact.get('description', 'Detected')}\n"
                
                # Emotions
                emotions = analysis['sentiment'].get('emotions', [])
                if emotions:
                    comment += f"- Emotions: {', '.join(emotions)}\n"
                    
                comment += f"- Priority Score: {analysis.get('priority_score', 'n/a')}/10\n"
            else:
                # Basic sentiment
                comment += f"Sentiment: {analysis['sentiment']}\n"
        
        # Add category and component
        comment += f"Category: {analysis.get('category', 'uncategorized')}\n"
        
        if "component" in analysis and analysis["component"] != "none":
            comment += f"Hardware Component: {analysis['component']}\n"
        
        return comment
