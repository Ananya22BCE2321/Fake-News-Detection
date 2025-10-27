import os
import re
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# --- 1. SETUP ---
app = Flask(__name__)
# Crucial: Allows the React frontend (running on a different port) to access this server
CORS(app) 

# --- 2. CONFIGURATION (CHECK THESE VALUES FROM YOUR NOTEBOOK) ---
MAX_LEN = 200  # Check the max sequence length used during training
STOP_WORDS = set(stopwords.words('english'))

# --- 3. LOAD MODEL AND TOKENIZER ---
try:
    # Ensure these paths are correct relative to where you run app.py
    MODEL_PATH = 'lstm_model.h5'
    TOKENIZER_PATH = 'tokenizer.pkl'
    
    model = load_model(MODEL_PATH)
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)
    print(f"Model loaded from {MODEL_PATH}")
    print(f"Tokenizer loaded from {TOKENIZER_PATH}")
except Exception as e:
    print(f"Error loading model or tokenizer: {e}")
    model = None
    tokenizer = None


# --- 4. PREPROCESSING FUNCTION (Matches Notebook Logic) ---
def clean_text(text):
    """Applies the same cleaning steps as performed in the notebook."""
    if not isinstance(text, str):
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

# --- 5. PREDICTION ENDPOINT ---
@app.route('/predict', methods=['POST'])
def predict():
    if model is None or tokenizer is None:
        return jsonify({"error": "Prediction service is unavailable (Model/Tokenizer not loaded)."}), 503

    try:
        data = request.get_json()
        raw_text = data.get('text', '')
        
        if not raw_text:
            return jsonify({"error": "No 'text' provided for analysis."}), 400

        # Preprocess the text
        cleaned = clean_text(raw_text)
        
        # Tokenize and pad the sequence
        sequence = tokenizer.texts_to_sequences([cleaned])
        padded_sequence = np.array(sequence)
        
        # NOTE: Keras padding function might be needed if simple np.array doesn't handle padding correctly
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        padded_sequence = pad_sequences(padded_sequence, maxlen=MAX_LEN, padding='post', truncating='post')
        
        # Run prediction
        prediction = model.predict(padded_sequence)
        
        # The model outputs a probability (e.g., [0.99] or [0.01])
        # Convert the prediction probability to a binary label (0 or 1)
        # 1: Unreliable (Fake), 0: Reliable (Real)
        predicted_label = 1 if prediction[0][0] > 0.5 else 0
        
        print(f"Input: {raw_text[:50]}...")
        print(f"Cleaned: {cleaned[:50]}...")
        print(f"Prediction: {prediction[0][0]}, Label: {predicted_label}")
        
        return jsonify({
            "prediction": predicted_label,
            "probability": float(prediction[0][0])
        })
        
    except Exception as e:
        print(f"Prediction execution failed: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500

# --- 6. RUN SERVER ---
if __name__ == '__main__':
    # Running on port 5000, as configured in App.tsx
    app.run(port=5000, debug=True)