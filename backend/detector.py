import joblib
import os
import re
import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# --- Configuration and Setup ---

# Set up the file paths relative to the script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILENAME = 'fake_news_model.pkl'         # Ensure your model is saved as this file name
VECTORIZER_FILENAME = 'tfidf_vectorizer.pkl'   # Ensure your TfidfVectorizer is saved as this file name
MODEL_PATH = os.path.join(BASE_DIR, MODEL_FILENAME)
VECTORIZER_PATH = os.path.join(BASE_DIR, VECTORIZER_FILENAME)

# Initialize NLP tools
STOP_WORDS = set(stopwords.words('english'))
STEMMER = PorterStemmer()

# Global variables to hold the loaded model and vectorizer
LOADED_MODEL = None
LOADED_VECTORIZER = None

# --- Core Preprocessing Function (MUST MATCH NOTEBOOK TRAINING) ---

def preprocess_text(text: str) -> str:
    """
    Applies the same preprocessing steps used during model training in the IPYNB.
    
    The steps are typically:
    1. Lowercasing
    2. Removing punctuation
    3. Removing non-alphanumeric characters (optional)
    4. Removing stop words
    5. Stemming/Lemmatization
    """
    if not isinstance(text, str):
        text = str(text) # Handle non-string inputs (e.g., NaN from a dataset)

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # 3. Remove non-word characters and extra spaces
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip() # Replace multiple spaces with one

    # 4. Tokenization (splitting into words)
    words = text.split()

    # 5. Stop word removal and Stemming
    processed_words = [
        STEMMER.stem(word) 
        for word in words 
        if word not in STOP_WORDS and len(word) > 1
    ]

    return " ".join(processed_words)

# --- Model Loading Function ---

def load_pipeline_components():
    """
    Loads the trained machine learning model and the TfidfVectorizer.
    This function is called once when the server starts.
    """
    global LOADED_MODEL, LOADED_VECTORIZER
    
    print(f"Attempting to load model from: {MODEL_PATH}")
    print(f"Attempting to load vectorizer from: {VECTORIZER_PATH}")

    try:
        LOADED_MODEL = joblib.load(MODEL_PATH)
        LOADED_VECTORIZER = joblib.load(VECTORIZER_PATH)
        print("Model and Vectorizer loaded successfully.")
        
    except FileNotFoundError:
        error_msg = ("\n\nFATAL ERROR: Model or Vectorizer file not found! "
                     f"Expected files: {MODEL_FILENAME} and {VECTORIZER_FILENAME}. "
                     "Please ensure you have saved them from your notebook and placed them in the same directory as detector.py."
                     "\n\nRun the model saving code in your IPYNB (e.g., joblib.dump(model, 'fake_news_model.pkl'))"
                     )
        print(error_msg)
        LOADED_MODEL = None # Set to None to indicate failure
        
    except Exception as e:
        print(f"An error occurred during model loading: {e}")
        LOADED_MODEL = None

# --- Main Prediction Function ---

def analyze_text(text: str) -> str:
    """
    The main function to classify a piece of text.
    
    Args:
        text: The raw news text/headline to analyze.
        
    Returns:
        "Reliable" or "Unreliable" or an error message.
    """
    if LOADED_MODEL is None:
        return "ERROR: Model not loaded. Check server logs."
        
    if not text or len(text.strip()) < 10:
        return "Unreliable (Input too short or empty for analysis)"

    try:
        # 1. Apply Preprocessing
        processed_text = preprocess_text(text)
        
        # 2. Vectorize the processed text (uses the *loaded* TfidfVectorizer)
        text_vectorized = LOADED_VECTORIZER.transform([processed_text])

        # 3. Make the prediction
        # The output prediction[0] is typically 0 or 1
        prediction = LOADED_MODEL.predict(text_vectorized)[0]
        
        # 4. Map the numerical prediction to the desired string output
        # ASSUMPTION: Based on common Fake News datasets (Kaggle/others), 
        # Label 1 is often FAKE/UNRELIABLE and Label 0 is REAL/RELIABLE.
        # *Adjust this mapping to match YOUR specific IPYNB's label encoding.*
        
        if prediction == 0:
            return "Reliable"
        elif prediction == 1:
            return "Unreliable"
        else:
            # Fallback for unexpected model output
            return f"Uncertain (Model output: {prediction})"

    except Exception as e:
        print(f"Error during prediction: {e}")
        return f"ERROR: An internal error occurred during text classification: {e}"

# --- Initial Load and Test ---

# Load the model and vectorizer immediately when the script is imported/run
load_pipeline_components()

if __name__ == '__main__':
    # Simple console test
    print("\n--- Running Console Test ---")
    
    # Example 1: Likely a real news headline
    test_real = "U.S. stocks rally as inflation concerns ease and technology sector posts strong gains."
    print(f"Text: '{test_real}'")
    print(f"Classification: {analyze_text(test_real)}\n")
    
    # Example 2: Likely a sensational/fake news headline
    test_fake = "ALIENS DISCOVERED on Mars, Government is HIDING the truth! Secret message decoded in crop circles."
    print(f"Text: '{test_fake}'")
    print(f"Classification: {analyze_text(test_fake)}")