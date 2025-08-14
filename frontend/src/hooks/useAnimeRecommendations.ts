import { useState, useCallback } from 'react';
import { SearchParams } from '@/components/SearchForm';

interface UseAnimeRecommendationsReturn {
  results: any;
  error: string | null;
  isLoading: boolean;
  searchRecommendations: (params: SearchParams) => Promise<void>;
  clearResults: () => void;
}

const API_BASE_URL = 'http://localhost:5000'; // Update this to match your Flask backend URL

export const useAnimeRecommendations = (): UseAnimeRecommendationsReturn => {
  const [results, setResults] = useState(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const buildUrl = useCallback((params: SearchParams): string => {
    const { type, title, userId, count } = params;
    const baseUrl = `${API_BASE_URL}/recommend/${type}`;
    const urlParams = new URLSearchParams();

    if (count) urlParams.append('n', count);

    switch (type) {
      case 'content':
        if (title) urlParams.append('title', title);
        break;
      case 'collaborative':
        if (userId) urlParams.append('user_id', userId);
        break;
      case 'hybrid':
        if (title) urlParams.append('title', title);
        if (userId) urlParams.append('user_id', userId);
        break;
      case 'random':
        // No additional parameters needed for random
        break;
    }

    return `${baseUrl}?${urlParams.toString()}`;
  }, []);

  const searchRecommendations = useCallback(async (params: SearchParams) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const url = buildUrl(params);
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      console.error('Recommendation fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [buildUrl]);

  const clearResults = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    results,
    error,
    isLoading,
    searchRecommendations,
    clearResults,
  };
};