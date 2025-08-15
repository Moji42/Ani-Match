import { useState, useCallback } from 'react';
import { SearchParams } from '@/components/SearchForm';

interface AnimeRecommendation {
  Anime: string;
  Genres: string[];
  'Predicted Rating'?: number;
  'Similarity Score'?: number;
  'Combined_Score'?: string;
  Rating?: number;
  Members?: number;
  Type?: string;
  Method?: string;
}

interface ApiResponse {
  results: AnimeRecommendation[] | {
    content_based?: AnimeRecommendation[];
    collaborative?: AnimeRecommendation[];
    hybrid?: AnimeRecommendation[];
  };
  error?: string;
}

const API_BASE_URL = 'http://localhost:5000';

export const useAnimeRecommendations = () => {
  const [results, setResults] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const searchRecommendations = useCallback(async (params: SearchParams) => {
    setIsLoading(true);
    setError(null);

    try {
      const { type, title, userId, count } = params;
      const url = new URL(`${API_BASE_URL}/recommend/${type}`);
      
      if (count) url.searchParams.append('n', count);
      if (title) url.searchParams.append('title', title);
      if (userId) url.searchParams.append('user_id', userId);

      const response = await fetch(url.toString(), {
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      setResults(Array.isArray(data) ? { results: data } : { results: data });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('Recommendation error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, error, isLoading, searchRecommendations, clearResults };
};