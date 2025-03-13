import os
import time
import random
import logging
import json
from typing import Dict, Any, Optional, List

import openai

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))

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

def exponential_backoff_with_jitter(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff and jitter to avoid thundering herd problem"""
    # Calculate exponential backoff
    delay = min(max_delay, base_delay * (2 ** retry_count))
    # Add jitter (random value between 0 and delay/2)
    jitter = random.uniform(0, delay / 2)
    return delay + jitter

def call_openai_with_retries(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    max_retries: int = 5,
    temperature: float = 0.0,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Call OpenAI API with retries, backoff, and error handling
    
    Args:
        prompt: The text prompt to send to the API
        model: The model to use (default: gpt-3.5-turbo)
        max_retries: Maximum number of retry attempts (default: 5)
        temperature: Temperature setting (default: 0.0)
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Dict with parsed JSON response
        
    Raises:
        AIServiceError: If all retries fail or other errors occur
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # Add timeout to avoid hanging requests
            response = openai_client.chat.completions.create(
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
                
        except openai.RateLimitError as e:
            last_exception = RateLimitError(f"Rate limit exceeded: {str(e)}")
            logger.warning(f"OpenAI rate limit hit (attempt {attempt+1}/{max_retries})")
            
            # Calculate delay with jitter
            delay = exponential_backoff_with_jitter(attempt)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            
        except openai.BadRequestError as e:
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
                
        except openai.APITimeoutError:
            last_exception = AIServiceError("OpenAI API timeout")
            logger.warning(f"OpenAI timeout (attempt {attempt+1}/{max_retries})")
            
            # Use shorter timeout for retries to avoid long waits
            timeout = max(timeout * 0.8, 10.0)  # Reduce timeout but not below 10 seconds
            
            delay = exponential_backoff_with_jitter(attempt, base_delay=2.0)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            
        except (openai.APIError, openai.APIConnectionError) as e:
            last_exception = AIServiceError(f"OpenAI API error: {str(e)}")
            logger.warning(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {str(e)}")
            
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

def analyze_ticket_content(content: str) -> Dict[str, str]:
    """
    Analyze ticket content to determine sentiment and category
    
    Args:
        content: The ticket content to analyze
        
    Returns:
        Dict with sentiment and category
    """
    try:
        prompt = f"""
        Analyze the following customer message and:
        1) Provide sentiment: Positive, Negative, or Neutral.
        2) Provide category label (e.g., billing issue, technical issue, general inquiry).
        
        Message: {content}
        
        Format your response as JSON with keys: sentiment, category.
        """
        
        result = call_openai_with_retries(
            prompt=prompt,
            model="gpt-3.5-turbo",
            max_retries=3
        )
        
        # Ensure we have the expected fields
        sentiment = result.get("sentiment", "unknown")
        category = result.get("category", "general_inquiry")
        
        return {
            "sentiment": sentiment.lower().replace(" ", "_"),
            "category": category.lower().replace(" ", "_"),
            "confidence": 0.9  # Could be dynamic based on model output in future
        }
        
    except Exception as e:
        logger.exception(f"Error analyzing ticket content: {str(e)}")
        return {
            "sentiment": "unknown",
            "category": "uncategorized",
            "confidence": 0.0,
            "error": str(e)
        }