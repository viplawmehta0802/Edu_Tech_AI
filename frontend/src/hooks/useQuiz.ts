import { useState } from 'react';
import { apiClient, QuizRequest, QuizResponse } from '../lib/api';

export const useQuiz = () => {
  const [quiz, setQuiz] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateQuiz = async (topic: string, grade: number, numQuestions: number) => {
    setLoading(true);
    setError(null);
    setQuiz(null);

    try {
      const req: QuizRequest = { topic, grade, num_questions: numQuestions };
      const res: QuizResponse = await apiClient.generateQuiz(req);
      setQuiz(res.quiz);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Quiz generation failed';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setQuiz(null);
    setError(null);
  };

  return { quiz, loading, error, generateQuiz, reset };
};
