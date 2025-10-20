"""
Response Formatter

This module provides formatting for command responses.
"""

import json
import logging
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats command responses for display.

    This class handles different output formats such as text, JSON, and HTML.
    """

    def format_response(self, response: Dict[str, Any]) -> None:
        """
        Format a response based on its content and requested format.

        Args:
            response: Response dictionary to format
        """
        # If response is None or not a dictionary, do nothing
        if not response or not isinstance(response, dict):
            return

        # Check if a specific format was requested
        output_format = response.get("format")

        if not output_format:
            # No specific format requested or already handled by the command
            return

        # Format based on the requested format
        if output_format == "json":
            self._format_json(response)
        elif output_format == "html":
            self._format_html(response)
        elif output_format == "text":
            # Text format is handled by the command itself
            pass
        else:
            logger.warning(f"Unknown format requested: {output_format}")

    def _format_json(self, response: Dict[str, Any]) -> None:
        """
        Format a response as JSON.

        Args:
            response: Response to format
        """
        # Remove the format key to avoid circular references
        response_copy = response.copy()
        response_copy.pop("format", None)

        # Convert to JSON
        json_str = json.dumps(response_copy, indent=2, default=self._json_serialize)

        # Print to console
        print(json_str)

    def _format_html(self, response: Dict[str, Any]) -> None:
        """
        Format a response as HTML.

        Args:
            response: Response to format
        """
        # Build HTML content
        html = "<html>\n<head>\n"
        html += "  <title>Zendesk AI Integration - Analysis</title>\n"
        html += "  <style>\n"
        html += "    body { font-family: Arial, sans-serif; margin: 20px; }\n"
        html += "    h1 { color: #03363D; }\n"
        html += "    h2 { color: #03363D; margin-top: 20px; }\n"
        html += "    table { border-collapse: collapse; width: 100%; margin-top: 20px; }\n"
        html += "    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n"
        html += "    th { background-color: #f2f2f2; }\n"
        html += "    .positive { color: green; }\n"
        html += "    .negative { color: red; }\n"
        html += "    .neutral { color: gray; }\n"
        html += "    .high { color: red; font-weight: bold; }\n"
        html += "    .medium { color: orange; }\n"
        html += "    .low { color: green; }\n"
        html += "  </style>\n"
        html += "</head>\n<body>\n"

        # Add title based on command type
        if "ticket_id" in response:
            html += f"<h1>Ticket Analysis - #{response['ticket_id']}</h1>\n"
        elif "view_id" in response:
            html += f"<h1>View Analysis - #{response['view_id']}</h1>\n"
        elif "view_name" in response:
            html += f"<h1>View Analysis - {response['view_name']}</h1>\n"
        else:
            html += "<h1>Zendesk AI Integration - Analysis</h1>\n"

        # Add analysis data
        if "analysis" in response:
            self._add_analysis_to_html(html, response["analysis"])
        elif "analyses_count" in response:
            html += f"<p>Analyzed {response['analyses_count']} tickets</p>\n"

            # Add sentiment distribution if available
            if "sentiment_distribution" in response:
                html += "<h2>Sentiment Distribution</h2>\n"
                html += "<table>\n"
                html += "  <tr><th>Sentiment</th><th>Count</th></tr>\n"

                for sentiment, count in response["sentiment_distribution"].items():
                    sentiment_class = ""
                    if sentiment.lower() == "positive":
                        sentiment_class = "positive"
                    elif sentiment.lower() == "negative":
                        sentiment_class = "negative"
                    elif sentiment.lower() == "neutral":
                        sentiment_class = "neutral"

                    html += f"  <tr><td class='{sentiment_class}'>{sentiment}</td><td>{count}</td></tr>\n"

                html += "</table>\n"

        # Close HTML tags
        html += "</body>\n</html>"

        # Print to console
        print(html)

        # Optionally save to file if output file is specified
        output_file = response.get("output")
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"HTML report saved to {output_file}")
            except Exception as e:
                logger.error(f"Error saving HTML report to {output_file}: {e}")
                print(f"Error saving HTML report: {e}")

    def _add_analysis_to_html(self, html: str, analysis: Dict[str, Any]) -> str:
        """
        Add analysis data to HTML content.

        Args:
            html: HTML content
            analysis: Analysis data

        Returns:
            Updated HTML content
        """
        html += "<h2>Analysis Results</h2>\n"
        html += "<table>\n"

        # Add subject if available
        if "subject" in analysis:
            html += f"  <tr><th>Subject</th><td>{analysis['subject']}</td></tr>\n"

        # Add sentiment
        if "sentiment" in analysis:
            sentiment = analysis["sentiment"]
            sentiment_class = ""
            if sentiment.lower() == "positive":
                sentiment_class = "positive"
            elif sentiment.lower() == "negative":
                sentiment_class = "negative"
            elif sentiment.lower() == "neutral":
                sentiment_class = "neutral"

            html += f"  <tr><th>Sentiment</th><td class='{sentiment_class}'>{sentiment}</td></tr>\n"

        # Add category
        if "category" in analysis:
            html += f"  <tr><th>Category</th><td>{analysis['category']}</td></tr>\n"

        # Add priority
        if "priority" in analysis:
            priority = analysis["priority"]
            priority_class = ""
            if isinstance(priority, (int, float)):
                if priority >= 7:
                    priority_class = "high"
                elif priority >= 4:
                    priority_class = "medium"
                else:
                    priority_class = "low"

            html += f"  <tr><th>Priority</th><td class='{priority_class}'>{priority}</td></tr>\n"

        # Add hardware components
        if "hardware_components" in analysis and analysis["hardware_components"]:
            components = ", ".join(analysis["hardware_components"])
            html += f"  <tr><th>Hardware Components</th><td>{components}</td></tr>\n"

        # Add business impact
        if "business_impact" in analysis and analysis["business_impact"]:
            html += f"  <tr><th>Business Impact</th><td class='high'>{analysis['business_impact']}</td></tr>\n"

        # Add tags
        if "tags" in analysis and analysis["tags"]:
            tags = ", ".join(analysis["tags"])
            html += f"  <tr><th>Tags</th><td>{tags}</td></tr>\n"

        html += "</table>\n"

        return html

    def _json_serialize(self, obj):
        """
        JSON serialization for objects that aren't serializable by default.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation of the object
        """
        # Handle datetime objects
        if hasattr(obj, "isoformat"):
            return obj.isoformat()

        # Handle custom objects with to_dict method
        if hasattr(obj, "to_dict"):
            return obj.to_dict()

        # Default to string representation
        return str(obj)
