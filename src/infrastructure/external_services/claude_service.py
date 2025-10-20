"""
Claude Service Adapter

This module provides an implementation of the AIService interface using the Anthropic Claude API.
"""

import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional

from src.domain.interfaces.ai_service_interfaces import (
    AIService,
    AIServiceError,
    ContentFilterError,
    EnhancedAIService,
    RateLimitError,
    TokenLimitError,
)
from src.infrastructure.utils.retry import with_retry

# Set up logging
logger = logging.getLogger(__name__)


class ClaudeService(EnhancedAIService):
    """
    Implementation of the EnhancedAIService interface using the Anthropic Claude API.

    This service uses the Anthropic Claude API to analyze ticket content and sentiment,
    with enhanced capabilities like business impact analysis and response suggestions.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the Claude service.

        Args:
            api_key: Anthropic API key (optional, defaults to environment variable)
            model: Claude model to use (default: claude-3-haiku-20240307)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            logger.warning("Anthropic API key not provided - API calls will fail")

        # Initialize the client lazily when needed
        self._client = None

    @property
    def client(self):
        """Get the Anthropic client, initializing it if necessary."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("Anthropic package is not installed. Install it with: pip install anthropic>=0.7.0")
                raise AIServiceError("Anthropic package is not installed")
            except Exception as e:
                logger.error(f"Error initializing Anthropic client: {str(e)}")
                raise AIServiceError(f"Error initializing Anthropic client: {str(e)}")

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
                    "emotions": [],
                    "business_impact": {
                        "detected": False,
                        "impact_areas": [],
                        "severity": 0
                    }
                },
                "category": "uncategorized",
                "component": "none",
                "priority": "low",
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Analyzing content with Claude (length: {len(content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        Analyze the following customer message from Exxact Corporation (a hardware systems manufacturer) and provide a detailed analysis as JSON.

        I need you to output a JSON object with the following structure:

        {{
          "category": "[system/resale_component/hardware_issue/system_component/so_released_to_warehouse/wo_released_to_warehouse/technical_support/rma/software_issue/general_inquiry]",
          "component": "[gpu/cpu/drive/memory/power_supply/motherboard/cooling/display/network/none]",
          "priority": "[high/medium/low]",
          "sentiment": {{
            "polarity": "[positive/negative/neutral/unknown]",
            "urgency_level": [1-5 scale, where 1 is lowest urgency and 5 is highest],
            "frustration_level": [1-5 scale, where 1 is not frustrated and 5 is extremely frustrated],
            "emotions": [array of emotions detected in the message],
            "business_impact": {{
              "detected": [true/false],
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

        Customer message:
        {content}

        Please provide only valid JSON without any additional text, prefixes, or explanation.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score - Claude tends to be highly accurate
            result["confidence"] = 0.95

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
                    "emotions": [],
                    "business_impact": {
                        "detected": False,
                        "impact_areas": [],
                        "severity": 0
                    }
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
                "business_impact": {
                    "detected": False,
                    "impact_areas": [],
                    "severity": 0
                },
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Analyzing sentiment with Claude (length: {len(content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        Analyze the sentiment of the following customer message.

        I need you to output a JSON object with the following structure:

        {{
          "polarity": "[positive/negative/neutral/unknown]",
          "urgency_level": [1-5 scale, where 1 is lowest urgency and 5 is highest],
          "frustration_level": [1-5 scale, where 1 is not frustrated and 5 is extremely frustrated],
          "emotions": [array of emotions detected in the message],
          "business_impact": {{
            "detected": [true/false],
            "impact_areas": [array of business areas affected, if any],
            "severity": [0-5 scale, where 0 is no impact and 5 is severe impact]
          }}
        }}

        Message:
        {content}

        Please provide only valid JSON without any additional text, prefixes, or explanation.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Process the response
            result_json = self._process_response(response)

            # Extract sentiment data
            sentiment = result_json.get("sentiment", result_json)

            # Add confidence score
            sentiment["confidence"] = 0.95

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

        logger.info(f"Categorizing ticket with Claude (length: {len(content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        Categorize the following customer message from Exxact Corporation (a hardware systems manufacturer).

        I need you to output a JSON object with the following structure:

        {{
          "category": "[system/resale_component/hardware_issue/system_component/so_released_to_warehouse/wo_released_to_warehouse/technical_support/rma/software_issue/general_inquiry]",
          "component": "[gpu/cpu/drive/memory/power_supply/motherboard/cooling/display/network/none]",
          "priority": "[high/medium/low]",
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

        Customer message:
        {content}

        Please provide only valid JSON without any additional text, prefixes, or explanation.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score
            result["confidence"] = 0.95

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

    @with_retry(max_retries=3, retry_on=[Exception])
    def analyze_business_impact(self, content: str) -> Dict[str, Any]:
        """
        Analyze the business impact of the content.

        Args:
            content: The content to analyze

        Returns:
            Dictionary with business impact analysis results

        Raises:
            AIServiceError: If an error occurs during analysis
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for business impact analysis")
            return {
                "detected": False,
                "impact_areas": [],
                "severity": 0,
                "explanation": "Empty content provided",
                "confidence": 0.0
            }

        logger.info(f"Analyzing business impact with Claude (length: {len(content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        Analyze the following customer message from Exxact Corporation (a hardware systems manufacturer) to determine its business impact.

        I need you to output a JSON object with the following structure:

        {{
          "detected": [true/false],
          "impact_areas": [array of business areas affected, if any],
          "severity": [0-5 scale, where 0 is no impact and 5 is severe impact],
          "explanation": "[Brief explanation of the business impact]",
          "potential_revenue_impact": [estimated dollar impact if discernible, or "unknown"],
          "urgency": [1-5 scale, where 1 is lowest urgency and 5 is highest]
        }}

        Customer message:
        {content}

        Please provide only valid JSON without any additional text, prefixes, or explanation.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score
            result["confidence"] = 0.95

            logger.info(f"Business impact analysis complete: detected={result['detected']}, severity={result['severity']}")

            return result
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and wrap in a generic AIServiceError
            logger.exception(f"Unexpected error analyzing business impact: {str(e)}")
            return {
                "detected": False,
                "impact_areas": [],
                "severity": 0,
                "explanation": f"Error analyzing business impact: {str(e)}",
                "potential_revenue_impact": "unknown",
                "urgency": 1,
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }

    @with_retry(max_retries=3, retry_on=[Exception])
    def generate_response_suggestion(self, ticket_content: str) -> str:
        """
        Generate a suggested response for a ticket.

        Args:
            ticket_content: The ticket content

        Returns:
            Suggested response text

        Raises:
            AIServiceError: If an error occurs during generation
        """
        if not ticket_content or not ticket_content.strip():
            logger.warning("Empty content provided for response suggestion")
            return "I'm unable to suggest a response for empty content."

        logger.info(f"Generating response suggestion with Claude (length: {len(ticket_content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        You are a customer support representative at Exxact Corporation, a manufacturer of high-performance computing systems and components.

        Generate a helpful, professional response to the following customer message. The response should:
        1. Be empathetic and acknowledge any issues or concerns
        2. Provide clear, accurate information
        3. Include next steps or actions if appropriate
        4. Maintain a supportive and solution-oriented tone
        5. Be concise but thorough

        Customer message:
        {ticket_content}

        Write only the response text without any additional commentary, explanations, or prefixes.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Return the raw text (no need to parse as JSON)
            logger.info(f"Generated response suggestion ({len(response)} chars)")

            return response
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and return a simple message
            logger.exception(f"Unexpected error generating response suggestion: {str(e)}")
            return f"Failed to generate response suggestion: {str(e)}"

    @with_retry(max_retries=3, retry_on=[Exception])
    def extract_ticket_data(self, content: str) -> Dict[str, Any]:
        """
        Extract structured data from ticket content.

        Args:
            content: The ticket content

        Returns:
            Dictionary with extracted data

        Raises:
            AIServiceError: If an error occurs during extraction
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for data extraction")
            return {
                "entities": [],
                "product_mentions": [],
                "technical_specifications": {},
                "request_type": "unknown",
                "confidence": 0.0,
                "error": "Empty content provided"
            }

        logger.info(f"Extracting structured data with Claude (length: {len(content)} chars)")

        # Craft the prompt for Claude
        prompt = f"""
        Extract structured data from the following customer message sent to Exxact Corporation (a hardware systems manufacturer).

        I need you to output a JSON object with the following structure:

        {{
          "entities": [array of named entities like people, companies, products mentioned],
          "product_mentions": [array of specific product names or models mentioned],
          "technical_specifications": {{
            "cpu": "[any CPU specifications mentioned]",
            "gpu": "[any GPU specifications mentioned]",
            "memory": "[any memory specifications mentioned]",
            "storage": "[any storage specifications mentioned]",
            "other": "[any other technical specifications mentioned]"
          }},
          "request_type": "[inquiry/support/purchase/complaint/return/other]",
          "action_items": [array of specific actions requested or required]
        }}

        Customer message:
        {content}

        Please provide only valid JSON without any additional text, prefixes, or explanation.
        """

        try:
            # Call the Claude API
            response = self._call_api(prompt)

            # Process the response
            result = self._process_response(response)

            # Add confidence score
            result["confidence"] = 0.95

            logger.info(f"Data extraction complete: found {len(result.get('entities', []))} entities, {len(result.get('product_mentions', []))} products")

            return result
        except AIServiceError as e:
            # Re-raise specific AI service errors
            raise
        except Exception as e:
            # Log unexpected errors and wrap in a generic AIServiceError
            logger.exception(f"Unexpected error extracting data: {str(e)}")
            return {
                "entities": [],
                "product_mentions": [],
                "technical_specifications": {},
                "request_type": "unknown",
                "action_items": [],
                "confidence": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _call_api(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4000) -> str:
        """
        Call the Claude API with retry and error handling logic.

        Args:
            prompt: The text prompt to send to the API
            temperature: Temperature setting (default: 0.0)
            max_tokens: Maximum tokens in the response (default: 4000)

        Returns:
            Response text from the API

        Raises:
            RateLimitError: If rate limits are exceeded
            TokenLimitError: If token limits are exceeded
            ContentFilterError: If content violates usage policies
            AIServiceError: For other API errors
        """
        try:
            # Import error types from Anthropic only when needed to avoid direct dependencies
            from anthropic import (
                APIConnectionError,
                APIError,
                APITimeoutError,
                BadRequestError,
            )
            from anthropic import RateLimitError as AnthropicRateLimitError

            # Call the API
            logger.debug(f"Calling Claude API with model {self.model}")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract the content from the message
            content = message.content[0].text

            return content
        except AnthropicRateLimitError as e:
            error_msg = f"Claude rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise RateLimitError(error_msg)
        except BadRequestError as e:
            error_str = str(e).lower()
            # Check if it's a token limit issue
            if "token" in error_str and "limit" in error_str:
                error_msg = f"Claude token limit exceeded: {str(e)}"
                logger.error(error_msg)
                raise TokenLimitError(error_msg)
            # Check if it's a content filter issue
            elif "content" in error_str and "filter" in error_str:
                error_msg = f"Claude content filter triggered: {str(e)}"
                logger.error(error_msg)
                raise ContentFilterError(error_msg)
            # Other bad request errors
            else:
                error_msg = f"Claude bad request error: {str(e)}"
                logger.error(error_msg)
                raise AIServiceError(error_msg)
        except APITimeoutError as e:
            error_msg = f"Claude API timeout: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg)
        except (APIError, APIConnectionError) as e:
            error_msg = f"Claude API error: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg)
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error calling Claude: {str(e)}"
            logger.exception(error_msg)
            raise AIServiceError(error_msg)

    def _process_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process the response from the Claude API.

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
