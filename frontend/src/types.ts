// src/types.ts

/**
 * The shape of the analysis result object returned from the backend
 * and expected by the ResultDisplay component.
 */
export interface AnalysisResult {
  prediction: 'Reliable' | 'Unreliable';
  probability: number;
}

/**
 * The main state for the App component.
 */
export interface AppState {
  result: AnalysisResult | null;
  isLoading: boolean;
  error: string | null;
}