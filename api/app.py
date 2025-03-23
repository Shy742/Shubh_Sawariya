# ... existing imports ...

# Remove or comment out load_dotenv() since Render uses environment variables
# load_dotenv()

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

# ... rest of your code ...

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)