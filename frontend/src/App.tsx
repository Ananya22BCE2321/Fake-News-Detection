// src/App.tsx

import React, { useState, useCallback } from 'react';
import { FaSearch, FaLink, FaFilePdf, FaPaste } from 'react-icons/fa';
import ResultDisplay from './components/ResultDisplay';
import LiquidEtherBackground from './components/LiquidEther';
import type { AppState, AnalysisResult } from './types'; // Import AnalysisResult
import './App.css'; 

const API_ENDPOINT = 'http://localhost:5000'; 

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'text' | 'url' | 'pdf'>('text');
  const [title, setTitle] = useState<string>('');
  const [text, setText] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);

  const [appState, setAppState] = useState<AppState>({
    result: null,
    isLoading: false,
    error: null,
  });

  const getActiveEndpoint = () => {
    if (activeTab === 'text') return `${API_ENDPOINT}/predict`;
    return `${API_ENDPOINT}/analyze_remote`; 
  };

  const createRequestBody = () => {
    const formData = new FormData();
    if (activeTab === 'text') {
      return { 
          method: 'POST', 
          body: JSON.stringify({ title, text }), 
          headers: { 'Content-Type': 'application/json' } 
      };
    } 
    
    if (activeTab === 'url') {
      formData.append('url', url);
      return { method: 'POST', body: formData };
    } 
    
    if (activeTab === 'pdf' && pdfFile) {
      formData.append('file', pdfFile);
      return { method: 'POST', body: formData };
    }
    
    return null;
  };

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    let validationError = '';
    if (activeTab === 'text' && !text.trim()) {
      validationError = 'Please paste the full text of the news article.';
    } else if (activeTab === 'url' && !url.trim()) {
      validationError = 'Please enter a URL.';
    } else if (activeTab === 'pdf' && !pdfFile) {
      validationError = 'Please upload a PDF file.';
    }

    if (validationError) {
      alert(validationError);
      return;
    }

    setAppState({ result: null, isLoading: true, error: null });

    const requestConfig = createRequestBody();
    if (!requestConfig) {
      setAppState({ result: null, isLoading: false, error: 'Invalid submission data.' });
      return;
    }
    
    try {
      const response = await fetch(getActiveEndpoint(), requestConfig);

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        const errorMessage = errorBody.error || `HTTP error! Status: ${response.status}`;
        throw new Error(errorMessage);
      }

      // data should match the AnalysisResult structure: { prediction: string, probability: number }
      const data: AnalysisResult = await response.json(); 
      
      setAppState({
        result: data, // Setting the entire result object
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      setAppState({
        result: null,
        isLoading: false,
        error: `Failed to connect or analyze: ${error.message}`,
      });
    }
  }, [activeTab, title, text, url, pdfFile]);

  const renderAnalysisForm = () => {
    switch (activeTab) {
      case 'text':
        return (
          <div className="tab-content">
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
          </div>
        );
      case 'url':
        return (
          <div className="tab-content">
            <input 
              type="url" 
              placeholder="Paste the Article URL here (e.g., https://example.com/article)" 
              value={url} 
              onChange={(e) => setUrl(e.target.value)} 
              disabled={appState.isLoading} 
              required 
              className="input-field" 
            />
            <p className="help-text">
                Note: In a real deployment, the backend must be able to scrape the URL content.
            </p>
          </div>
        );
      case 'pdf':
        return (
          <div className="tab-content">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={(e) => setPdfFile(e.target.files ? e.target.files[0] : null)} 
              disabled={appState.isLoading} 
              required 
              className="input-file" 
            />
            {pdfFile && <p className="file-info">Selected File: {pdfFile.name}</p>}
            <p className="help-text">
                Note: The backend needs a PDF parsing library (like `PyPDF2`) to extract text.
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  const getSubmitButtonText = () => {
    if (appState.isLoading) return 'Analyzing...';
    if (activeTab === 'text') return 'Analyze Text Credibility';
    if (activeTab === 'url') return 'Analyze URL Credibility';
    if (activeTab === 'pdf') return 'Analyze PDF Credibility';
    return 'Analyze';
  };

  return (
    <div className="app-container">
      {/* 1. Dynamic Background */}
      <LiquidEtherBackground />
      {/* 2. Semi-transparent Overlay */}
      <div className="overlay"></div>
      
      {/* 3. Main Content Card */}
      <div className="main-card">
        <header className="header">
          <h1>FactCheck AI</h1>
          <p>Leveraging LSTM and ANN for Credibility Analysis</p>
        </header>

        {appState.error && <p className="error-message">{appState.error}</p>}

        <form onSubmit={handleSubmit} className="prediction-form">
          {/* Tab Navigation */}
          <div className="tab-nav">
            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
              onClick={() => setActiveTab('text')}
              disabled={appState.isLoading}
            >
              <FaPaste /> Text Input
            </button>
            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
              onClick={() => setActiveTab('url')}
              disabled={appState.isLoading}
            >
              <FaLink /> URL Analysis
            </button>
            <button 
              type="button" 
              className={`tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
              onClick={() => setActiveTab('pdf')}
              disabled={appState.isLoading}
            >
              <FaFilePdf /> PDF Analysis
            </button>
          </div>

          {/* Analysis Form Content (Text/URL/PDF) */}
          {renderAnalysisForm()}
          
          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={appState.isLoading || (activeTab === 'text' && !text.trim()) || (activeTab === 'url' && !url.trim()) || (activeTab === 'pdf' && !pdfFile)} 
            className="submit-button"
          >
            <FaSearch /> <span>{getSubmitButtonText()}</span>
          </button>
        </form>

        <ResultDisplay 
          result={appState.result} 
          isLoading={appState.isLoading} // NOW CORRECTLY PASSING ISLOADING
        />
      </div>
    </div>
  );
};

export default App;