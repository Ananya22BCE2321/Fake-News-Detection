// src/App.tsx

import React, { useState, useCallback } from 'react';
import { FaSearch } from 'react-icons/fa';
import ResultDisplay from './components/ResultDisplay';
import LiquidEtherBackground from './components/LiquidEther';
import type { AppState, PredictionRequest, PredictionResult } from './types';
import './App.css'; // Import the styling file

const API_ENDPOINT = 'http://localhost:5000/predict'; // Adjust to your backend URL

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

    const requestBody: PredictionRequest = { title, text };

    try {
      // NOTE: This is a placeholder for your actual API call.
      // You may need to handle CORS setup on your backend.
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Assuming the API returns a JSON object like { prediction: 0 or 1 }
      const data: { prediction: PredictionResult } = await response.json();
      
      setAppState({
        result: data.prediction,
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('Prediction failed:', error);
      setAppState({
        result: null,
        isLoading: false,
        error: 'Failed to connect to the prediction service. Please try again.',
      });
    }
  }, [title, text]); // Dependencies for useCallback

  return (
    <div className="app-container">
      {/* 1. Dynamic Background (Placed behind all content) */}
      <LiquidEtherBackground />
      
      {/* 2. Semi-transparent Overlay to ensure readability */}
      <div className="overlay"></div>

      {/* 3. Main Content Card (Centered) */}
      <div className="main-card">
        <header className="header">
          <h1>FactCheck AI</h1>
          <p>Leveraging LSTM and ANN for Credibility Analysis</p>
        </header>

        {appState.error && <p className="error-message">{appState.error}</p>}

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