
# Google API Key Setup Guide

## Issue Identified
Your application is encountering an error because the Google API key is invalid. The error message `API_KEY_INVALID` indicates that the key is either incorrect, expired, or doesn't have the proper permissions.

## How to Get a Valid Google API Key

1. **Go to Google AI Studio**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account

2. **Create a New API Key**:
   - Click on "Get API key" or "Create API key"
   - Follow the prompts to create a new key
   - Make sure to enable the Gemini API for your project

3. **Copy Your New API Key**:
   - Once created, copy the API key to your clipboard

4. **Update Your .env File**:
   - Open the `.env` file in your project directory
   - Replace the placeholder text with your actual API key:
     ```
     GOOGLE_API_KEY=your_actual_api_key_here
     ```
   - Save the file

5. **Restart Your Application**:
   - Stop the current running Flask server
   - Start it again with `python app.py`

## API Key Security Best Practices

- **Never share your API key** publicly or commit it to public repositories
- Consider using environment variables or a secure vault for production environments
- Regularly rotate your API keys for better security
- Set appropriate usage limits in the Google Cloud Console

## Troubleshooting

If you continue to experience issues after updating your API key:

1. Verify that the API key has been properly copied without any extra spaces
2. Check if your Google account has billing enabled (some API features may require this)
3. Ensure that the Gemini API is enabled for your project
4. Check for any quotas or rate limits that might be affecting your usage

For more information, visit the [Google AI documentation](https://ai.google.dev/docs).