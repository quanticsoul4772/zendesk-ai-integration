"""
Claude AI Service module for Zendesk integration.

This module provides functionality to interact with Anthropic's Claude API for analyzing
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

# Define fallback models for different versions of the API
CLAUDE_MODELS = [
    "claude-3-haiku-20240307",   # Most specific model name
    "claude-3-haiku",            # Less specific model name
    "claude-3-sonnet-20240229",  # Fallback to Sonnet if Haiku not available
    "claude-3-sonnet",           # Less specific Sonnet
    "claude-instant-1.2",        # Legacy claude-instant
    "claude-2.1",                # Legacy claude-2
]

# Define custom exceptions
class ClaudeServiceError(Exception):
    """Base exception for Claude service errors"""
    pass

class RateLimitError(ClaudeServiceError):
    """Raised when rate limits are hit"""
    pass

class TokenLimitError(ClaudeServiceError):
    """Raised when token limits are exceeded"""
    pass

class ContentFilterError(ClaudeServiceError):
    """Raised when content violates usage policies"""
    pass

class DependencyError(ClaudeServiceError):
    """Raised when a required dependency is missing"""
    pass

def get_claude_client():
    """
    Get an Anthropic Claude client instance.
    
    Returns:
        An Anthropic client instance if the package is installed, otherwise raises DependencyError.
    
    Raises:
        DependencyError: If the Anthropic package is not installed.
    """
    try:
        # Only import Anthropic when needed
        from anthropic import Anthropic
        
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY environment variable not set. API calls will fail.")
            
        # Create and return the client
        return Anthropic(api_key=api_key)
    except ImportError:
        error_msg = "Anthropic package is not installed. Install it with: pip install anthropic"
        logger.error(error_msg)
        raise DependencyError(error_msg)

def check_anthropic_version():
    """Check the installed Anthropic package version and log warnings if needed."""
    try:
        # Try importlib.metadata first (Python 3.8+)
        try:
            import importlib.metadata
            version = importlib.metadata.version("anthropic")
        except (ImportError, Exception):
            # Fall back to direct import
            try:
                import anthropic
                version = getattr(anthropic, "__version__", "unknown")
            except ImportError:
                return "unknown"
                
        logger.info(f"Using Anthropic package version: {version}")
        
        # Check version compatibility
        if version != "unknown":
            try:
                major_version = int(version.split('.')[0])
                minor_version = int(version.split('.')[1])
                # We'll work with any version of the Anthropic package
                # No specific version check needed
            except (ValueError, IndexError):
                pass
                
        return version
    except Exception as e:
        logger.warning(f"Could not determine Anthropic package version: {str(e)}")
        return "unknown"

def exponential_backoff_with_jitter(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff and jitter to avoid thundering herd problem"""
    # Calculate exponential backoff
    delay = min(max_delay, base_delay * (2 ** retry_count))
    # Add jitter (random value between 0 and delay/2)
    jitter = random.uniform(0, delay / 2)
    return delay + jitter

def call_claude_with_retries(
    prompt: str,
    model: Optional[str] = None,  # Default is None, will try models from CLAUDE_MODELS list
    max_retries: int = 5,
    temperature: float = 0.0,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Call Claude API with retries, backoff, and error handling
    
    Args:
        prompt: The text prompt to send to the API
        model: The model to use (default: claude-3-haiku-20240307)
        max_retries: Maximum number of retry attempts (default: 5)
        temperature: Temperature setting (default: 0.0)
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Dict with parsed JSON response
        
    Raises:
        ClaudeServiceError: If all retries fail or other errors occur
    """
    # Check Anthropic version on first call
    check_anthropic_version()
    
    # Import anthropic
    try:
        import anthropic
    except ImportError:
        raise DependencyError("Anthropic package is not installed. Install it with: pip install anthropic")
    
    # Get the Claude client
    try:
        client = get_claude_client()
    except DependencyError as e:
        raise ClaudeServiceError(f"Cannot call Claude API: {str(e)}")
    
    last_exception = None
    
    # Add system prompt to ensure we get JSON output
    system_prompt = "You are an AI assistant that analyzes text to detect sentiment, urgency, and business impact. Always return your analysis as valid JSON."
    
    # Use the model provided or default to the first in our list
    model_to_use = model if model is not None else CLAUDE_MODELS[0]
    
    for attempt in range(max_retries):
        try:
            # Use the modern API format that works with current Anthropic versions
            response = client.messages.create(
                model=model_to_use,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=4096
            )
            
            # Extract content from the response - handle different response structures
            try:
                # Try to access content as a list with text attribute
                if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                    # Use getattr to avoid type checking errors
                    content = getattr(response.content[0], 'text', None)
                    if content is None:
                        # Fallback if text attribute doesn't exist
                        content = str(response.content[0])
                else:
                    # Fallback for other response structures
                    content = str(response)
            except Exception as e:
                logger.warning(f"Error extracting content from response: {str(e)}")
                content = str(response)
            
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
                        return {"raw_text": content, "confidence": 0.9}
                else:
                    # If not valid JSON and not in code block, return as raw text
                    return {"raw_text": content, "confidence": 0.9}
                
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Handle rate limit errors
            if "rate limit" in error_msg.lower() or error_type.lower().find("ratelimit") >= 0:
                last_exception = RateLimitError(f"Rate limit exceeded: {error_msg}")
                logger.warning(f"Claude rate limit hit (attempt {attempt+1}/{max_retries}): {error_msg}")
                
                # Calculate delay with jitter
                delay = exponential_backoff_with_jitter(attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
                
            # Handle token limit errors
            if "maximum context length" in error_msg.lower() or "token limit" in error_msg.lower():
                raise TokenLimitError(f"Token limit exceeded: {error_msg}")
                
            # Handle content filter errors
            if "content filter" in error_msg.lower() or "content policy" in error_msg.lower():
                raise ContentFilterError(f"Content filtered: {error_msg}")
                
            # Handle timeout errors
            if "timeout" in error_msg.lower() or error_type.lower().find("timeout") >= 0:
                last_exception = ClaudeServiceError(f"Claude API timeout: {error_msg}")
                logger.warning(f"Claude timeout (attempt {attempt+1}/{max_retries}): {error_msg}")
                
                # Use shorter timeout for retries to avoid long waits
                timeout = max(timeout * 0.8, 10.0)  # Reduce timeout but not below 10 seconds
                
                delay = exponential_backoff_with_jitter(attempt, base_delay=2.0)
                logger.info(f"Retrying in {delay:.2f} seconds with timeout={timeout:.1f}s...")
                time.sleep(delay)
                continue
                
            # Handle connection errors
            if "connection" in error_msg.lower() or error_type.lower().find("connection") >= 0:
                last_exception = ClaudeServiceError(f"Claude API connection error: {error_msg}")
                logger.warning(f"Claude connection error (attempt {attempt+1}/{max_retries}): {error_msg}")
                
                delay = exponential_backoff_with_jitter(attempt, base_delay=3.0)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
                
            # Handle bad request errors
            if "bad request" in error_msg.lower() or error_type.lower().find("badrequest") >= 0:
                logger.error(f"Claude bad request error: {error_msg}")
                raise ClaudeServiceError(f"Bad request: {error_msg}")
                
            # Unexpected error
            logger.exception(f"Unexpected error calling Claude: {error_msg}")
            raise ClaudeServiceError(f"Unexpected error: {error_msg}")
    
    # If we exhausted all retries
    if last_exception:
        logger.error(f"All {max_retries} Claude API call attempts failed")
        raise last_exception
        
    # This should never happen but just in case
    raise ClaudeServiceError("Failed to get response from Claude API")

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
        logger.info(f"Analyzing ticket content with Claude (length: {len(content)} chars)")
        
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
        
        result = call_claude_with_retries(
            prompt=prompt,
            model="claude-3-haiku-20240307",
            max_retries=3,
            temperature=0.3
        )
        
        # Extract and normalize values
        sentiment = result.get("sentiment", "unknown").lower().replace(" ", "_") if isinstance(result.get("sentiment"), str) else "unknown"
        category = result.get("category", "general_inquiry").lower().replace(" ", "_") if isinstance(result.get("category"), str) else "uncategorized"
        
        # Handle component which might be a list or string
        component_value = result.get("component", "none")
        if isinstance(component_value, list) and len(component_value) > 0:
            component = str(component_value[0]).lower().replace(" ", "_")
        elif isinstance(component_value, str):
            component = component_value.lower().replace(" ", "_")
        else:
            component = "none"
        
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
        
    except ClaudeServiceError as e:
        # Log specific AI service errors with appropriate level
        logger.error(f"Claude service error analyzing ticket content: {str(e)}")
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
