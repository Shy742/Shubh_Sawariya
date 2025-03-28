import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_API_KEY')
print(f'API Key found: {api_key is not None}')
if api_key:
    print(f'API Key: {api_key[:5]}...{api_key[-5:]}')

# Test the API key
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content('Hello, are you working?')
    print('API Test Result: Success')
    print(response.text)
except Exception as e:
    print(f'API Test Error: {str(e)}')