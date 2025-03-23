import os
from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from cors_middleware import setup_cors_middleware
import json
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder="../public", static_url_path="")
setup_cors_middleware(app)

# Load environment variables
load_dotenv()

# Configure Gemini AI
try:
    logger.info("Initializing Gemini AI model...")
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not found")
        raise ValueError("GOOGLE_API_KEY environment variable not found")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    logger.info("Successfully initialized Gemini AI model")
except Exception as e:
    logger.error(f"Error initializing Gemini model: {str(e)}")
    model = None

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)