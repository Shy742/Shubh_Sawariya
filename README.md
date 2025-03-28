# BRM Financial Analyzer

A web application that analyzes financial documents using Google's Gemini AI. The application extracts financial data from PDF documents and visualizes it using Sankey diagrams.

## Features

- PDF document upload and processing
- Financial data extraction using Gemini AI
- Visualization of financial data using Sankey diagrams
- Chat interface for asking questions about the financial data

## Deployment

This application is configured for deployment on Render.com. The deployment is set up to use environment variables for configuration, so no local setup is required for end users.

### Deployment Steps (for administrators)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following environment variables in the Render dashboard:
   - `GOOGLE_API_KEY`: Your Google Gemini API key
4. Deploy the application

### Accessing the Application

Once deployed, the application will be available at the URL provided by Render. No additional setup is required for end users.

## Local Development

If you want to run the application locally for development:

1. Clone the repository
2. Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python app.py`
5. Access the application at `http://localhost:5000`

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- AI: Google Gemini AI
- Visualization: D3.js with D3-Sankey
- PDF Processing: PyPDF2