"""
AI Service module for Zendesk integration.

This module provides functionality to interact with OpenAI's API for analyzing
ticket content, determining sentiment, and categorizing customer inquiries.
"""

import os
import time
import random
import logging
import json
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

# Define custom exceptions
class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass

class RateLimitError(AIServiceError):
    """Raised when rate limits are hit"""
    pass

class TokenLimitError(AIServiceError):
    """Raised when token limits are exceeded"""
    pass

class ContentFilterError(AIServiceError):
    """Raised when content violates usage policies"""
    pass

class DependencyError(AIServiceError):
    """Raised when a required dependency is missing"""
    pass

def get_openai_client():
    """
    Get an OpenAI client instance.
    
    Returns:
        An OpenAI client instance if the package is installed, otherwise raises DependencyError.
    
    Raises:
        DependencyError: If the OpenAI package is not installed.
    """
    try:
        # Only import OpenAI when needed
        from openai import OpenAI  # type: ignore
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY environment variable not set. API calls will fail.")
            
        # Create and return the client
        return OpenAI(api_key=api_key)
    except ImportError:
        error_msg = "OpenAI package is not installed. Install it with: pip install openai>=1.0.0"
        logger.error(error_msg)
        raise DependencyError(error_msg)

def check_openai_version():
    """Check the installed OpenAI package version and log warnings if needed."""
    try:
        # Try importlib.metadata first (Python 3.8+)
        try:
            import importlib.metadata
            version = importlib.metadata.version("openai")
        except (ImportError, Exception):
            # Fall back to direct import
            try:
                import openai  # type: ignore
                version = getattr(openai, "__version__", "unknown")
            except ImportError:
                return "unknown"
                
        logger.info(f"Using OpenAI package version: {version}")
        
        # Check version compatibility
        if version != "unknown":
            try:
                major_version = int(version.split('.')[0])
                if major_version < 1:
                    logger.warning(f"OpenAI package version {version} may not be compatible. Version 1.0.0+ is recommended.")
            except (ValueError, IndexError):
                pass
                
        return version
    except Exception as e:
        logger.warning(f"Could not determine OpenAI package version: {str(e)}")
        return "unknown"

def exponential_backoff_with_jitter(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff and jitter to avoid thundering herd problem"""
    # Calculate exponential backoff
    delay = min(max_delay, base_delay * (2 ** retry_count))
    # Add jitter (random value between 0 and delay/2)
    jitter = random.uniform(0, delay / 2)
    return delay + jitter

def call_openai_with_retries(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 5,
    temperature: float = 0.0,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Call OpenAI API with retries, backoff, and error handling
    
    Args:
        prompt: The text prompt to send to the API
        model: The model to use (default: gpt-4o-mini)
        max_retries: Maximum number of retry attempts (default: 5)
        temperature: Temperature setting (default: 0.0)
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Dict with parsed JSON response
        
    Raises:
        AIServiceError: If all retries fail or other errors occur
    """
    # Check OpenAI version on first call
    check_openai_version()
    
    # Import error types only when needed
    try:
        from openai import (  # type: ignore
            APIError,
            APIConnectionError,
            APITimeoutError,
            BadRequestError,
            RateLimitError as OpenAIRateLimitError
        )
    except ImportError:
        raise DependencyError("OpenAI package is not installed. Install it with: pip install openai>=1.0.0")
    
    # Get the OpenAI client
    try:
        client = get_openai_client()
    except DependencyError as e:
        raise AIServiceError(f"Cannot call OpenAI API: {str(e)}")
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # Add timeout to avoid hanging requests
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=timeout
            )
            
            # Extract the content from the first choice
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, return as raw text
                return {"raw_text": content}
                
        except OpenAIRateLimitError as e:
            error_msg = f"Rate limit exceeded: {str(e)}"
            last_exception = RateLimitError(error_msg)
            logger.warning(f"OpenAI rate limit hit (attempt {attempt+1}/{max_retries}): {error_msg}")
            
            # Calculate delay with jitter
            delay = exponential_backoff_with_jitter(attempt)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            
        except BadRequestError as e:
            # Check if it's a token limit issue
            if "maximum context length" in str(e).lower():
                raise TokenLimitError(f"Token limit exceeded: {str(e)}")
            # Check if it's a content filter issue
            elif "content filter" in str(e).lower():
                raise ContentFilterError(f"Content filtered: {str(e)}")
            # Other bad request errors
            else:
                logger.error(f"OpenAI bad request error: {str(e)}")
                raise AIServiceError(f"Bad request: {str(e)}")
                
        except APITimeoutError:
            error_msg = "OpenAI API timeout"
            last_exception = AIServiceError(error_msg)
            logger.warning(f"OpenAI timeout (attempt {attempt+1}/{max_retries}): {error_msg}")
            
            # Use shorter timeout for retries to avoid long waits
            timeout = max(timeout * 0.8, 10.0)  # Reduce timeout but not below 10 seconds
            
            delay = exponential_backoff_with_jitter(attempt, base_delay=2.0)
            logger.info(f"Retrying in {delay:.2f} seconds with timeout={timeout:.1f}s...")
            time.sleep(delay)
            
        except (APIError, APIConnectionError) as e:
            error_type = type(e).__name__
            error_msg = f"OpenAI {error_type}: {str(e)}"
            last_exception = AIServiceError(error_msg)
            logger.warning(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {error_msg}")
            
            delay = exponential_backoff_with_jitter(attempt, base_delay=3.0)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            
        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error calling OpenAI: {str(e)}")
            raise AIServiceError(f"Unexpected error: {str(e)}")
    
    # If we exhausted all retries
    if last_exception:
        logger.error(f"All {max_retries} OpenAI API call attempts failed")
        raise last_exception
        
    # This should never happen but just in case
    raise AIServiceError("Failed to get response from OpenAI API")

def analyze_ticket_content(content: str) -> Dict[str, Any]:
    """
    Analyze ticket content to determine sentiment and category
    
    Args:
        content: The ticket content to analyze
        
    Returns:
        Dict with sentiment, category, confidence, and optional error
    """
    if not content or not content.strip():
        logger.warning("Empty content provided for analysis")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "confidence": 0.0,
            "error": "Empty content provided"
        }
        
    try:
        logger.info(f"Analyzing ticket content (length: {len(content)} chars)")
        
        prompt = f"""
        Analyze the following customer message and:
        1) Provide sentiment: Positive, Negative, or Neutral.
        2) Provide category label (e.g., billing issue, technical issue, general inquiry).
        
        Message: {content}
        
        Format your response as JSON with keys: sentiment, category.
        """
        
        result = call_openai_with_retries(
            prompt=prompt,
            model="gpt-4o-mini",
            max_retries=3
        )
        
        # Ensure we have the expected fields
        sentiment = result.get("sentiment", "unknown")
        category = result.get("category", "general_inquiry")
        
        # Normalize values
        normalized_sentiment = sentiment.lower().replace(" ", "_")
        normalized_category = category.lower().replace(" ", "_")
        
        logger.info(f"Analysis complete: sentiment={normalized_sentiment}, category={normalized_category}")
        
        return {
            "sentiment": normalized_sentiment,
            "category": normalized_category,
            "confidence": 0.9,  # Could be dynamic based on model output in future
            "raw_result": result  # Include raw result for debugging
        }
        
    except AIServiceError as e:
        # Log specific AI service errors with appropriate level
        logger.error(f"AI service error analyzing ticket content: {str(e)}")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "confidence": 0.0,
            "error": str(e),
            "error_type": type(e).__name__
        }
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error analyzing ticket content: {str(e)}")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "confidence": 0.0,
            "error": str(e),
            "error_type": type(e).__name__
        }