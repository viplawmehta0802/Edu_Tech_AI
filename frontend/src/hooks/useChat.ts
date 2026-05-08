import { useState } from 'react';
import { apiClient, ChatRequest, ChatResponse } from '../lib/api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const useChat = (studentId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hi! I'm EduBot, your AI tutor. Ask me anything about math, science, coding, history, or languages. I'll explain concepts, give hints, and help you solve problems step-by-step.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (userMessage: string) => {
    if (!userMessage.trim()) return;

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setError(null);

    try {
      const req: ChatRequest = { student_id: studentId, message: userMessage };
      const res: ChatResponse = await apiClient.chat(req);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Chat failed';
      setError(errMsg);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${errMsg}. Please try again.` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, loading, error, sendMessage };
};
