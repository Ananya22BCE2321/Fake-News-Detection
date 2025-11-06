// src/types.ts

// Define the shape of the data sent to the backend
export interface PredictionRequest {
  title: string;
  text: string;
}

// Define the shape of the data received from the backend's prediction endpoints
export interface AnalysisResult {
  prediction: 'Reliable' | 'Unreliable';
  probability: number; // The confidence score (0.0 to 1.0) for the 'Unreliable' class
}

// Define the overall state of the application
export interface AppState {
  // result now holds the full analysis object, or null
  result: AnalysisResult | null; 
  isLoading: boolean;
  error: string | null;
}