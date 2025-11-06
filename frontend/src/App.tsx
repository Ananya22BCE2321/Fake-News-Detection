// src/App.tsx

import React, { useState, useCallback } from 'react';
import { FaSearch } from 'react-icons/fa';
import ResultDisplay from './components/ResultDisplay';
import LiquidEtherBackground from './components/LiquidEther';
import type { AppState, PredictionRequest, PredictionResult } from './types';
import './App.css';

const API_ENDPOINT = 'http://localhost:5000/predict';

const App: React.FC = () => {
  const [title, setTitle] = useState<string>('');
  const [text, setText] = useState<string>('');
  const [appState, setAppState] = useState<AppState>({
    result: null,
    isLoading: false,
    error: null,
  });

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!text.trim()) {
      alert('Please paste the full text of the news article.');
      return;
    }

    setAppState({ result: null, isLoading: true, error: null });

    // Combine title and text for the backend
    const fullText = title ? `${title}\n\n${text}` : text;
    const requestBody = { text: fullText };

    try {
      console.log('Sending request to:', API_ENDPOINT);
      console.log('Request body:', requestBody);

      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      
      // Handle the response format from app.py
      // It returns: { prediction: 0 or 1, probability: float }
      const prediction = data.prediction as PredictionResult;
      
      setAppState({
        result: prediction,
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('Prediction failed:', error);
      setAppState({
        result: null,
        isLoading: false,
        error: error instanceof Error 
          ? `Error: ${error.message}. Make sure the backend server is running on port 5000.`
          : 'Failed to connect to the prediction service. Please try again.',
      });
    }
  }, [title, text]);

  return (
    <div className="app-container">
      <LiquidEtherBackground />
      <div className="overlay"></div>

      <div className="main-card">
        <header className="header">
          <h1>FactCheck AI</h1>
          <p>Leveraging LSTM and ANN for Credibility Analysis</p>
        </header>

        {appState.error && (
          <div style={{
            padding: '1rem',
            marginBottom: '1rem',
            backgroundColor: 'rgba(244, 67, 54, 0.15)',
            border: '1px solid #f44336',
            borderRadius: '8px',
            color: '#f44336'
          }}>
            {appState.error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="prediction-form">
          <input
            type="text"
            placeholder="Optional: Article Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={appState.isLoading}
            className="input-field"
          />
          <textarea
            placeholder="Paste the full text of the news article here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={appState.isLoading}
            rows={10}
            required
            className="textarea-field"
          />
          <button
            type="submit"
            disabled={appState.isLoading || !text.trim()}
            className="submit-button"
          >
            <FaSearch />
            <span>{appState.isLoading ? 'Analyzing...' : 'Analyze Credibility'}</span>
          </button>
        </form>

        <ResultDisplay result={appState.result} isLoading={appState.isLoading} />
      </div>
    </div>
  );
};

export default App;