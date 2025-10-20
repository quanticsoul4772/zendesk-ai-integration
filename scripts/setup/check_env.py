import os

# Check for Zendesk credentials
print("Checking for Zendesk credentials...")
print(f"ZENDESK_EMAIL: {'*****' if 'ZENDESK_EMAIL' in os.environ else 'Not found'}")
print(f"ZENDESK_API_TOKEN: {'*****' if 'ZENDESK_API_TOKEN' in os.environ else 'Not found'}")
print(f"ZENDESK_SUBDOMAIN: {'*****' if 'ZENDESK_SUBDOMAIN' in os.environ else 'Not found'}")

# Check for MongoDB and AI service credentials
print(f"MONGODB_URI: {'*****' if 'MONGODB_URI' in os.environ else 'Not found'}")
print(f"OPENAI_API_KEY: {'*****' if 'OPENAI_API_KEY' in os.environ else 'Not found'}")
print(f"CLAUDE_API_KEY: {'*****' if 'CLAUDE_API_KEY' in os.environ else 'Not found'}")

# Print available environment variable keys (without values for security)
print("\nAll environment variables available to Python:")
for key in os.environ.keys():
    print(f"- {key}")
