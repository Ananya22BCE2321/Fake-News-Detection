import os
import re
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS # FIX: Added the necessary import
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.corpus import stopwords
from werkzeug.utils import secure_filename
import string

# --- 1. SETUP ---
app = Flask(__name__)
CORS(app) 
UPLOAD_FOLDER = '/tmp/uploads' # Temporary folder for file uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- 2. CONFIGURATION (Matches Notebook Logic) ---
MAX_LEN = 200  # Check the max sequence length used during training
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
    print(f"Model loaded from {MODEL_PATH}")
    print(f"Tokenizer loaded from {TOKENIZER_PATH}")
except Exception as e:
    # This error was fixed by moving the files to the backend folder
    print(f"Error loading model or tokenizer: {e}") 


# --- 4. PREPROCESSING & HELPER FUNCTIONS ---

def clean_text(text: str) -> str:
    """Applies the same cleaning steps as performed in the notebook."""
    if not isinstance(text, str):
        return ""
        
    # 1. Lowercase
    text = text.lower()
    
    # 2. Remove punctuation and special characters (using regex from notebook)
    text = re.sub(r'[^A-Za-z0-9\s]', '', text)
    
    # 3. Remove newlines and extra spaces
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 4. Remove stopwords
    words = text.split()
    text = " ".join([word for word in words if word not in STOP_WORDS])
    
    # NOTE: If your final model training in the notebook included NLTK Stemming 
    # (as suggested by a snippet from a detector.py file), you must uncomment 
    # and import the stemmer here to ensure consistent preprocessing.
    
    return text

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- PLACEHOLDER FUNCTIONS FOR EXTERNAL DATA SOURCES ---
# REMINDER: You must replace these placeholders with real implementations 
# using requests/BeautifulSoup for URLs and PyPDF2/pdfminer.six for PDFs.

def get_text_from_url(url: str) -> str:
    """
    *** Placeholder Function ***
    Simulates fetching and scraping text from a URL.
    """
    if "fake-example.com" in url:
        return "BREAKING: Scientists have discovered that eating broccoli makes you instantly rich. This is definitely not fake news."
    elif "real-example.com" in url:
        return "Experts from the World Health Organization published a report on current pandemic trends, noting the importance of vaccination."
    else:
        # Simulate a scrape
        print(f"Simulating scrape for URL: {url}")
        return "The recent developments in the global market show a 1.5% rise in tech stocks, driven by quarterly earnings reports from major corporations."

def get_text_from_pdf(filepath: str) -> str:
    """
    *** Placeholder Function ***
    Simulates extracting text from an uploaded PDF file.
    """
    # Simulate PDF text extraction
    if os.path.basename(filepath) == "unreliable.pdf":
        return "PDF Source: Shocking new documents reveal that all world leaders are secretly aliens working for a shadow government."
    else:
        return "PDF Source: A detailed analysis of the quarterly financial reports, as mandated by the regulatory body, shows compliance with all required benchmarks and disclosures."

# --- 5. PREDICTION ENDPOINTS ---

@app.route('/predict', methods=['POST'])
def predict_text():
    """Endpoint for direct text input analysis (from the existing App.tsx)."""
    if model is None or tokenizer is None:
        return jsonify({"error": "Model or tokenizer not loaded."}), 500
        
    data = request.get_json()
    # The frontend is sending 'text' in the request body (title is optional)
    raw_text = data.get('text', '')
    
    if not raw_text.strip():
        return jsonify({"error": "No text provided for analysis."}), 400

    try:
        # 1. Apply Preprocessing
        cleaned = clean_text(raw_text)

        # 2. Convert text to sequence and pad
        sequence = tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(sequence, maxlen=MAX_LEN)

        # 3. Make the prediction
        prediction = model.predict(padded)
        
        # ASSUMPTION: 1=Unreliable, 0=Reliable 
        predicted_label = "Unreliable" if prediction[0][0] >= 0.5 else "Reliable"
        
        print(f"Text Analysis - Cleaned: {cleaned[:50]}...")
        print(f"Prediction: {prediction[0][0]}, Label: {predicted_label}")

        return jsonify({ 
            "prediction": predicted_label, 
            "probability": float(prediction[0][0])
        })
    except Exception as e:
        print(f"Prediction execution failed: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500

@app.route('/analyze_remote', methods=['POST'])
def predict_remote():
    """Unified endpoint for URL and PDF analysis."""
    if model is None or tokenizer is None:
        return jsonify({"error": "Model or tokenizer not loaded."}), 500
        
    raw_text = None
    source_type = None

    if 'url' in request.form:
        source_type = 'URL'
        url = request.form.get('url')
        if not url:
            return jsonify({"error": "No URL provided."}), 400
        try:
            raw_text = get_text_from_url(url)
        except Exception as e:
            return jsonify({"error": f"Failed to fetch content from URL: {e}"}), 500

    elif 'file' in request.files:
        source_type = 'PDF'
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected."}), 400
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                raw_text = get_text_from_pdf(filepath)
                os.remove(filepath) # Clean up the temporary file
            except Exception as e:
                return jsonify({"error": f"Failed to process PDF file: {e}"}), 500
        else:
            return jsonify({"error": "Invalid file type. Only PDF is supported."}), 400

    if not raw_text:
        return jsonify({"error": "Could not extract or retrieve text for analysis."}), 400

    # Perform the prediction on the extracted raw_text
    try:
        cleaned = clean_text(raw_text)
        sequence = tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(sequence, maxlen=MAX_LEN)
        prediction = model.predict(padded)
        
        predicted_label = "Unreliable" if prediction[0][0] >= 0.5 else "Reliable"
        
        print(f"{source_type} Analysis - Cleaned: {cleaned[:50]}...")
        print(f"Prediction: {prediction[0][0]}, Label: {predicted_label}")

        return jsonify({ 
            "prediction": predicted_label, 
            "probability": float(prediction[0][0])
        })
    except Exception as e:
        print(f"Prediction execution failed: {e}")
        return jsonify({"error": f"Internal prediction error: {e}"}), 500

# --- 6. RUN SERVER ---
if __name__ == '__main__':
    # Running on port 5000, as configured in App.tsx
    app.run(port=5000, debug=True)