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
                # First try direct JSON parsing
                return json.loads(content)
            except json.JSONDecodeError:
                # Check if JSON is wrapped in a code block
                if '```json' in content and '```' in content.split('```json', 1)[1]:
                    # Extract content between ```json and the next ```
                    json_content = content.split('```json', 1)[1].split('```', 1)[0].strip()
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError:
                        # If still not valid JSON, return as raw text
                        return {"raw_text": content}
                else:
                    # If not valid JSON and not in code block, return as raw text
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
    Analyze ticket content to determine sentiment and category based on Exxact's actual categories
    
    Args:
        content: The ticket content to analyze
        
    Returns:
        Dict with sentiment, category, component, confidence, and optional error
    """
    if not content or not content.strip():
        logger.warning("Empty content provided for analysis")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "component": "none",
            "confidence": 0.0,
            "error": "Empty content provided"
        }
        
    try:
        logger.info(f"Analyzing ticket content (length: {len(content)} chars)")
        
        prompt = f"""
        Analyze the following customer message from Exxact Corporation (a hardware systems manufacturer) and:
        
        1) Identify the sentiment: Positive, Negative, Neutral, or Unknown.
        
        2) Categorize the message into ONE of these business categories:
        
           - system: Issues related to complete computer systems
           - resale_component: Issues with components being resold
           - hardware_issue: Problems with physical hardware components
           - system_component: Issues specific to system components
           - so_released_to_warehouse: Sales order released to warehouse status
           - wo_released_to_warehouse: Work order released to warehouse status
           - technical_support: General technical assistance requests
           - rma: Return merchandise authorization requests
           - software_issue: Problems with software, OS or drivers
           - general_inquiry: Information seeking that doesn't fit other categories
           
        3) If relevant, identify the specific component type mentioned:
           - gpu: Graphics processing unit issues
           - cpu: Central processing unit issues
           - drive: Hard drive or storage issues
           - memory: RAM or memory issues
           - power_supply: Power supply issues
           - motherboard: Motherboard issues
           - cooling: Cooling system issues
           - display: Monitor or display issues
           - network: Network card or connectivity issues
           - none: No specific component mentioned
        
        Customer message: {content}
        
        Format your response as JSON with these keys: sentiment, category, component, confidence.
        Keep your analysis focused on Exxact's business of computer hardware systems.
        """
        
        result = call_openai_with_retries(
            prompt=prompt,
            model="gpt-4o",
            max_retries=3,
            temperature=0.3
        )
        
        # Extract and normalize values
        sentiment = result.get("sentiment", "unknown").lower().replace(" ", "_")
        category = result.get("category", "general_inquiry").lower().replace(" ", "_")
        component = result.get("component", "none").lower().replace(" ", "_")
        
        # Handle confidence - convert text values to numeric
        confidence_value = result.get("confidence", 0.9)
        if isinstance(confidence_value, str):
            # Map text confidence levels to numeric values
            confidence_map = {
                "high": 0.9,
                "medium": 0.7,
                "low": 0.5,
                "veryhigh": 1.0,
                "verylow": 0.3
            }
            # Convert to lowercase and remove spaces for matching
            confidence_key = confidence_value.lower().replace(" ", "")
            confidence = confidence_map.get(confidence_key, 0.9)
        else:
            # Try to convert to float, default to 0.9 if fails
            try:
                confidence = float(confidence_value)
            except (ValueError, TypeError):
                confidence = 0.9
        
        logger.info(f"Analysis complete: sentiment={sentiment}, category={category}, component={component}")
        
        return {
            "sentiment": sentiment,
            "category": category,
            "component": component,
            "confidence": confidence,
            "raw_result": result  # Include raw result for debugging
        }
        
    except AIServiceError as e:
        # Log specific AI service errors with appropriate level
        logger.error(f"AI service error analyzing ticket content: {str(e)}")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "component": "none",
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
            "component": "none",
            "confidence": 0.0,
            "error": str(e),
            "error_type": type(e).__name__
        }