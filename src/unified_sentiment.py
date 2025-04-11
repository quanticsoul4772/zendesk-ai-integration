"""
Unified Sentiment Analysis Module

This module provides a unified interface for sentiment analysis
that works with multiple AI providers (OpenAI and Claude).
"""

import logging
from typing import Dict, Any, Optional

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
        "error_type": "EmptyContentError" if not error_message else "SentimentAnalysisError"
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

def analyze_sentiment(
    content: str,
    use_enhanced: bool = True,
    ai_provider: str = "claude",
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified sentiment analysis for ticket content.
    
    Args:
        content: The ticket content to analyze
        use_enhanced: Whether to use enhanced sentiment analysis
        ai_provider: AI provider to use ("openai" or "claude")
        model: Specific model to use
        api_key: Optional API key
        
    Returns:
        Dict with sentiment analysis results
    """
    if not content or not content.strip():
        return create_default_sentiment_response("Empty content provided")
    
    try:
        logger.info(f"Analyzing sentiment using {ai_provider} (enhanced: {use_enhanced})")
        
        # Try using the UnifiedAIService first
        try:
            # Use the UnifiedAIService to perform the analysis
            from src.unified_ai_service import UnifiedAIService
            
            # Create a service instance with the specified provider
            service = UnifiedAIService(provider=ai_provider, api_key=api_key)
            
            # Perform sentiment analysis
            logger.info(f"Using UnifiedAIService for sentiment analysis")
            result = service.analyze_sentiment(
                content=content,
                use_enhanced=use_enhanced,
                model=model
            )
            
            return result
            
        except ImportError as e:
            # If UnifiedAIService is not available, fall back to direct API calls
            logger.warning(f"UnifiedAIService not available, falling back to direct implementations: {e}")
            
            # Fallback to provider-specific implementations
            if ai_provider == "openai":
                if use_enhanced:
                    # Import the enhanced OpenAI sentiment analysis
                    from src.enhanced_sentiment import enhanced_analyze_ticket_content
                    return enhanced_analyze_ticket_content(content)
                else:
                    # Import the basic OpenAI sentiment analysis
                    from src.ai_service import analyze_ticket_content
                    return analyze_ticket_content(content)
            elif ai_provider == "claude":
                if use_enhanced:
                    # Import the enhanced Claude sentiment analysis
                    from src.claude_enhanced_sentiment import enhanced_analyze_ticket_content
                    return enhanced_analyze_ticket_content(content)
                else:
                    # Import the basic Claude sentiment analysis
                    from src.claude_service import analyze_ticket_content
                    return analyze_ticket_content(content)
            else:
                error_message = f"Unsupported AI provider: {ai_provider}"
                logger.error(error_message)
                return create_default_sentiment_response(error_message)
                
    except ImportError as e:
        # Handle import errors
        error_message = f"Failed to import sentiment analysis module: {e}"
        logger.error(error_message)
        return create_default_sentiment_response(error_message)
        
    except Exception as e:
        # Handle any other errors
        error_message = f"Error analyzing sentiment: {e}"
        logger.exception(error_message)
        return create_default_sentiment_response(error_message)