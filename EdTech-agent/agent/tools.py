import json
import random
from agent.openai_client import client
from config import MODEL_NAME
from agent.prompts import QUIZ_PROMPT, EVALUATE_PROMPT, SIMPLIFY_PROMPT


def generate_quiz(topic: str, grade: int, num_questions: int = 5) -> str:
    """Generate a quiz on a given topic for a specific grade level."""
    prompt = QUIZ_PROMPT.format(
        topic=topic,
        grade=grade,
        num_questions=num_questions
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content


def evaluate_answer(question: str, student_answer: str, correct_answer: str, grade: int) -> str:
    """Evaluate a student's answer and provide feedback."""
    prompt = EVALUATE_PROMPT.format(
        grade=grade,
        question=question,
        student_answer=student_answer,
        correct_answer=correct_answer
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=400
    )
    return response.choices[0].message.content


def simplify_explanation(text: str, grade: int) -> str:
    """Rewrite a complex explanation for a specific grade level."""
    prompt = SIMPLIFY_PROMPT.format(grade=grade, text=text)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=250
    )
    return response.choices[0].message.content


def get_study_tip(weak_topics: list[str]) -> str:
    """Generate a personalized study tip based on weak topics."""
    if not weak_topics:
        return "Keep up the great work! Review your recent lessons to stay sharp."
    topic = random.choice(weak_topics)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": f"Give one short, actionable study tip for a student struggling with: {topic}"
        }],
        temperature=0.7
    )
    return response.choices[0].message.content


# Tool registry — maps tool names to functions
TOOLS = {
    "generate_quiz": generate_quiz,
    "evaluate_answer": evaluate_answer,
    "simplify_explanation": simplify_explanation,
    "get_study_tip": get_study_tip,
}
