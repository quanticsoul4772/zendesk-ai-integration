import openai  # type: ignore

# Simple test to verify the import works
print("OpenAI package imported successfully")
print(f"OpenAI version: {openai.__version__}")

# Initialize client (without making any API calls)
client = openai.OpenAI(api_key="test_key")
print("Client initialized successfully")