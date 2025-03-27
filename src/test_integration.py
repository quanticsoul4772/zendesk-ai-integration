"""
Real integration test for both OpenAI and Claude services.

This test runs real API calls to both OpenAI and Claude to ensure
that all parsing enhancements work correctly with real responses.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_test")

def main():
    """Run integration tests for both AI services."""
    print("\nRunning AI Service Integration Tests\n")
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key:
        print("WARNING: OPENAI_API_KEY not set in .env file!")
    
    if not claude_key:
        print("WARNING: ANTHROPIC_API_KEY not set in .env file!")
    
    if not openai_key and not claude_key:
        print("ERROR: No API keys found. Please set at least one in your .env file.")
        return
    
    # Import OpenAI service if key exists
    if openai_key:
        print("\n=== Testing OpenAI Service ===\n")
        
        try:
            from ai_service import analyze_ticket_content as openai_analyze
            
            # Test with a simple ticket
            sample_ticket = """
            Hello, I have an issue with my server not booting. The motherboard lights up
            but there's no POST beep and no display. I've already tried reseating all 
            components and clearing CMOS. This is quite urgent as we have a deadline tomorrow.
            """
            
            print("Sending sample ticket to OpenAI...")
            result = openai_analyze(sample_ticket)
            
            # Display result with special attention to parsed values
            print("\nOpenAI Analysis Result:")
            print(f"Sentiment: {result.get('sentiment')}")
            print(f"Category: {result.get('category')}")
            print(f"Component: {result.get('component')}")
            print(f"Confidence: {result.get('confidence')}")
            
            # Check if any error occurred
            if 'error' in result:
                print(f"ERROR: {result.get('error')}")
            
            # Verify if parsing was successful
            if result.get('sentiment') != 'unknown' and result.get('category') != 'uncategorized':
                print("\nSUCCESS: OpenAI parsing successful!")
            else:
                print("\nWARNING: OpenAI parsing may have issues!")
            
        except Exception as e:
            print(f"ERROR testing OpenAI service: {e}")
    
    # Import Claude service if key exists
    if claude_key:
        print("\n=== Testing Claude Service ===\n")
        
        try:
            from claude_service import analyze_ticket_content as claude_analyze
            from claude_enhanced_sentiment import enhanced_analyze_ticket_content as claude_enhanced_analyze
            
            # Test with a simple ticket
            sample_ticket = """
            Hello, I have an issue with my server not booting. The motherboard lights up
            but there's no POST beep and no display. I've already tried reseating all 
            components and clearing CMOS. This is quite urgent as we have a deadline tomorrow.
            """
            
            print("Sending sample ticket to Claude (basic)...")
            result = claude_analyze(sample_ticket)
            
            # Display result with special attention to parsed values
            print("\nClaude Basic Analysis Result:")
            print(f"Sentiment: {result.get('sentiment')}")
            print(f"Category: {result.get('category')}")
            print(f"Component: {result.get('component')}")
            print(f"Confidence: {result.get('confidence')}")
            
            # Check if any error occurred
            if 'error' in result:
                print(f"ERROR: {result.get('error')}")
            
            # Verify if parsing was successful
            if result.get('sentiment') != 'unknown' and result.get('category') != 'uncategorized':
                print("\nSUCCESS: Claude basic parsing successful!")
            else:
                print("\nWARNING: Claude basic parsing may have issues!")
            
            # Test enhanced sentiment analysis
            print("\nSending sample ticket to Claude (enhanced)...")
            enhanced_result = claude_enhanced_analyze(sample_ticket)
            
            # Display result with special attention to parsed values
            print("\nClaude Enhanced Analysis Result:")
            sentiment = enhanced_result.get('sentiment', {})
            
            if isinstance(sentiment, dict):
                print(f"Sentiment Polarity: {sentiment.get('polarity')}")
                print(f"Urgency Level: {sentiment.get('urgency_level')}/5")
                print(f"Frustration Level: {sentiment.get('frustration_level')}/5")
                print(f"Business Impact: {'Detected' if sentiment.get('business_impact', {}).get('detected', False) else 'None'}")
            else:
                print(f"Sentiment: {sentiment}")
            
            print(f"Category: {enhanced_result.get('category')}")
            print(f"Component: {enhanced_result.get('component')}")
            print(f"Priority Score: {enhanced_result.get('priority_score')}/10")
            print(f"Confidence: {enhanced_result.get('confidence')}")
            
            # Check if any error occurred
            if 'error' in enhanced_result:
                print(f"ERROR: {enhanced_result.get('error')}")
            
            # Verify if parsing was successful
            if isinstance(sentiment, dict) and sentiment.get('polarity') != 'unknown':
                print("\nSUCCESS: Claude enhanced parsing successful!")
            else:
                print("\nWARNING: Claude enhanced parsing may have issues!")
            
        except Exception as e:
            print(f"ERROR testing Claude service: {e}")
    
    print("\nIntegration tests complete!")

if __name__ == "__main__":
    main()
