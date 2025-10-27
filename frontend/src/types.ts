// src/types.ts

// Define the shape of the data sent to the backend
export interface PredictionRequest {
  title: string;
  text: string;
}

// Define the shape of the data received from the backend
// Assuming the backend returns 0 for Reliable and 1 for Unreliable
export type PredictionResult = 0 | 1 | null; // null for initial state

// Define the overall state of the application
export interface AppState {
  result: PredictionResult;
  isLoading: boolean;
  error: string | null;
}