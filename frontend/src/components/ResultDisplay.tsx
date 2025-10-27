// src/components/ResultDisplay.tsx

import React from 'react';
import { FaCheckCircle, FaTimesCircle, FaSpinner } from 'react-icons/fa';
import type { PredictionResult } from '../types';

interface ResultDisplayProps {
  result: PredictionResult;
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

  if (result === 0) {
    return (
      <div className="result-container reliable">
        <div className="icon check-icon">
          <FaCheckCircle size={64} />
        </div>
        <h1 className="status-text green">Status: Reliable</h1>
        <p>The model classifies this article as reliable.</p>
      </div>
    );
  }

  if (result === 1) {
    return (
      <div className="result-container unreliable">
        <div className="icon times-icon">
          <FaTimesCircle size={64} />
        </div>
        <h1 className="status-text red">Status: Unreliable</h1>
        <p>The model classifies this article as unreliable (fake news).</p>
      </div>
    );
  }

  return null;
};

export default ResultDisplay;