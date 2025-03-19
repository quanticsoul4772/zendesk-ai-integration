"""
Test script for the AI service module.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the AI service module
# Use relative import since we're in the same package
try:
    # When running as a module
    from .ai_service import analyze_ticket_content
except ImportError:
    # When running directly
    from ai_service import analyze_ticket_content

def main():
    """Test the AI service functionality."""
    print("Testing AI service module...")
    
    # Test with a sample ticket
    sample_ticket = """
    Hello support team,
    
    I've been trying to use your product for the past week and I'm really impressed with the features.
    However, I'm having trouble with the export functionality. When I try to export my data to CSV,
    the application crashes. Could you please help me resolve this issue?
    
    Thanks,
    John
    """
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY environment variable is not set.")
        print("The analysis will fail unless you set this environment variable.")
        print("For testing purposes only, you can set it temporarily:")
        print("  - Windows (PowerShell): $env:OPENAI_API_KEY = 'your-api-key'")
        print("  - Windows (CMD): set OPENAI_API_KEY=your-api-key")
        print("  - Linux/macOS: export OPENAI_API_KEY=your-api-key")
        return
    
    print("\nAnalyzing sample ticket...")
    result = analyze_ticket_content(sample_ticket)
    
    print("\nAnalysis Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()