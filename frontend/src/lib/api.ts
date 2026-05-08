const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ChatRequest {
  student_id: string;
  message: string;
}

export interface ChatResponse {
  reply: string;
}

export interface QuizRequest {
  topic: string;
  grade: number;
  num_questions: number;
}

export interface QuizResponse {
  quiz: string;
}

export interface ProgressResponse {
  mastery_summary: Record<string, string>;
  weekly_trend: Array<{ day: string; xp: number }>;
}

export const apiClient = {
  async chat(req: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/tutor/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!response.ok) throw new Error('Chat request failed');
    return response.json();
  },

  async generateQuiz(req: QuizRequest): Promise<QuizResponse> {
    const response = await fetch(`${API_BASE}/quiz/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!response.ok) throw new Error('Quiz generation failed');
    return response.json();
  },

  async getProgress(): Promise<ProgressResponse> {
    const response = await fetch(`${API_BASE}/progress/`);
    if (!response.ok) throw new Error('Progress fetch failed');
    return response.json();
  },
};
