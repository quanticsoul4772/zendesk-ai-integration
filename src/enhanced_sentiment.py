"""
Enhanced Sentiment Analysis module for Zendesk integration.

This module provides more detailed sentiment analysis capabilities beyond basic
positive/negative classification, including urgency detection, frustration levels,
technical expertise assessment, and business impact detection.
"""

import os
import time
import logging
import json
from typing import Dict, Any, Optional, List, Union

# Import the base AI service functionality
from ai_service import call_openai_with_retries, AIServiceError

# Set up logging
logger = logging.getLogger(__name__)

def create_default_sentiment_response(error_message=""):
    """
    Create a default response for when sentiment analysis fails.
    
    Args:
        error_message: Optional error message
        
    Returns:
        Dict with default sentiment values
    """
    return {
        "sentiment": {
            "polarity": "unknown",
            "urgency_level": 1,
            "frustration_level": 1,
            "technical_expertise": 1,
            "business_impact": {
                "detected": False,
                "description": ""
            },
            "key_phrases": [],
            "emotions": []
        },
        "category": "uncategorized",
        "component": "none",
        "priority_score": 1,
        "confidence": 0.0,
        "error": error_message,
        "error_type": "EmptyContentError" if not error_message else "EnhancedSentimentError"
    }

def calculate_priority_score(sentiment_data: Dict) -> int:
    """
    Calculate an overall priority score based on sentiment metrics.
    Returns a score from 1-10 where higher means higher priority.
    
    Args:
        sentiment_data: Dictionary with sentiment analysis data
        
    Returns:
        Priority score from 1-10
    """
    # Base weights for each factor
    weights = {
        "urgency": 0.35,
        "frustration": 0.30,
        "business_impact": 0.25,
        "technical_expertise": 0.10
    }
    
    # Convert sentiment data to scores
    urgency_score = sentiment_data.get("urgency_level", 1)  # 1-5
    frustration_score = sentiment_data.get("frustration_level", 1)  # 1-5
    
    # Business impact is binary but with higher weight if detected
    business_impact_score = 5 if sentiment_data.get("business_impact", {}).get("detected", False) else 0
    
    # Technical expertise (inverse relationship - less technical customers may need more help)
    technical_expertise = sentiment_data.get("technical_expertise", 3)  # 1-5
    technical_score = max(1, 6 - technical_expertise)  # Invert: 5->1, 4->2, 3->3, 2->4, 1->5
    
    # Calculate weighted score
    weighted_score = (
        weights["urgency"] * urgency_score +
        weights["frustration"] * frustration_score +
        weights["business_impact"] * business_impact_score + 
        weights["technical_expertise"] * technical_score
    )
    
    # Convert to 1-10 scale
    priority_score = min(10, max(1, round(weighted_score * 2)))
    
    return priority_score

def enhanced_analyze_ticket_content(content: str) -> Dict[str, Any]:
    """
    Enhanced ticket content analysis with detailed sentiment metrics.
    
    This function provides more nuanced analysis including:
    - Urgency detection
    - Frustration level assessment
    - Technical expertise estimation
    - Business impact detection
    - Key phrases identification
    - Emotion detection
    - Priority score calculation
    
    Args:
        content: The ticket content to analyze
        
    Returns:
        Dict with detailed sentiment metrics, category, component, priority score, and confidence
    """
    if not content or not content.strip():
        return create_default_sentiment_response("Empty content provided")
        
    try:
        logger.info(f"Performing enhanced sentiment analysis (content length: {len(content)} chars)")
        
        # Enhanced prompt with examples
        prompt = f"""
        Analyze this hardware support ticket and return detailed sentiment analysis in JSON format:
        
        TICKET CONTENT:
        {content}
        
        RETURN JSON WITH:
        1) "sentiment": A dictionary with:
           - "polarity": "positive", "negative", "neutral", or "unknown"
           - "urgency_level": 1-5 scale with examples:
              * 1: "Just checking in about my order status"
              * 2: "My system is having minor issues that aren't affecting work"
              * 3: "System is having intermittent issues impacting productivity"
              * 4: "System is down and we need it fixed very soon"
              * 5: "CRITICAL: Production system completely down, losing $10k/hour"
           - "frustration_level": 1-5 scale with examples:
              * 1: "Thanks for your assistance with my question"
              * 2: "I'd appreciate help resolving this issue"
              * 3: "I've been waiting for several days to get this resolved"
              * 4: "This is quite frustrating as I've reported this twice now"
              * 5: "This is now the THIRD time I've had to contact support about this same ISSUE!"
           - "technical_expertise": 1-5 scale with examples:
              * 1: "I'm not sure what a driver is"
              * 2: "I know how to install software but not hardware"
              * 3: "I've updated drivers and checked system logs"
              * 4: "I've tried replacing components and running diagnostics"
              * 5: "I've already analyzed the memory dumps and identified a potential IRQ conflict"
           - "business_impact": Object with "detected" (boolean) and "description" (string)
              * Examples: Production down, deadline risk, revenue loss, contract obligations
           - "key_phrases": Up to 3 phrases showing sentiment
           - "emotions": Array of detected emotions (anger, worry, satisfaction, etc.)
        
        2) "category": One of [hardware_issue, software_issue, system, technical_support, rma, general_inquiry]
        
        3) "component": One of [gpu, cpu, drive, memory, power_supply, motherboard, cooling, display, network, ipmi, bios, boot, none]
        
        4) "confidence": 0.0-1.0 reflecting your confidence in this analysis
        
        Focus on hardware support context for Exxact Corporation. Look for urgency signals such as system down, production impact, deadlines, revenue loss. Detect frustration signals like repeated contact attempts, escalation requests, strong language, excessive punctuation, and ALL CAPS text.
        
        Be very careful to differentiate between tickets with true business impact versus routine issues. Consider context clues about production environments, deadlines, and financial implications.
        """
        
        result = call_openai_with_retries(
            prompt=prompt,
            model="gpt-4o-mini",
            max_retries=3,
            temperature=0.3
        )
        
        # Extract and normalize sentiment data
        sentiment_data = result.get("sentiment", {})
        
        # Normalize sentiment polarity
        if isinstance(sentiment_data, dict):
            polarity = sentiment_data.get("polarity", "unknown").lower().replace(" ", "_")
            sentiment_data["polarity"] = polarity
        else:
            # Handle case where sentiment isn't a dictionary
            sentiment_data = {
                "polarity": "unknown",
                "urgency_level": 1,
                "frustration_level": 1,
                "technical_expertise": 1,
                "business_impact": {"detected": False, "description": ""},
                "key_phrases": [],
                "emotions": []
            }
        
        # Normalize category and component
        category = result.get("category", "general_inquiry").lower().replace(" ", "_")
        component = result.get("component", "none").lower().replace(" ", "_")
        confidence = float(result.get("confidence", 0.9))
        
        # Calculate priority score
        priority_score = calculate_priority_score(sentiment_data)
        
        logger.info(f"Enhanced analysis complete: priority={priority_score}/10, urgency={sentiment_data.get('urgency_level', 1)}/5, frustration={sentiment_data.get('frustration_level', 1)}/5")
        
        return {
            "sentiment": sentiment_data,
            "category": category,
            "component": component,
            "priority_score": priority_score,
            "confidence": confidence,
            "raw_result": result  # Include raw result for debugging
        }
        
    except AIServiceError as e:
        # Log specific AI service errors with appropriate level
        logger.error(f"AI service error in enhanced sentiment analysis: {str(e)}")
        error_response = create_default_sentiment_response(str(e))
        error_response["error_type"] = type(e).__name__
        return error_response
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error in enhanced sentiment analysis: {str(e)}")
        error_response = create_default_sentiment_response(str(e))
        error_response["error_type"] = type(e).__name__
        return error_response
