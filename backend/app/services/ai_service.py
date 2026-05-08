import os
from app.core.config import OPENAI_API_BASE, OPENAI_API_KEY, MODEL_NAME

# Placeholder AI logic. Replace with OpenRouter/OpenAI integration.

def generate_response(prompt: str) -> str:
    if not OPENAI_API_KEY:
        return 'AI key not configured. Set OPENAI_API_KEY in environment.'
    return f'[AI response for prompt] {prompt[:120]}'


def generate_quiz(topic: str, grade: int, num_questions: int) -> str:
    return (
        f'Quiz on {topic} for grade {grade}:\n' +
        '\n'.join([f'{i+1}. Sample question {i+1}?' for i in range(num_questions)])
    )


def get_progress_summary(student_id: str) -> dict:
    return {
        'mastery_summary': {
            'Math': '82%',
            'Science': '76%',
            'Coding': '91%',
        },
        'weekly_trend': [
            {'day': 'Mon', 'xp': 20},
            {'day': 'Tue', 'xp': 28},
            {'day': 'Wed', 'xp': 24},
            {'day': 'Thu', 'xp': 30},
            {'day': 'Fri', 'xp': 18},
          ],
    }
