"""
Test script for sentiment analysis improvements.

This script tests the enhanced sentiment analysis with different sample tickets 
to verify that the model changes and prompt enhancements are working correctly.
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sentiment_test")

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from enhanced_sentiment import enhanced_analyze_ticket_content

# Sample tickets with varying sentiment characteristics
SAMPLE_TICKETS = [
    {
        "title": "Low urgency order status",
        "content": """
        Hello, I placed an order for a new workstation last week (Order #12345).
        I was just wondering if you could provide me with an estimated delivery date?
        Thank you for your help!
        """
    },
    {
        "title": "Medium urgency technical issue",
        "content": """
        Hi support team,
        
        I'm having an issue with one of our development systems. The system keeps freezing
        when running our compute workloads. I've tried rebooting and checking temperatures
        but it still happens. This is slowing down our development process and we need
        to get it resolved in the next few days if possible.
        
        System details:
        - Model: Traverse Pro X8
        - CPU: Intel i9-13900K
        - GPU: 2x RTX 4090
        
        Thanks,
        Dave
        """
    },
    {
        "title": "High urgency production issue",
        "content": """
        URGENT HELP NEEDED! Our main production render server has completely crashed
        and we have a client deliverable due tomorrow morning! This is the third system
        failure this month and it's severely impacting our business. We have a team of
        15 artists sitting idle and we're losing thousands of dollars per hour!
        
        The system was running fine last night but now it won't POST and all diagnostic
        LEDs are red. We've already tried reseating components and testing the power supply.
        
        We need someone to call us IMMEDIATELY to help troubleshoot this.
        Our business literally depends on getting this fixed TODAY.
        
        Jason Miller
        Chief Technical Officer
        """
    }
]

def display_analysis_results(title: str, analysis: Dict[str, Any]) -> None:
    """Display the analysis results in a readable format."""
    print(f"\n{'='*80}")
    print(f"ANALYSIS RESULTS: {title}")
    print(f"{'='*80}")
    
    # Extract sentiment data
    sentiment = analysis.get("sentiment", {})
    
    # Print sentiment metrics
    print(f"Sentiment Polarity: {sentiment.get('polarity', 'unknown')}")
    print(f"Urgency Level: {sentiment.get('urgency_level', 'unknown')}/5")
    print(f"Frustration Level: {sentiment.get('frustration_level', 'unknown')}/5")
    print(f"Technical Expertise: {sentiment.get('technical_expertise', 'unknown')}/5")
    
    # Print business impact
    business_impact = sentiment.get("business_impact", {})
    if business_impact and business_impact.get("detected", False):
        print(f"Business Impact: DETECTED - {business_impact.get('description', '')}")
    else:
        print("Business Impact: None detected")
    
    # Print emotions
    emotions = sentiment.get("emotions", [])
    if emotions:
        print(f"Emotions: {', '.join(emotions)}")
    
    # Print category and component
    print(f"Category: {analysis.get('category', 'unknown')}")
    print(f"Component: {analysis.get('component', 'none')}")
    print(f"Priority Score: {analysis.get('priority_score', 'unknown')}/10")
    print(f"Confidence: {analysis.get('confidence', 'unknown')}")
    
    # Print key phrases
    key_phrases = sentiment.get("key_phrases", [])
    if key_phrases:
        print("Key Phrases:")
        for phrase in key_phrases:
            print(f"  - {phrase}")
    
    print(f"{'='*80}\n")

def main():
    """Test enhanced sentiment analysis with sample tickets."""
    print("\nTesting Enhanced Sentiment Analysis with GPT-4o and Improved Prompts\n")
    
    for i, sample in enumerate(SAMPLE_TICKETS, 1):
        title = sample["title"]
        content = sample["content"]
        
        print(f"Processing sample {i}/{len(SAMPLE_TICKETS)}: {title}")
        analysis = enhanced_analyze_ticket_content(content)
        display_analysis_results(title, analysis)
    
    print("Sentiment analysis testing complete!")

if __name__ == "__main__":
    main()
