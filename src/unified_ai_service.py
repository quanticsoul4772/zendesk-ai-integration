"""
Unified AI Service Module

This module provides a single interface for interacting with different AI providers
(OpenAI and Claude) with consistent error handling and retry logic.
"""

import os
import time
import random
import logging
import json
from typing import Dict, Any, Optional, List, Union
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    CLAUDE = "claude"

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

class UnifiedAIService:
    """
    Unified AI service that provides a common interface to multiple AI providers.
    Supports OpenAI and Claude.
    """
    
    def __init__(self, provider: str = "claude", api_key: Optional[str] = None):
        """
        Initialize the AI service.
        
        Args:
            provider: AI provider to use ("openai" or "claude")
            api_key: Optional API key (otherwise read from environment)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.client = None
        self.ready = False
        
        # Set up the appropriate client based on provider
        if self.provider == AIProvider.OPENAI.value:
            self._setup_openai()
        elif self.provider == AIProvider.CLAUDE.value:
            self._setup_claude()
        else:
            raise ValueError(f"Unsupported AI provider: {provider}. Supported: openai, claude")
    
    def _setup_openai(self):
        """Setup OpenAI integration."""
        try:
            # Only import when needed
            from openai import OpenAI
            
            # Get API key from environment if not provided
            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY environment variable not set. API calls will fail.")
            
            # Create the client
            self.client = OpenAI(api_key=api_key)
            self.ready = True
            logger.info("OpenAI client initialized successfully")
            
        except ImportError as e:
            logger.error(f"Error setting up OpenAI: {e}")
            logger.error("OpenAI package is not installed. Install it with: pip install openai>=1.0.0")
            self.ready = False
            
    def _setup_claude(self):
        """Setup Claude integration."""
        try:
            # Only import when needed
            from anthropic import Anthropic
            
            # Get API key from environment if not provided
            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY environment variable not set. API calls will fail.")
            
            # Create the client
            self.client = Anthropic(api_key=api_key)
            self.ready = True
            logger.info("Claude client initialized successfully")
            
        except ImportError as e:
            logger.error(f"Error setting up Claude: {e}")
            logger.error("Anthropic package is not installed. Install it with: pip install anthropic")
            self.ready = False
    
    def _get_openai_version(self) -> str:
        """Get the installed OpenAI package version."""
        try:
            # Try importlib.metadata first (Python 3.8+)
            try:
                import importlib.metadata
                return importlib.metadata.version("openai")
            except (ImportError, Exception):
                # Fall back to direct import
                try:
                    import openai
                    return getattr(openai, "__version__", "unknown")
                except ImportError:
                    return "unknown"
        except Exception as e:
            logger.warning(f"Could not determine OpenAI package version: {str(e)}")
            return "unknown"
    
    def _get_anthropic_version(self) -> str:
        """Get the installed Anthropic package version."""
        try:
            # Try importlib.metadata first (Python 3.8+)
            try:
                import importlib.metadata
                return importlib.metadata.version("anthropic")
            except (ImportError, Exception):
                # Fall back to direct import
                try:
                    import anthropic
                    return getattr(anthropic, "__version__", "unknown")
                except ImportError:
                    return "unknown"
        except Exception as e:
            logger.warning(f"Could not determine Anthropic package version: {str(e)}")
            return "unknown"
    
    def _exponential_backoff_with_jitter(self, retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        Calculate delay with exponential backoff and jitter to avoid thundering herd problem.
        
        Args:
            retry_count: Number of retries that have been attempted
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            
        Returns:
            Delay in seconds to wait before next retry
        """
        # Calculate exponential backoff
        delay = min(max_delay, base_delay * (2 ** retry_count))
        # Add jitter (random value between 0 and delay/2)
        jitter = random.uniform(0, delay / 2)
        return delay + jitter
        
    def get_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.0,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Get a completion from the AI service with retries and error handling.
        
        Args:
            prompt: Text prompt
            model: Model to use (defaults based on provider)
            max_retries: Maximum retry attempts
            temperature: Temperature setting
            timeout: Request timeout in seconds
            
        Returns:
            Dict with completion result
        """
        if not self.ready or not self.client:
            return {"error": "AI service not properly initialized"}
            
        if self.provider == AIProvider.OPENAI.value:
            return self._get_openai_completion(
                prompt=prompt,
                model=model or "gpt-4o-mini",
                max_retries=max_retries,
                temperature=temperature,
                timeout=timeout
            )
        elif self.provider == AIProvider.CLAUDE.value:
            return self._get_claude_completion(
                prompt=prompt,
                model=model or "claude-3-haiku-20240307",
                max_retries=max_retries,
                temperature=temperature,
                timeout=timeout
            )
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
    
    def _get_openai_completion(
        self,
        prompt: str,
        model: str,
        max_retries: int,
        temperature: float,
        timeout: float
    ) -> Dict[str, Any]:
        """Get completion from OpenAI with retries and error handling."""
        if not self.ready or not self.client:
            return {"error": "OpenAI client not initialized"}
            
        try:
            # Import error types for handling
            from openai import (
                APIError,
                APIConnectionError,
                APITimeoutError,
                BadRequestError,
                RateLimitError as OpenAIRateLimitError
            )
        except ImportError:
            return {"error": "OpenAI package is not properly installed or imported"}
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Add timeout to avoid hanging requests
                response = self.client.chat.completions.create(
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
                    # Check if JSON is wrapped in a code block
                    if '```json' in content and '```' in content.split('```json', 1)[1]:
                        json_content = content.split('```json', 1)[1].split('```', 1)[0].strip()
                        try:
                            return json.loads(json_content)
                        except json.JSONDecodeError:
                            return {"raw_text": content}
                    else:
                        return {"raw_text": content}
                    
            except OpenAIRateLimitError as e:
                error_msg = f"Rate limit exceeded: {str(e)}"
                last_exception = RateLimitError(error_msg)
                logger.warning(f"OpenAI rate limit hit (attempt {attempt+1}/{max_retries}): {error_msg}")
                
                # Calculate delay with jitter
                delay = self._exponential_backoff_with_jitter(attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
            except BadRequestError as e:
                if "maximum context length" in str(e).lower():
                    return {"error": f"Token limit exceeded: {str(e)}"}
                elif "content filter" in str(e).lower():
                    return {"error": f"Content filtered: {str(e)}"}
                else:
                    return {"error": f"Bad request: {str(e)}"}
                    
            except APITimeoutError as e:
                last_exception = AIServiceError(f"OpenAI API timeout: {str(e)}")
                logger.warning(f"OpenAI timeout (attempt {attempt+1}/{max_retries})") 
                
                timeout = max(timeout * 0.8, 10.0)  # Reduce timeout but not below 10 seconds
                
                delay = self._exponential_backoff_with_jitter(attempt, base_delay=2.0)
                logger.info(f"Retrying in {delay:.2f} seconds with timeout={timeout:.1f}s...")
                time.sleep(delay)
                
            except (APIError, APIConnectionError) as e:
                last_exception = AIServiceError(f"OpenAI API error: {str(e)}")
                logger.warning(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                delay = self._exponential_backoff_with_jitter(attempt, base_delay=3.0)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
        
        # If we exhausted all retries
        if last_exception:
            return {"error": f"All {max_retries} OpenAI API call attempts failed: {str(last_exception)}"}
            
        # This should never happen but just in case
        return {"error": "Failed to get response from OpenAI API"}
    
    def _get_claude_completion(
        self,
        prompt: str,
        model: str,
        max_retries: int,
        temperature: float,
        timeout: float
    ) -> Dict[str, Any]:
        """Get completion from Claude with retries and error handling."""
        if not self.ready or not self.client:
            return {"error": "Claude client not initialized"}
            
        # Add system prompt to ensure we get consistent output
        system_prompt = "You are an AI assistant that analyzes text to detect sentiment, urgency, and business impact. Always return your analysis as valid JSON."
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Use the modern API format for Claude
                response = self.client.messages.create(
                    model=model,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=4096
                )
                
                # Extract content from the response
                try:
                    # Try to access content as a list with text attribute
                    if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                        content = getattr(response.content[0], 'text', None)
                        if content is None:
                            content = str(response.content[0])
                    else:
                        content = str(response)
                except Exception as e:
                    logger.warning(f"Error extracting content from response: {str(e)}")
                    content = str(response)
                
                # Try to parse as JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Check if JSON is wrapped in a code block
                    if '```json' in content and '```' in content.split('```json', 1)[1]:
                        json_content = content.split('```json', 1)[1].split('```', 1)[0].strip()
                        try:
                            return json.loads(json_content)
                        except json.JSONDecodeError:
                            return {"raw_text": content}
                    else:
                        return {"raw_text": content}
                    
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Handle rate limit errors
                if "rate limit" in error_msg.lower() or error_type.lower().find("ratelimit") >= 0:
                    last_exception = RateLimitError(f"Rate limit exceeded: {error_msg}")
                    logger.warning(f"Claude rate limit hit (attempt {attempt+1}/{max_retries}): {error_msg}")
                    
                    delay = self._exponential_backoff_with_jitter(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                    
                # Handle token limit errors
                if "maximum context length" in error_msg.lower() or "token limit" in error_msg.lower():
                    return {"error": f"Token limit exceeded: {error_msg}"}
                    
                # Handle content filter errors
                if "content filter" in error_msg.lower() or "content policy" in error_msg.lower():
                    return {"error": f"Content filtered: {error_msg}"}
                    
                # Handle timeout errors
                if "timeout" in error_msg.lower() or error_type.lower().find("timeout") >= 0:
                    last_exception = AIServiceError(f"Claude API timeout: {error_msg}")
                    logger.warning(f"Claude timeout (attempt {attempt+1}/{max_retries}): {error_msg}")
                    
                    timeout = max(timeout * 0.8, 10.0)
                    
                    delay = self._exponential_backoff_with_jitter(attempt, base_delay=2.0)
                    logger.info(f"Retrying in {delay:.2f} seconds with timeout={timeout:.1f}s...")
                    time.sleep(delay)
                    continue
                    
                # Handle connection errors
                if "connection" in error_msg.lower() or error_type.lower().find("connection") >= 0:
                    last_exception = AIServiceError(f"Claude API connection error: {error_msg}")
                    logger.warning(f"Claude connection error (attempt {attempt+1}/{max_retries}): {error_msg}")
                    
                    delay = self._exponential_backoff_with_jitter(attempt, base_delay=3.0)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                    
                # Unexpected error
                return {"error": f"Unexpected error calling Claude: {error_msg}"}
        
        # If we exhausted all retries
        if last_exception:
            return {"error": f"All {max_retries} Claude API call attempts failed: {str(last_exception)}"}
            
        # This should never happen but just in case
        return {"error": "Failed to get response from Claude API"}
        
    def analyze_sentiment(
        self,
        content: str,
        use_enhanced: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment in the provided content using the appropriate provider.
        
        Args:
            content: Text content to analyze
            use_enhanced: Whether to use enhanced sentiment analysis
            model: Model to use (defaults to appropriate default for provider)
            
        Returns:
            Dict with sentiment analysis results
        """
        if not content or not content.strip():
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
                "error": "Empty content provided"
            }
        
        if self.provider == AIProvider.OPENAI.value:
            prompt = self._create_sentiment_prompt(content, use_enhanced)
            result = self.get_completion(
                prompt=prompt,
                model=model or "gpt-4o-mini",
                temperature=0.3
            )
        elif self.provider == AIProvider.CLAUDE.value:
            prompt = self._create_sentiment_prompt(content, use_enhanced)
            result = self.get_completion(
                prompt=prompt,
                model=model or "claude-3-haiku-20240307",
                temperature=0.3
            )
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
        
        # Check for errors
        if "error" in result:
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
                "error": result["error"]
            }
            
        # Process sentiment data to ensure consistent structure
        return self._process_sentiment_result(result, use_enhanced)
    
    def _create_sentiment_prompt(self, content: str, use_enhanced: bool) -> str:
        """Create the appropriate prompt for sentiment analysis."""
        if use_enhanced:
            # Enhanced sentiment analysis prompt
            return f"""
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
        else:
            # Basic sentiment analysis prompt
            return f"""
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
    
    def _process_sentiment_result(self, result: Dict[str, Any], use_enhanced: bool) -> Dict[str, Any]:
        """Process and normalize the sentiment analysis result."""
        if not isinstance(result, dict):
            return {
                "sentiment": "unknown",
                "category": "uncategorized",
                "component": "none",
                "confidence": 0.0,
                "error": "Invalid response format"
            }
        
        # Handle raw text response
        if "raw_text" in result:
            return {
                "sentiment": "unknown",
                "category": "uncategorized",
                "component": "none",
                "confidence": 0.0,
                "error": "Invalid response format",
                "raw_text": result["raw_text"]
            }
            
        # Extract and normalize sentiment data
        if use_enhanced:
            # Process enhanced sentiment result
            sentiment_data = result.get("sentiment", {})
            
            if not isinstance(sentiment_data, dict):
                sentiment_data = {
                    "polarity": str(sentiment_data).lower() if sentiment_data else "unknown",
                    "urgency_level": 1,
                    "frustration_level": 1,
                    "technical_expertise": 1,
                    "business_impact": {"detected": False, "description": ""},
                    "key_phrases": [],
                    "emotions": []
                }
            
            # Ensure polarity is normalized
            polarity = sentiment_data.get("polarity", "unknown")
            if isinstance(polarity, str):
                polarity = polarity.lower().replace(" ", "_")
            else:
                polarity = "unknown"
                
            sentiment_data["polarity"] = polarity
            
            # Ensure other fields are present and normalized
            for field in ["urgency_level", "frustration_level", "technical_expertise"]:
                if field not in sentiment_data or not isinstance(sentiment_data[field], (int, float)):
                    sentiment_data[field] = 1
                else:
                    sentiment_data[field] = max(1, min(5, int(sentiment_data[field])))
            
            # Ensure business_impact is properly formatted
            if "business_impact" not in sentiment_data or not isinstance(sentiment_data["business_impact"], dict):
                sentiment_data["business_impact"] = {"detected": False, "description": ""}
            
            # Ensure emotions and key_phrases are lists
            for field in ["emotions", "key_phrases"]:
                if field not in sentiment_data or not isinstance(sentiment_data[field], list):
                    sentiment_data[field] = []
            
            # Try to calculate priority score
            try:
                # First try direct import
                from unified_sentiment import calculate_priority_score
                priority_score = calculate_priority_score(sentiment_data)
            except ImportError:
                try:
                    # Fall back to enhanced_sentiment if unified_sentiment is not available
                    from enhanced_sentiment import calculate_priority_score
                    priority_score = calculate_priority_score(sentiment_data)
                except ImportError:
                    # Calculate directly if neither module is available
                    weights = {
                        "urgency": 0.35,
                        "frustration": 0.30,
                        "business_impact": 0.25,
                        "technical_expertise": 0.10
                    }
                    
                    urgency_score = sentiment_data.get("urgency_level", 1)  # 1-5
                    frustration_score = sentiment_data.get("frustration_level", 1)  # 1-5
                    business_impact_score = 5 if sentiment_data.get("business_impact", {}).get("detected", False) else 0
                    technical_expertise = sentiment_data.get("technical_expertise", 3)  # 1-5
                    technical_score = max(1, 6 - technical_expertise)  # Invert scale
                    
                    weighted_score = (
                        weights["urgency"] * urgency_score +
                        weights["frustration"] * frustration_score +
                        weights["business_impact"] * business_impact_score + 
                        weights["technical_expertise"] * technical_score
                    )
                    
                    priority_score = min(10, max(1, round(weighted_score * 2)))
            
            # Build final result
            category = result.get("category", "uncategorized")
            component = result.get("component", "none")
            confidence = result.get("confidence", 0.9)
            
            return {
                "sentiment": sentiment_data,
                "category": category.lower().replace(" ", "_") if isinstance(category, str) else "uncategorized",
                "component": component.lower().replace(" ", "_") if isinstance(component, str) else "none",
                "priority_score": priority_score,
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else 0.9
            }
        else:
            # Process basic sentiment result
            sentiment = result.get("sentiment", "unknown")
            if isinstance(sentiment, str):
                sentiment = sentiment.lower().replace(" ", "_")
            else:
                sentiment = "unknown"
                
            category = result.get("category", "uncategorized")
            if isinstance(category, str):
                category = category.lower().replace(" ", "_")
            else:
                category = "uncategorized"
                
            component = result.get("component", "none")
            if isinstance(component, str):
                component = component.lower().replace(" ", "_")
            else:
                component = "none"
                
            confidence = result.get("confidence", 0.9)
            if not isinstance(confidence, (int, float)):
                confidence = 0.9
                
            return {
                "sentiment": sentiment,
                "category": category,
                "component": component,
                "confidence": confidence
            }