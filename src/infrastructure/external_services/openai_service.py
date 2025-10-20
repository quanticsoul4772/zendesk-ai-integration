"""
OpenAI Service Adapter

This module provides an implementation of the AIService interface using the OpenAI API.
"""

import os
import logging
import json
import time
import random
from typing import Dict, Any, List, Optional

from src.domain.interfaces.ai_service_interfaces import AIService, AIServiceError, RateLimitError, TokenLimitError, ContentFilterError
from src.infrastructure.utils.retry import with_retry

# Set up logging
logger = logging.getLogger(__name__)


class OpenAIService(AIService):
    """
    Implementation of the AIService interface using the OpenAI API.

    This service uses the OpenAI API to analyze ticket content and sentiment.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI service.

        Args:
            api_key: OpenAI API key (optional, defaults to environment variable)
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            logger.warning("OpenAI API key not provided - API calls will fail")

        # Initialize the client lazily when needed
        self._client = None

    @property
    def client(self):
        """Get the OpenAI client, initializing it if necessary."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package is not installed. Install it with: pip install openai>=1.0.0")
                raise AIServiceError("OpenAI package is not installed")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
                raise AIServiceError(f"Error initializing OpenAI client: {str(e)}")

        return self._client

    @with_retry(max_retries=3, retry_on=[Exception])
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to determine sentiment, category, etc.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for analysis")
            return {
                "sentiment": {
                    "polarity": "unknown",
                    "urgency_level": 1,
                    "frustration_level": 1,
                    "emotions": []
                },
                "category": "uncategorized",
                "component": "none",
                "priority": "low",
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Analyzing content with OpenAI (length: {len(content)} chars)")

        # Craft the prompt for OpenAI
        prompt = f"""
        Analyze the following customer message from Exxact Corporation (a hardware systems manufacturer) and provide a detailed analysis as JSON with the following structure:

        {{
          "category": "[Select ONE category: system, resale_component, hardware_issue, system_component, so_released_to_warehouse, wo_released_to_warehouse, technical_support, rma, software_issue, general_inquiry]",
          "component": "[ONE component type if relevant: gpu, cpu, drive, memory, power_supply, motherboard, cooling, display, network, none]",
          "priority": "[high, medium, or low]",
          "sentiment": {{
            "polarity": "[positive, negative, neutral, or unknown]",
            "urgency_level": [1-5 scale, where 1 is lowest urgency and 5 is highest],
            "frustration_level": [1-5 scale, where 1 is not frustrated and 5 is extremely frustrated],
            "emotions": [array of emotions detected in the message],
            "business_impact": {{
              "detected": [true or false],
              "impact_areas": [array of business areas affected, if any],
              "severity": [0-5 scale, where 0 is no impact and 5 is severe impact]
            }}
          }}
        }}

        Categories explanation:
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

        Customer message: {content}

        Provide only the JSON output with no other text.
        """

        try:
            # Call the OpenAI API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score
            result["confidence"] = 0.9  # Default high confidence for OpenAI

            logger.info(f"Analysis complete: sentiment.polarity={result['sentiment']['polarity']}, category={result['category']}")

            return result
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and wrap in a generic AIServiceError
            logger.exception(f"Unexpected error analyzing content: {str(e)}")
            return {
                "sentiment": {
                    "polarity": "unknown",
                    "urgency_level": 1,
                    "frustration_level": 1,
                    "emotions": []
                },
                "category": "uncategorized",
                "component": "none",
                "priority": "low",
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }

    @with_retry(max_retries=3, retry_on=[Exception])
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Analyze sentiment of content.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with sentiment analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for sentiment analysis")
            return {
                "polarity": "unknown",
                "urgency_level": 1,
                "frustration_level": 1,
                "emotions": [],
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Analyzing sentiment with OpenAI (length: {len(content)} chars)")

        # Craft the prompt for OpenAI
        prompt = f"""
        Analyze the sentiment of the following customer message and provide a detailed analysis as JSON with the following structure:

        {{
          "polarity": "[positive, negative, neutral, or unknown]",
          "urgency_level": [1-5 scale, where 1 is lowest urgency and 5 is highest],
          "frustration_level": [1-5 scale, where 1 is not frustrated and 5 is extremely frustrated],
          "emotions": [array of emotions detected in the message],
          "business_impact": {{
            "detected": [true or false],
            "impact_areas": [array of business areas affected, if any],
            "severity": [0-5 scale, where 0 is no impact and 5 is severe impact]
          }}
        }}

        Message: {content}

        Provide only the JSON output with no other text.
        """

        try:
            # Call the OpenAI API
            response = self._call_api(prompt)

            # Process the response
            result_json = self._process_response(response)

            # Extract sentiment data
            sentiment = result_json.get("sentiment", result_json)

            # Add confidence score
            sentiment["confidence"] = 0.9  # Default high confidence for OpenAI

            logger.info(f"Sentiment analysis complete: polarity={sentiment['polarity']}")

            return sentiment
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and wrap in a generic AIServiceError
            logger.exception(f"Unexpected error analyzing sentiment: {str(e)}")
            return {
                "polarity": "unknown",
                "urgency_level": 1,
                "frustration_level": 1,
                "emotions": [],
                "business_impact": {
                    "detected": False,
                    "impact_areas": [],
                    "severity": 0
                },
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }

    @with_retry(max_retries=3, retry_on=[Exception])
    def categorize_ticket(self, content: str) -> Dict[str, Any]:
        """
        Categorize a ticket based on its content.

        Args:
            content: The ticket content to categorize

        Returns:
            Dictionary with categorization results

        Raises:
            AIServiceError: If an error occurs during categorization
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for categorization")
            return {
                "category": "uncategorized",
                "component": "none",
                "priority": "low",
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Categorizing ticket with OpenAI (length: {len(content)} chars)")

        # Craft the prompt for OpenAI
        prompt = f"""
        Categorize the following customer message from Exxact Corporation (a hardware systems manufacturer) and provide a detailed categorization as JSON with the following structure:

        {{
          "category": "[Select ONE category: system, resale_component, hardware_issue, system_component, so_released_to_warehouse, wo_released_to_warehouse, technical_support, rma, software_issue, general_inquiry]",
          "component": "[ONE component type if relevant: gpu, cpu, drive, memory, power_supply, motherboard, cooling, display, network, none]",
          "priority": "[high, medium, or low]",
          "rationale": "[Brief explanation of the categorization]"
        }}

        Categories explanation:
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

        Customer message: {content}

        Provide only the JSON output with no other text.
        """

        try:
            # Call the OpenAI API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score
            result["confidence"] = 0.9  # Default high confidence for OpenAI

            logger.info(f"Categorization complete: category={result['category']}, component={result['component']}")

            return result
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and wrap in a generic AIServiceError
            logger.exception(f"Unexpected error categorizing ticket: {str(e)}")
            return {
                "category": "uncategorized",
                "component": "none",
                "priority": "low",
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _call_api(self, prompt: str, temperature: float = 0.0, timeout: float = 30.0) -> str:
        """
        Call the OpenAI API with retry and error handling logic.

        Args:
            prompt: The text prompt to send to the API
            temperature: Temperature setting (default: 0.0)
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Response text from the API

        Raises:
            RateLimitError: If rate limits are exceeded
            TokenLimitError: If token limits are exceeded
            ContentFilterError: If content violates usage policies
            AIServiceError: For other API errors
        """
        try:
            # Import error types from OpenAI only when needed to avoid direct dependencies
            from openai import (
                APIError,
                APIConnectionError,
                APITimeoutError,
                BadRequestError,
                RateLimitError as OpenAIRateLimitError
            )

            # Call the API
            logger.debug(f"Calling OpenAI API with model {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=timeout
            )

            # Extract the content from the first choice
            content = response.choices[0].message.content

            return content
        except OpenAIRateLimitError as e:
            error_msg = f"OpenAI rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise RateLimitError(error_msg)
        except BadRequestError as e:
            error_str = str(e).lower()
            # Check if it's a token limit issue
            if "maximum context length" in error_str:
                error_msg = f"OpenAI token limit exceeded: {str(e)}"
                logger.error(error_msg)
                raise TokenLimitError(error_msg)
            # Check if it's a content filter issue
            elif "content filter" in error_str:
                error_msg = f"OpenAI content filter triggered: {str(e)}"
                logger.error(error_msg)
                raise ContentFilterError(error_msg)
            # Other bad request errors
            else:
                error_msg = f"OpenAI bad request error: {str(e)}"
                logger.error(error_msg)
                raise AIServiceError(error_msg)
        except APITimeoutError as e:
            error_msg = f"OpenAI API timeout: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg)
        except (APIError, APIConnectionError) as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg)
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error calling OpenAI: {str(e)}"
            logger.exception(error_msg)
            raise AIServiceError(error_msg)

    def _process_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process the response from the OpenAI API.

        Args:
            response_text: Text response from the API

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            AIServiceError: If the response cannot be parsed as JSON
        """
        try:
            # First try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Check if JSON is wrapped in a code block
            if '```json' in response_text and '```' in response_text.split('```json', 1)[1]:
                # Extract content between ```json and the next ```
                json_content = response_text.split('```json', 1)[1].split('```', 1)[0].strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    error_msg = f"Error parsing JSON in code block: {str(e)}"
                    logger.error(error_msg)
                    raise AIServiceError(error_msg)
            elif '```' in response_text and '```' in response_text.split('```', 1)[1]:
                # Try extracting content from a generic code block
                json_content = response_text.split('```', 1)[1].split('```', 1)[0].strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    error_msg = f"Error parsing JSON in generic code block: {str(e)}"
                    logger.error(error_msg)
                    raise AIServiceError(error_msg)
            else:
                # If not valid JSON and not in code block, raise an error
                error_msg = "Response is not valid JSON"
                logger.error(f"{error_msg}: {response_text}")
                raise AIServiceError(error_msg)
