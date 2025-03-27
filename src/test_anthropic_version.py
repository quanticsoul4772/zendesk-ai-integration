        # Print list of available models
        try:
            print("Available models:")
            models = client.models.list()
            for model in models.data:
                print(f" - {model.id}")
        except Exception as e:
            print(f"Could not list models: {type(e).__name__}: {str(e)}")"""
Test script to verify Anthropic package compatibility.
"""

import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("anthropic_test")

# Load environment variables
load_dotenv()

def main():
    """Test Anthropic package compatibility."""
    print("\nTesting Anthropic Package Compatibility\n")
    
    # First, test that the API key is set correctly
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it in the .env file and try again.")
        return
    
    print("API key found, proceeding with tests...\n")
    
    # Import and check version
    try:
        import anthropic
        version = getattr(anthropic, "__version__", "unknown")
        print(f"Anthropic package found, version: {version}")
        
        # Test creating a client
        client = anthropic.Anthropic(api_key=api_key)
        print("Successfully created Anthropic client.")
        
        # Try a simple API call
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Hello, Claude! Can you hear me?"}],
            temperature=0.0
        )
        
        # Print response
        content = response.content[0].text
        print(f"\nAPI Response: {content}\n")
        
        # Print list of available models
        try:
            print("Available models:")
            models = client.models.list()
            for model in models.data:
                print(f" - {model.id}")
        except Exception as e:
            print(f"Could not list models: {type(e).__name__}: {str(e)}")
        
        print("Anthropic API test successful!")
        
    except ImportError:
        print("ERROR: Anthropic package is not installed.")
        print("Please install it with: pip install anthropic")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
if __name__ == "__main__":
    main()
