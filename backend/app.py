import os
import re
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.corpus import stopwords
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO

# --- 1. SETUP ---
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# --- 2. CONFIGURATION ---
MAX_LEN = 200
STOP_WORDS = set(stopwords.words('english'))
ALLOWED_EXTENSIONS = {'pdf'}

# --- 3. LOAD MODEL AND TOKENIZER ---
MODEL_PATH = 'lstm_model.h5'
TOKENIZER_PATH = 'tokenizer.pkl'
model = None
tokenizer = None

try:
    model = load_model(MODEL_PATH)
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)
    print(f"✓ Model loaded from {MODEL_PATH}")
    print(f"✓ Tokenizer loaded from {TOKENIZER_PATH}")
except Exception as e:
    print(f"✗ Error loading model or tokenizer: {e}")
    print("Please ensure lstm_model.h5 and tokenizer.pkl are in the backend directory")

# --- 4. PREPROCESSING FUNCTIONS ---

def clean_text(text: str) -> str:
    """Applies the same cleaning steps as performed in the notebook."""
    if not isinstance(text, str) or not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove special characters/punctuation
    text = re.sub(r'[^A-Za-z0-9\s]', '', text)
    
    # Remove newlines and extra spaces
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove stopwords
    words = text.split()
    text = " ".join([word for word in words if word not in STOP_WORDS])
    
    return text

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 5. CONTENT EXTRACTION FUNCTIONS ---
def get_text_from_url(url: str) -> str:
    """Extract text content from a URL using web scraping."""
    try:
        # --- THIS IS THE FIX ---
        # We are using more headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        # --- END OF FIX ---
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Fetch the webpage with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script.decompose()
        
        # Get text from article, main content, or body
        content = None
        
        # Try to find article content
        for selector in ['article', 'main', '.article-content', '.post-content', '[role="main"]']:
            content = soup.select_one(selector)
            if content:
                break
        
        # Fallback to body if no specific content found
        if not content:
            content = soup.find('body')
        
        if not content:
            raise ValueError("Could not extract text content from the page")
        
        # Extract and clean text
        text = content.get_text(separator=' ', strip=True)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:
            raise ValueError("Extracted text is too short (less than 100 characters)")
        
        return text
        
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. The website took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise Exception("Failed to connect to the URL. Please check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error occurred: {e}")
    except Exception as e:
        raise Exception(f"Failed to extract text from URL: {str(e)}")
def get_text_from_pdf(file_storage) -> str:
    """Extract text from an uploaded PDF file."""
    try:
        # Read PDF from file storage
        pdf_reader = PyPDF2.PdfReader(file_storage)
        
        if len(pdf_reader.pages) == 0:
            raise ValueError("PDF file is empty")
        
        # Extract text from all pages
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + " "
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:
            raise ValueError("Extracted text is too short (less than 100 characters)")
        
        return text
        
    except PyPDF2.errors.PdfReadError:
        raise Exception("Invalid or corrupted PDF file")
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

# --- 6. PREDICTION LOGIC ---

def make_prediction(raw_text: str):
    """Common prediction logic used by all endpoints."""
    if not raw_text or len(raw_text.strip()) < 10:
        raise ValueError("Text is too short for analysis (minimum 10 characters)")
    
    # Apply preprocessing
    cleaned = clean_text(raw_text)
    
    if not cleaned:
        raise ValueError("After preprocessing, no valid text remains")
    
    # Convert text to sequence and pad
    sequence = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(sequence, maxlen=MAX_LEN, padding='post', truncating='post')
    
    # Make prediction
    prediction = model.predict(padded, verbose=0)
    probability = float(prediction[0][0])
    
    # ASSUMPTION: probability > 0.5 = Unreliable, <= 0.5 = Reliable
    predicted_label = "Unreliable" if probability > 0.5 else "Reliable"
    
    return predicted_label, probability

# --- 7. API ENDPOINTS ---

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None
    })

@app.route('/predict', methods=['POST'])
def predict_text():
    """Endpoint for direct text input analysis."""
    if model is None or tokenizer is None:
        return jsonify({"error": "Model or tokenizer not loaded. Please check server logs."}), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        title = data.get('title', '')
        text = data.get('text', '')
        
        # Combine title and text
        raw_text = f"{title}\n\n{text}" if title else text
        
        if not raw_text.strip():
            return jsonify({"error": "No text provided for analysis"}), 400
        
        # Make prediction
        predicted_label, probability = make_prediction(raw_text)
        
        print(f"✓ Text Analysis - Label: {predicted_label}, Probability: {probability:.4f}")
        
        return jsonify({
            "prediction": predicted_label,
            "probability": probability
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/analyze_remote', methods=['POST'])
def analyze_remote():
    """Unified endpoint for URL and PDF analysis."""
    if model is None or tokenizer is None:
        return jsonify({"error": "Model or tokenizer not loaded. Please check server logs."}), 503
    
    try:
        raw_text = None
        source_type = None
        
        # Check if URL is provided
        if 'url' in request.form:
            source_type = 'URL'
            url = request.form.get('url', '').strip()
            
            if not url:
                return jsonify({"error": "URL cannot be empty"}), 400
            
            print(f"→ Processing URL: {url}")
            raw_text = get_text_from_url(url)
            print(f"✓ Extracted {len(raw_text)} characters from URL")
        
        # Check if PDF file is provided
        elif 'file' in request.files:
            source_type = 'PDF'
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if not allowed_file(file.filename):
                return jsonify({"error": "Invalid file type. Only PDF files are supported"}), 400
            
            print(f"→ Processing PDF: {file.filename}")
            raw_text = get_text_from_pdf(file)
            print(f"✓ Extracted {len(raw_text)} characters from PDF")
        
        else:
            return jsonify({"error": "No URL or file provided"}), 400
        
        # Make prediction
        predicted_label, probability = make_prediction(raw_text)
        
        print(f"✓ {source_type} Analysis - Label: {predicted_label}, Probability: {probability:.4f}")
        
        return jsonify({
            "prediction": predicted_label,
            "probability": probability,
            "source_type": source_type
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        return jsonify({"error": str(e)}), 500

# --- 8. ERROR HANDLERS ---

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error occurred"}), 500

# --- 9. RUN SERVER ---
if __name__ == '__main__':
    print("\n" + "="*50)
    print("FactCheck AI Backend Server")
    print("="*50)
    print(f"Model Status: {'✓ Loaded' if model else '✗ Not Loaded'}")
    print(f"Tokenizer Status: {'✓ Loaded' if tokenizer else '✗ Not Loaded'}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)