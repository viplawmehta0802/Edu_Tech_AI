// API client for the EdTech-agent FastAPI backend.
// Default points to local EdTech-agent dev server. Override via VITE_API_URL.
const API_BASE =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────
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

export interface StudentProfile {
  name: string;
  grade: number;
  weak_topics?: string[];
  completed_lessons?: string[];
  study_plans?: unknown[];
  gamification?: {
    points: number;
    badges: string[];
    current_streak: number;
    longest_streak: number;
    last_activity: string | null;
  };
  analytics?: {
    quizzes_taken: number;
    average_score: number;
    total_questions: number;
    correct_answers: number;
    time_spent_minutes: number;
    subjects_practiced: string[];
  };
}

export interface CurriculumSource {
  source: string;
  chunks: number;
  grade: number;
}

export interface ProgressResponse {
  mastery_summary: Record<string, string>;
  weekly_trend: Array<{ day: string; xp: number }>;
}

// ── Client ─────────────────────────────────────────────────────────
export const apiClient = {
  // Chat / tutor
  async chat(req: ChatRequest): Promise<ChatResponse> {
    return http<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  async resetChat(studentId: string): Promise<{ message: string }> {
    return http(`/chat/reset?student_id=${encodeURIComponent(studentId)}`, {
      method: 'POST',
    });
  },

  // Quiz
  async generateQuiz(req: QuizRequest): Promise<QuizResponse> {
    return http<QuizResponse>('/quiz', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  // Students
  async listStudents(): Promise<Record<string, StudentProfile>> {
    return http<Record<string, StudentProfile>>('/students');
  },

  async getStudent(studentId: string): Promise<StudentProfile> {
    return http<StudentProfile>(`/students/${encodeURIComponent(studentId)}`);
  },

  async createStudent(payload: {
    student_id: string;
    name: string;
    grade: number;
  }): Promise<{ message: string; profile: StudentProfile }> {
    return http('/students', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Admin
  async adminLogin(password: string): Promise<{ ok: boolean }> {
    return http('/admin/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  },

  // Curriculum (RAG)
  async listCurriculum(): Promise<{
    sources: CurriculumSource[];
    total_chunks: number;
  }> {
    return http('/curriculum');
  },

  async uploadCurriculum(
    file: File,
    grade = 0
  ): Promise<{ message: string; source: string; pages: number; chunks: number }> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('grade', String(grade));
    const res = await fetch(`${API_BASE}/curriculum/upload`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const b = await res.json();
        detail = b.detail || detail;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }
    return res.json();
  },

  async deleteCurriculum(
    sourceName: string
  ): Promise<{ message: string; chunks_removed: number }> {
    return http(`/curriculum/${encodeURIComponent(sourceName)}`, {
      method: 'DELETE',
    });
  },

  // URL for streaming a curriculum PDF (used by <iframe>)
  curriculumFileUrl(sourceName: string): string {
    return `${API_BASE}/curriculum/file/${encodeURIComponent(sourceName)}`;
  },

  // Short notes from highlighted text
  async summarizeNotes(payload: {
    text: string;
    grade?: number;
    style?: 'bullets' | 'summary' | 'flashcards';
  }): Promise<{ notes: string; style: string }> {
    return http('/notes/summarize', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Generate a quiz from an uploaded Q&A PDF (not added to RAG)
  async quizFromPdf(
    file: File,
    numQuestions = 5,
    grade = 0
  ): Promise<{
    quiz: string;
    source: string;
    extracted_chars: number;
    num_questions: number;
  }> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('num_questions', String(numQuestions));
    fd.append('grade', String(grade));
    const res = await fetch(`${API_BASE}/quiz/from-pdf`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const b = await res.json();
        detail = b.detail || detail;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }
    return res.json();
  },

  // Gamification / analytics
  async getGamification(studentId: string) {
    return http<{ gamification: StudentProfile['gamification'] }>(
      `/students/${encodeURIComponent(studentId)}/gamification`
    );
  },

  async getAnalytics(studentId: string) {
    return http<{ analytics: StudentProfile['analytics'] }>(
      `/students/${encodeURIComponent(studentId)}/analytics`
    );
  },

  // Legacy progress shape (kept so existing Progress page still works)
  async getProgress(studentId?: string): Promise<ProgressResponse> {
    if (studentId) {
      try {
        const [g, a] = await Promise.all([
          this.getGamification(studentId),
          this.getAnalytics(studentId),
        ]);
        const avg = Math.round(a.analytics?.average_score || 0);
        return {
          mastery_summary: {
            Overall: `${avg}%`,
            Quizzes: String(a.analytics?.quizzes_taken || 0),
            Streak: String(g.gamification?.current_streak || 0),
          },
          weekly_trend: [
            { day: 'Mon', xp: 20 },
            { day: 'Tue', xp: 28 },
            { day: 'Wed', xp: 24 },
            { day: 'Thu', xp: 30 },
            { day: 'Fri', xp: 18 },
          ],
        };
      } catch {
        // fall through to mock
      }
    }
    return {
      mastery_summary: { Math: '82%', Science: '76%', Coding: '91%' },
      weekly_trend: [
        { day: 'Mon', xp: 20 },
        { day: 'Tue', xp: 28 },
        { day: 'Wed', xp: 24 },
        { day: 'Thu', xp: 30 },
        { day: 'Fri', xp: 18 },
      ],
    };
  },
};

