import { useState, useEffect } from 'react';
import { apiClient, ProgressResponse } from '../lib/api';

export const useProgress = () => {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProgress();
  }, []);

  const fetchProgress = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getProgress();
      setProgress(data);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to fetch progress';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return { progress, loading, error, refetch: fetchProgress };
};
