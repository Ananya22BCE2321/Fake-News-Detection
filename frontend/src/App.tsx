// src/App.tsx

import React, { useState, useCallback } from 'react';
import { FaSearch, FaFilePdf, FaLink, FaPaste } from 'react-icons/fa';
import ResultDisplay from './components/ResultDisplay';
import LiquidEtherBackground from './components/LiquidEther';
import type { AppState, AnalysisResult } from './types';
import './App.css'; // Make sure to update App.css (see step 4)

// Define API endpoints
const API_PREDICT_TEXT = 'http://localhost:5000/predict';
const API_ANALYZE_REMOTE = 'http://localhost:5000/analyze_remote';

type InputMode = 'text' | 'url' | 'file';

const App: React.FC = () => {
  // State for input mode and values
  const [mode, setMode] = useState<InputMode>('text');
  const [title, setTitle] = useState<string>('');
  const [text, setText] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);

  // State for app status
  const [appState, setAppState] = useState<AppState>({
    result: null,
    isLoading: false,
    error: null,
  });

  // Check if the form is submittable
  const canSubmit = () => {
    if (appState.isLoading) return false;
    if (mode === 'text') return text.trim().length > 0;
    if (mode === 'url') return url.trim().length > 0;
    if (mode === 'file') return file !== null;
    return false;
  };

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit()) {
      alert('Please provide the required input (text, URL, or PDF file).');
      return;
    }

    setAppState({ result: null, isLoading: true, error: null });

    let endpoint = '';
    let requestOptions: RequestInit = {};

    try {
      // --- Configure request based on input mode ---
      if (mode === 'text') {
        endpoint = API_PREDICT_TEXT;
        const fullText = title ? `${title}\n\n${text}` : text;
        
        requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: fullText }),
        };

      } else {
        // URL and File modes use the same endpoint with FormData
        endpoint = API_ANALYZE_REMOTE;
        const formData = new FormData();

        if (mode === 'url') {
          formData.append('url', url);
        } else if (mode === 'file' && file) {
          formData.append('file', file);
        }

        requestOptions = {
          method: 'POST',
          // DO NOT set 'Content-Type' for FormData,
          // the browser sets it automatically with the correct boundary
          body: formData,
        };
      }

      // --- Send API Request ---
      console.log('Sending request to:', endpoint);
      const response = await fetch(endpoint, requestOptions);
      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to parse error response' }));
        console.error('Error response:', errorData);
        throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
      }

      const data = (await response.json()) as AnalysisResult;
      console.log('Response data:', data);

      // --- THIS IS THE BUG FIX ---
      // 'data' is the object { prediction: "...", probability: ... }
      // We set it directly as the result.
      setAppState({
        result: data,
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('Prediction failed:', error);
      setAppState({
        result: null,
        isLoading: false,
        error: error instanceof Error 
          ? `Error: ${error.message}. Make sure the backend server is running.`
          : 'An unknown error occurred. Please try again.',
      });
    }
  }, [mode, title, text, url, file, appState.isLoading]); // Include all dependencies

  // Helper to render the correct input field
  const renderInput = () => {
    switch (mode) {
      case 'text':
        return (
          <>
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
          </>
        );
      case 'url':
        return (
          <input
            type="url"
            placeholder="Enter the full article URL (e.g., https://...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={appState.isLoading}
            className="input-field"
          />
        );
      case 'file':
        return (
          <div className="file-input-container">
            <input
              type="file"
              id="pdf-upload"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
              disabled={appState.isLoading}
              className="file-input-hidden"
            />
            <label htmlFor="pdf-upload" className="file-input-label">
              <FaFilePdf />
              <span>{file ? file.name : 'Click to select a PDF file'}</span>
            </label>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-container">
      <LiquidEtherBackground />
      <div className="overlay"></div>

      <div className="main-card">
        <header className="header">
          <h1>FactCheck AI</h1>
          <p>Analyze News from Text, URLs, and PDFs</p>
        </header>

        {appState.error && (
          <div className="error-box">
            {appState.error}
          </div>
        )}

        {/* --- Input Mode Tabs --- */}
        <div className="input-mode-selector">
          <button
            className={`mode-tab ${mode === 'text' ? 'active' : ''}`}
            onClick={() => setMode('text')}
            disabled={appState.isLoading}
          >
            <FaPaste /> Text
          </button>
          <button
            className={`mode-tab ${mode === 'url' ? 'active' : ''}`}
            onClick={() => setMode('url')}
            disabled={appState.isLoading}
          >
            <FaLink /> URL
          </button>
          <button
            className={`mode-tab ${mode === 'file' ? 'active' : ''}`}
            onClick={() => setMode('file')}
            disabled={appState.isLoading}
          >
            <FaFilePdf /> PDF
          </button>
        </div>

        <form onSubmit={handleSubmit} className="prediction-form">
          
          {renderInput()}

          <button
            type="submit"
            disabled={!canSubmit()}
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