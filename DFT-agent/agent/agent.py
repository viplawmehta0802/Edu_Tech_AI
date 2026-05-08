from agent.openai_client import client
from config import MODEL_NAME
from agent.prompts import SYSTEM_PROMPT
from agent import rag
from memory.student_memory import StudentMemory


class EdTechAgent:
    """
    Core AI agent for the EdTech tutor.
    Maintains per-session conversation history and injects student profile.
    """

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.memory = StudentMemory()
        self.history: list[dict] = []

    def _build_system_message(self) -> dict:
        profile = self.memory.get_student(self.student_id)
        if profile:
            profile_text = (
                f"Name: {profile['name']}\n"
                f"Grade: {profile['grade']}\n"
                f"Weak Topics: {', '.join(profile.get('weak_topics', [])) or 'None identified yet'}\n"
                f"Completed Lessons: {', '.join(profile.get('completed_lessons', [])) or 'None yet'}"
            )
        else:
            profile_text = "New student — no profile data available yet."

        return {
            "role": "system",
            "content": SYSTEM_PROMPT.format(student_profile=profile_text)
        }

    def chat(self, user_message: str) -> str:
        """Send a message to the agent and get a response, using RAG if curriculum is loaded."""
        self.history.append({"role": "user", "content": user_message})

        messages = [self._build_system_message()]

        # ── RAG: retrieve relevant curriculum chunks ──────────────
        profile = self.memory.get_student(self.student_id)
        grade = profile["grade"] if profile else None
        try:
            chunks = rag.retrieve(user_message, grade=grade, k=4)
        except Exception:
            chunks = []

        if chunks:
            context = rag.format_context(chunks)
            messages.append({
                "role": "system",
                "content": (
                    "You have access to the student's curriculum below. "
                    "PREFER this content when answering. If the answer is here, cite the source like (Source: <name>, page X). "
                    "If the answer is NOT in this content, say so briefly and then answer from your general knowledge.\n\n"
                    f"=== CURRICULUM CONTEXT ===\n{context}\n=== END CONTEXT ==="
                )
            })

        messages.extend(self.history)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})

        # Auto-detect if student struggled and update weak topics
        self._update_weak_topics_if_needed(user_message, reply)

        return reply

    def _update_weak_topics_if_needed(self, user_msg: str, reply: str):
        """Heuristic: if the agent detected a mistake, log the topic."""
        struggle_keywords = ["incorrect", "not quite", "wrong", "let's try again", "common mistake"]
        if any(kw in reply.lower() for kw in struggle_keywords):
            topic = self._extract_topic(user_msg)
            if topic:
                self.memory.add_weak_topic(self.student_id, topic)

    def _extract_topic(self, text: str) -> str | None:
        """Simple topic extraction — ask LLM to identify subject in one word."""
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": (
                        f"In one or two words, what academic topic or subject is this message about? "
                        f"Reply with only the topic name, nothing else.\n\nMessage: {text}"
                    )
                }],
                temperature=0,
                max_tokens=10
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return None

    def reset_history(self):
        """Clear conversation history for a new session."""
        self.history = []
