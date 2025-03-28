import os
from dotenv import load_dotenv
import sys

# Print Python version and path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check if .env file exists
env_path = os.path.join(os.getcwd(), '.env')
print(f".env file exists: {os.path.exists(env_path)}")

# Try to load environment variables
print("Attempting to load .env file...")
load_dotenv()
print("After load_dotenv() call")

# Check if API key is available
api_key = os.getenv('GOOGLE_API_KEY')
print(f"API Key found: {api_key is not None}")
if api_key:
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
else:
    print("API Key not found in environment variables")

# Check all environment variables
print("\nAll environment variables:")
for key, value in os.environ.items():
    if 'API' in key:
        print(f"{key}: {'*' * 10}")
    else:
        print(f"{key}: {value[:20] if isinstance(value, str) and len(value) > 20 else value}")