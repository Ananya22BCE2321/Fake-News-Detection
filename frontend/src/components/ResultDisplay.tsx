// src/components/ResultDisplay.tsx

import React from 'react';
import { FaCheckCircle, FaTimesCircle, FaSpinner } from 'react-icons/fa';
// Importing the new type structure
import type { AnalysisResult } from '../types'; 

interface ResultDisplayProps {
  result: AnalysisResult | null; // Now accepts the full analysis object
  isLoading: boolean;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="result-container loading">
        <div className="icon spinner">
          <FaSpinner size={48} />
        </div>
        <h2 className="status-text">Analyzing Credibility...</h2>
      </div>
    );
  }

  if (result === null) {
    return null;
  }

  // --- Logic for Confidence Score ---
  const isReliable = result.prediction === 'Reliable';
  
  // The backend's probability is the score for 'Unreliable' (Class 1).
  // We calculate the final confidence in the predicted label.
  const rawConfidence = isReliable 
    ? (1 - result.probability) 
    : result.probability; 
  
  const confidencePercent = (rawConfidence * 100).toFixed(2);
  
  const label = result.prediction;
  
  // --- Styling and Content ---
  const containerClass = isReliable ? 'reliable' : 'unreliable';
  const icon = isReliable ? <FaCheckCircle size={64} /> : <FaTimesCircle size={64} />;
  const statusClass = isReliable ? 'green' : 'red';
  
  return (
    <div className={`result-container ${containerClass}`}>
      <div className={`icon ${isReliable ? 'check-icon' : 'times-icon'}`}>
        {icon}
      </div>
      <h1 className={`status-text ${statusClass}`}>Status: {label}</h1>
      <p className="summary-text">
        The model classifies this article as **{label.toLowerCase()}**.
      </p>
      {/* IMPROVED CONFIDENCE SCORE DISPLAY */}
      <div className="confidence-score-box">
        <strong className="confidence-percent-text">{confidencePercent}%</strong>
        <p className="confidence-detail">
          Confidence Score for the **{label}** classification.
        </p>
      </div>
    </div>
  );
};

export default ResultDisplay;