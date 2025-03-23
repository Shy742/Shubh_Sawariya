import os
from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from cors_middleware import setup_cors_middleware
import json
import logging
# Initialize Flask app (only once)
app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public'),
    static_url_path=''
)

# Update CORS configuration
def setup_cors_middleware(app):
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    return app

app = setup_cors_middleware(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Remove this duplicate initialization:
# app = Flask(__name__)
# setup_cors_middleware(app)

def extract_text_from_pdf(pdf_file):
    logger.info(f"Starting PDF text extraction for file: {pdf_file.filename}")
    try:
        reader = PdfReader(pdf_file)
        logger.info(f"Successfully created PdfReader object. Number of pages: {len(reader.pages)}")
        text = ''
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            logger.info(f"Extracted text from page {i+1}. Text length: {len(page_text)}")
            text += page_text + '\n'
        logger.info(f"Total extracted text length: {len(text)}")
        return text
    except Exception as e:
        logger.error(f"Error in PDF text extraction: {str(e)}")
        raise

def parse_financial_data(text):
    logger.info("Starting financial data parsing...")
    # Enhanced prompt for Gemini AI to extract financial data with detailed categorization
    prompt = f"""Extract financial data from the following text. Focus on:
    1. Balance Sheet items with detailed categorization:
       - Current Assets (e.g., Cash, Accounts Receivable, Inventory)
       - Non-Current Assets (e.g., Property, Plant, Equipment, Intangible Assets)
       - Current Liabilities (e.g., Accounts Payable, Short-term Debt)
       - Non-Current Liabilities (e.g., Long-term Debt, Deferred Tax Liabilities)
       - Equity components (e.g., Common Stock, Retained Earnings)
    2. Profit & Loss items with detailed categorization:
       - Operating Revenue (e.g., Revenue from Operations, Sales Revenue, Service Revenue)
       - Non-Operating Revenue (e.g., Other Income, Interest Income, Dividend Income)
       - Operating Expenses (e.g., Cost of Materials Consumed, Employees Benefit Expenses, Cost of Goods Sold, Salaries, Rent, Changes in Inventories of WIP & Finished Goods)
       - Non-Operating Expenses (e.g., Finance Cost, Interest Expense, Loss on Sale of Assets, Depreciation & Amortization Expenses if not part of operations)

    Important rules:
    - All amounts must be numeric values (convert text/string amounts to numbers)
    - Remove any currency symbols (e.g., $, €) and commas from amounts
    - Ensure all values are positive numbers
    - Use 0 if an amount cannot be determined
    - Categorize revenue and expenses into operating and non-operating based on their nature:
      - Operating Revenue: Directly related to the core business activities (e.g., sales of goods or services)
      - Non-Operating Revenue: Not related to core business (e.g., interest earned, dividends, other income)
      - Operating Expenses: Directly related to core business operations (e.g., cost of materials, employee salaries, changes in inventory)
      - Non-Operating Expenses: Not related to core operations (e.g., finance costs, interest expenses, depreciation if not operational)
    - If an item cannot be categorized, place it in the appropriate default category (e.g., use 'operating' for revenue/expenses if unclear)
    - For expenses labeled as "Other Expenses", attempt to classify them as operating unless they clearly relate to non-operating activities (e.g., interest or finance costs)

    Format the response as a valid JSON object with this type of structure:
    {{
        "balance_sheet": {{
            "assets": {{
                "current": [
                    {{"name": "item_name", "value": numeric_amount}}
                ],
                "non_current": [
                    {{"name": "item_name", "value": numeric_amount}}
                ]
            }},
            "liabilities": {{
                "current": [
                    {{"name": "item_name", "value": numeric_amount}}
                ],
                "non_current": [
                    {{"name": "item_name", "value": numeric_amount}}
                ]
            }},
            "equity": [
                {{"name": "item_name", "value": numeric_amount}}
            ]
        }},
        "income_statement": {{
            "revenue": {{
                "operating": [
                    {{"name": "item_name", "value": numeric_amount}}
                ],
                "non_operating": [
                    {{"name": "item_name", "value": numeric_amount}}
                ]
            }},
            "expenses": {{
                "operating": [
                    {{"name": "item_name", "value": numeric_amount}}
                ],
                "non_operating": [
                    {{"name": "item_name", "value": numeric_amount}}
                ]
            }}
        }}
    }}

    Example output for clarity:
    {{
        "balance_sheet": {{
            "assets": {{
                "current": [
                    {{"name": "Cash", "value": 5000}},
                    {{"name": "Accounts Receivable", "value": 3000}}
                ],
                "non_current": [
                    {{"name": "Property", "value": 10000}},
                    {{"name": "Equipment", "value": 7000}}
                ]
            }},
            "liabilities": {{
                "current": [
                    {{"name": "Accounts Payable", "value": 2000}}
                ],
                "non_current": [
                    {{"name": "Long-term Debt", "value": 5000}}
                ]
            }},
            "equity": [
                {{"name": "Common Stock", "value": 8000}},
                {{"name": "Retained Earnings", "value": 4000}}
            ]
        }},
        "income_statement": {{
            "revenue": {{
                "operating": [
                    {{"name": "Revenue from Operations", "value": 15000}}
                ],
                "non_operating": [
                    {{"name": "Other Income", "value": 500}}
                ]
            }},
            "expenses": {{
                "operating": [
                    {{"name": "Cost of Materials Consumed", "value": 8000}},
                    {{"name": "Employees Benefit Expenses", "value": 3000}},
                    {{"name": "Changes in Inventories of WIP & Finished Goods", "value": 1000}}
                ],
                "non_operating": [
                    {{"name": "Finance Cost", "value": 1000}},
                    {{"name": "Depreciation & Amortization Expenses", "value": 500}}
                ]
            }}
        }}
    }}

    Text to analyze: {text}
    """
    
    try:
        if not model:
            logger.error("Error: Gemini AI model not initialized")
            raise Exception("Gemini AI model not initialized properly")
            
        logger.info("Sending request to Gemini AI...")
        try:
            response = model.generate_content(prompt)
            logger.info(f"Received response from Gemini AI: {response.text}")
        except Exception as api_error:
            logger.error(f"Error calling Gemini AI API: {str(api_error)}")
            raise Exception(f"Failed to process text with AI: {str(api_error)}")
        
        if not response.text:
            logger.error("Error: Empty response from Gemini AI")
            raise ValueError("Empty response from Gemini AI")
            
        # Clean up the response text to ensure it's valid JSON
        cleaned_text = response.text.strip()
        logger.info(f"Cleaned text (before processing): {cleaned_text}")
        
        # Remove any markdown code block markers if present
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '')
        # Replace single quotes with double quotes for JSON compatibility
        cleaned_text = cleaned_text.replace("'", '"')
        
        logger.info(f"Cleaned text (after processing): {cleaned_text}")
        
        # Validate JSON structure and numeric values
        try:
            data = json.loads(cleaned_text)
            logger.info(f"Successfully parsed JSON data: {json.dumps(data, indent=2)}")
            
            # Validate required structure and data format
            required_sections = ['balance_sheet', 'income_statement']
            for section in required_sections:
                if section not in data:
                    logger.error(f"Error: Missing required section '{section}' in data")
                    raise ValueError(f"Missing required section: {section}")
                if not isinstance(data[section], dict):
                    logger.error(f"Error: Invalid format for section '{section}', expected object but got {type(data[section])}")
                    raise ValueError(f"Invalid format for section: {section}")
            
            # Validate subsections for balance_sheet
            balance_sheet_subsections = {
                'assets': ['current', 'non_current'],
                'liabilities': ['current', 'non_current'],
                'equity': None  # equity is a list, not a dict with subcategories
            }
            for subsection, subcategories in balance_sheet_subsections.items():
                if subsection not in data['balance_sheet']:
                    logger.error(f"Error: Missing subsection '{subsection}' in balance_sheet")
                    raise ValueError(f"Missing subsection '{subsection}' in balance_sheet")
                if subsection == 'equity':
                    if not isinstance(data['balance_sheet'][subsection], list):
                        logger.error(f"Error: Invalid format for 'equity', expected array but got {type(data['balance_sheet'][subsection])}")
                        raise ValueError(f"Invalid format for 'equity' in balance_sheet")
                else:
                    if not isinstance(data['balance_sheet'][subsection], dict):
                        logger.error(f"Error: Invalid format for '{subsection}', expected object but got {type(data['balance_sheet'][subsection])}")
                        raise ValueError(f"Invalid format for '{subsection}' in balance_sheet")
                    for subcategory in subcategories:
                        if subcategory not in data['balance_sheet'][subsection]:
                            logger.warning(f"Warning: Missing subcategory '{subcategory}' in {subsection}, initializing as empty list")
                            data['balance_sheet'][subsection][subcategory] = []
                        if not isinstance(data['balance_sheet'][subsection][subcategory], list):
                            logger.error(f"Error: Invalid format for '{subcategory}' in {subsection}, expected array but got {type(data['balance_sheet'][subsection][subcategory])}")
                            raise ValueError(f"Invalid format for '{subcategory}' in {subsection}")
            
            # Validate subsections for income_statement
            income_statement_subsections = {
                'revenue': ['operating', 'non_operating'],
                'expenses': ['operating', 'non_operating']
            }
            for subsection, subcategories in income_statement_subsections.items():
                if subsection not in data['income_statement']:
                    logger.error(f"Error: Missing subsection '{subsection}' in income_statement")
                    raise ValueError(f"Missing subsection '{subsection}' in income_statement")
                if not isinstance(data['income_statement'][subsection], dict):
                    logger.error(f"Error: Invalid format for '{subsection}', expected object but got {type(data['income_statement'][subsection])}")
                    raise ValueError(f"Invalid format for '{subsection}' in income_statement")
                for subcategory in subcategories:
                    if subcategory not in data['income_statement'][subsection]:
                        logger.warning(f"Warning: Missing subcategory '{subcategory}' in {subsection}, initializing as empty list")
                        data['income_statement'][subsection][subcategory] = []
                    if not isinstance(data['income_statement'][subsection][subcategory], list):
                        logger.error(f"Error: Invalid format for '{subcategory}' in {subsection}, expected array but got {type(data['income_statement'][subsection][subcategory])}")
                        raise ValueError(f"Invalid format for '{subcategory}' in {subsection}")
            
            # Function to convert value to numeric
            def convert_to_numeric(value):
                if isinstance(value, (int, float)):
                    return value
                try:
                    # Remove currency symbols and commas
                    cleaned_value = str(value).replace('$', '').replace(',', '').strip()
                    # Handle empty or invalid values
                    if not cleaned_value or cleaned_value.lower() in ['na', 'n/a', '-']:
                        logger.warning(f"Warning: Empty or invalid value '{value}', defaulting to 0")
                        return 0
                    # Convert to float
                    numeric_value = float(cleaned_value)
                    logger.info(f"Successfully converted '{value}' to numeric value: {numeric_value}")
                    return numeric_value
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting value '{value}' to numeric: {str(e)}")
                    return 0
            
            # Process and validate numeric values recursively
            def process_items(items):
                for item in items:
                    if not isinstance(item, dict) or 'name' not in item:
                        logger.error(f"Error: Invalid item format: {item}")
                        raise ValueError(f"Invalid item format")
                    original_value = item.get('value', 0)
                    item['value'] = convert_to_numeric(original_value)
                    logger.info(f"Converted value for {item['name']}: {original_value} -> {item['value']}")
            
            # Process balance_sheet items
            for subsection in ['assets', 'liabilities']:
                for subcategory in ['current', 'non_current']:
                    process_items(data['balance_sheet'][subsection][subcategory])
            process_items(data['balance_sheet']['equity'])
            
            # Process income_statement items
            for subsection in ['revenue', 'expenses']:
                for subcategory in ['operating', 'non_operating']:
                    process_items(data['income_statement'][subsection][subcategory])
            
            # Convert back to JSON string
            result = json.dumps(data)
            logger.info(f"Final processed data: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {str(e)}\nProblematic text: {cleaned_text}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in parse_financial_data: {str(e)}")
        raise Exception(f"Error processing financial data: {str(e)}")

@app.route('/api/process-pdf', methods=['POST'])
def process_pdf():
    logger.info("\n=== Starting PDF Upload Process ===\nRequest Details:")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Content Type: {request.content_type}")
    logger.info(f"Content Length: {request.content_length}")
    logger.info(f"Files: {request.files}")
    logger.info(f"Form Data: {request.form}")
    
    # Validate file presence
    if 'file' not in request.files:
        error_msg = 'No file provided in request'
        logger.error(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 400
        
    file = request.files['file']
    logger.info(f"File received: {file.filename}")
    logger.info(f"File content type: {file.content_type}")
    
    # Validate filename
    if file.filename == '':
        error_msg = 'No file selected'
        logger.error(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Validate file format
    if not file.filename.lower().endswith('.pdf'):
        error_msg = 'File must be a PDF'
        logger.error(f"Error: {error_msg} (received: {file.filename})")
        return jsonify({'error': error_msg}), 400
    
    # Validate file content type
    if file.content_type != 'application/pdf':
        error_msg = 'Invalid file type. Please upload a PDF file.'
        logger.error(f"Error: {error_msg} (received: {file.content_type})")
        return jsonify({'error': error_msg}), 400
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    if request.content_length > max_size:
        error_msg = 'File size exceeds maximum limit of 10MB'
        logger.error(f"Error: {error_msg} (size: {request.content_length} bytes)")
        return jsonify({'error': error_msg}), 400
    
    logger.info("=== File validation passed successfully ===")
    
    try:
        # Check if Gemini AI model is properly initialized
        if not model:
            error_msg = 'AI service is not available. Please check your API key configuration.'
            logger.error(f"Error: {error_msg}")
            return jsonify({'error': error_msg}), 503

        # Extract text from PDF
        try:
            logger.info("Starting text extraction from PDF...")
            text = extract_text_from_pdf(file)
            if not text.strip():
                error_msg = 'No readable text found in the PDF. Please ensure the PDF contains text and not just images.'
                logger.error(f"Error: {error_msg}")
                return jsonify({'error': error_msg}), 400
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
        except Exception as e:
            error_msg = f'Error reading PDF file: {str(e)}. Please ensure the file is not corrupted and is a valid PDF.'
            logger.error(f"Error during PDF extraction: {str(e)}")
            return jsonify({'error': error_msg}), 400
        
        # Parse financial data using Gemini AI
        try:
            logger.info("Starting financial data parsing with Gemini AI...")
            financial_data_str = parse_financial_data(text)
            financial_data = json.loads(financial_data_str)
            
            # Additional validation of the extracted data
            if not any(section for section in financial_data['balance_sheet'].values()) and \
               not any(section for section in financial_data['income_statement'].values()):
                error_msg = 'No financial data could be extracted from the PDF. Please ensure the document contains financial statements.'
                logger.error(f"Error: {error_msg}")
                return jsonify({'error': error_msg}), 400
                
            logger.info("Successfully processed and validated financial data")
            return jsonify({'data': financial_data})
        except json.JSONDecodeError as e:
            error_msg = f'Invalid data format received: {str(e)}'
            logger.error(f"JSON decode error: {str(e)}")
            return jsonify({'error': error_msg}), 500
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error: {str(e)}")
            return jsonify({'error': error_msg}), 400
        except Exception as e:
            error_msg = f'Error processing financial data: {str(e)}'
            logger.error(f"Error during financial data processing: {str(e)}")
            return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        logger.error(f"Unexpected error during processing: {str(e)}")
        return jsonify({'error': error_msg}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'financial_data' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        message = data['message']
        financial_data = data['financial_data']

        # Company information for context
        company_info = """
        Shubh Sawariya Industries Private Limited is a manufacturing company based in Jamshedpur, Jharkhand, India.
        Established in 2019 (Jamshedpur location), the company manufactures and supplies food carts, food vans, push carts, and kiosks.
        The company is directed by Mr. Nishant Agarwal with an employee count between 50-100.
        Annual turnover: Below Rs. 0.5 Crore.
        The company holds ISO 9001:2015 certification for quality management.
        """

        # Prepare prompt for financial analysis with company context and markdown formatting
        prompt = f"""Analyze the following financial data for Shubh Sawariya Industries and answer this question: {message}

        Company Context:
        {company_info}

        Financial Data:
        {json.dumps(financial_data, indent=2)}

        If the question is about WACC (Weighted Average Cost of Capital), calculate it using this formula:
        WACC = (E/V) * Re + (D/V) * Rd * (1-Tc)
        Where:
        - E = Market value of equity
        - D = Market value of debt
        - V = Total value of the firm (E + D)
        - Re = Cost of equity (use CAPM if possible, otherwise assume 10-15%)
        - Rd = Cost of debt (use average interest rate if available, otherwise assume 8-10%)
        - Tc = Corporate tax rate (assume 30% if not specified)

        For debt-to-equity ratio, calculate Total Debt / Total Equity.

        Please provide a clear, concise answer focusing on the specific financial metrics requested.
        Format your response using markdown for better readability:
        - Use **bold** for important numbers and metrics
        - Use headings (## and ###) for sections
        - Use bullet points where appropriate
        - Include formula calculations when relevant

        If the question cannot be answered with the available data, explain what additional information would be needed."""

        try:
            response = model.generate_content(prompt)
            return jsonify({'response': response.text})
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return jsonify({'error': 'Failed to generate response'}), 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')

@app.route('/')
def index():
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({'error': 'Failed to load index page'}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        return app.send_static_file(path)
    except Exception as e:
        logger.error(f"Error serving file {path}: {str(e)}")
        return jsonify({'error': f'File not found: {path}'}), 404

@app.errorhandler(404)
def not_found_error(error):
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory('public', 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('public', 'script.js')

@app.route('/shubh_logo.png')
def serve_logo():
    return send_from_directory('public', 'shubh_logo.png')

if __name__ == '__main__':
    logger.info("\n* Server is ready to process PDF uploads and chat! You can now upload your financial documents and ask questions.")
    app.run(debug=True, port=5000)