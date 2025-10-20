"""
Load environment variables from .env file

This script helps load environment variables from .env file
"""

from dotenv import load_dotenv
import os

def load_environment():
    """Load environment variables from .env file"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Print loaded Zendesk credentials
    print("Loaded Zendesk environment variables:")
    print(f"ZENDESK_EMAIL: {os.getenv('ZENDESK_EMAIL', 'Not found')}")
    print(f"ZENDESK_API_TOKEN: {'*' * 10 if os.getenv('ZENDESK_API_TOKEN') else 'Not found'}")
    print(f"ZENDESK_SUBDOMAIN: {os.getenv('ZENDESK_SUBDOMAIN', 'Not found')}")

if __name__ == "__main__":
    load_environment()
