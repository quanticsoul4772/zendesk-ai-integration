"""
Function to analyze and update a Zendesk ticket with AI analysis results.
This modified version DOES NOT add comments to tickets, only tags.
"""

import logging
from zenpy.lib.api_objects import Ticket

# Import AI services
from ai_service import analyze_ticket_content as basic_analyze_ticket_content
from enhanced_sentiment import enhanced_analyze_ticket_content

# MongoDB support
from mongodb_helper import insert_ticket_analysis

# Exponential backoff for API retries and Zendesk client
from zendesk_ai_app import exponential_backoff_retry, get_zendesk_client

# Setup logging
logger = logging.getLogger(__name__)

def analyze_and_update_ticket(ticket: Ticket, use_enhanced_sentiment=True):
    """
    Analyze ticket content and update the ticket with AI classification.
    NO COMMENTS will be added to tickets, only tags.
    
    Args:
        ticket: The Zendesk ticket to analyze and update
        use_enhanced_sentiment: Whether to use enhanced sentiment analysis
        
    Returns:
        The AI analysis result
    """
    try:
        description = ticket.description or ""
        
        # Use the enhanced AI service if requested, otherwise use the basic one
        if use_enhanced_sentiment:
            ai_result = enhanced_analyze_ticket_content(description)
            
            # Extract enhanced sentiment information
            sentiment_data = ai_result.get("sentiment", {})
            sentiment_polarity = sentiment_data.get("polarity", "unknown")
            urgency_level = sentiment_data.get("urgency_level", 0)
            frustration_level = sentiment_data.get("frustration_level", 0)
            priority_score = ai_result.get("priority_score", 0)
            
            category = ai_result.get("category", "general_inquiry")
            component = ai_result.get("component", "none")
            key_phrases = ai_result.get("key_phrases", [])
            detected_emotions = ai_result.get("emotions", [])
            business_impact = ai_result.get("business_impact", "None detected")
            tech_expertise = ai_result.get("technical_expertise", 0)
            
            # Prepare tags to add
            tags_to_add = []
            
            # Add category tag if not already present
            if category not in ticket.tags:
                tags_to_add.append(category)
            
            # Add component tag if not "none" and not already present
            if component != "none" and component not in ticket.tags:
                tags_to_add.append(component)
            
            # Add sentiment tag
            if f"sentiment_{sentiment_polarity}" not in ticket.tags:
                tags_to_add.append(f"sentiment_{sentiment_polarity}")
            
            # Add urgency tag based on urgency level
            if urgency_level >= 4 and "urgency_high" not in ticket.tags:
                tags_to_add.append("urgency_high")
            elif urgency_level >= 2 and "urgency_medium" not in ticket.tags:
                tags_to_add.append("urgency_medium")
            
            # Add frustration tag based on frustration level
            if frustration_level >= 4 and "frustration_high" not in ticket.tags:
                tags_to_add.append("frustration_high")
            elif frustration_level >= 2 and "frustration_medium" not in ticket.tags:
                tags_to_add.append("frustration_medium")
            
            # Add business impact tag if detected
            if sentiment_data.get("business_impact", {}).get("detected", False) and "business_impact" not in ticket.tags:
                tags_to_add.append("business_impact")
                
            # Add priority tag based on priority score
            if priority_score >= 8 and "priority_high" not in ticket.tags:
                tags_to_add.append("priority_high")
            elif priority_score >= 5 and "priority_medium" not in ticket.tags:
                tags_to_add.append("priority_medium")
            
            # Add all tags
            for tag in tags_to_add:
                ticket.tags.append(tag)
                
            # NO COMMENTS ADDED TO TICKET
            
            # Update the ticket in Zendesk
            zenpy_client = get_zendesk_client()
            exponential_backoff_retry(zenpy_client.tickets.update, ticket)
            logger.info(f"Updated ticket #{ticket.id} with enhanced sentiment analysis - priority={priority_score}/10")
            
            # Store the analysis for reporting purposes
            store_ticket_analysis(
                ticket_id=ticket.id,
                subject=ticket.subject,
                category=category,
                component=component,
                sentiment=sentiment_polarity,
                priority_score=priority_score,
                urgency_level=urgency_level,
                frustration_level=frustration_level,
                business_impact=business_impact,
                technical_expertise=tech_expertise,
                key_phrases=key_phrases,
                emotions=detected_emotions,
                use_enhanced=True
            )
            
            return ai_result
        else:
            # Basic sentiment analysis
            ai_result = basic_analyze_ticket_content(description)
            
            category = ai_result.get("category", "general_inquiry")
            component = ai_result.get("component", "none")
            sentiment = ai_result.get("sentiment", "unknown")
            confidence = ai_result.get("confidence", 0.0)
            
            # Prepare tags to add
            tags_to_add = []
            
            # Add category tag if not already present
            if category not in ticket.tags:
                tags_to_add.append(category)
            
            # Add sentiment tag
            if f"sentiment_{sentiment}" not in ticket.tags:
                tags_to_add.append(f"sentiment_{sentiment}")
            
            # Add component tag if not "none"
            if component != "none" and component not in ticket.tags:
                tags_to_add.append(component)
            
            # Add all tags
            for tag in tags_to_add:
                ticket.tags.append(tag)
            
            # NO COMMENTS ADDED TO TICKET
            
            # Update the ticket in Zendesk
            zenpy_client = get_zendesk_client()
            exponential_backoff_retry(zenpy_client.tickets.update, ticket)
            logger.info(f"Updated ticket #{ticket.id} - category={category}, component={component}, sentiment={sentiment}")
            
            # Store analysis in MongoDB
            store_ticket_analysis(
                ticket_id=ticket.id,
                subject=ticket.subject,
                category=category,
                component=component,
                sentiment=sentiment,
                confidence=confidence,
                use_enhanced=False
            )
            
            return ai_result
    except Exception as e:
        logger.error(f"Error analyzing ticket #{ticket.id}: {e}")
        return None

def store_ticket_analysis(ticket_id, subject, category, component, sentiment, confidence=None, priority_score=None, 
                         urgency_level=None, frustration_level=None, business_impact=None, technical_expertise=None,
                         key_phrases=None, emotions=None, use_enhanced=False):
    """Store ticket analysis data in MongoDB."""
    try:
        from datetime import datetime
        
        analysis_data = {
            "ticket_id": ticket_id,
            "subject": subject,
            "category": category,
            "component": component,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow(),
            "use_enhanced": use_enhanced
        }
        
        # Add basic sentiment fields
        if confidence is not None:
            analysis_data["confidence"] = confidence
        
        # Add enhanced sentiment fields if available
        if use_enhanced:
            analysis_data["priority_score"] = priority_score
            analysis_data["urgency_level"] = urgency_level
            analysis_data["frustration_level"] = frustration_level
            analysis_data["business_impact"] = business_impact
            analysis_data["technical_expertise"] = technical_expertise
            analysis_data["key_phrases"] = key_phrases or []
            analysis_data["emotions"] = emotions or []
        
        # Insert into MongoDB
        insert_ticket_analysis(analysis_data)
        logger.info(f"Stored {'enhanced' if use_enhanced else 'basic'} analysis for ticket #{ticket_id}")
    except Exception as e:
        logger.error(f"Error storing ticket analysis: {e}")
