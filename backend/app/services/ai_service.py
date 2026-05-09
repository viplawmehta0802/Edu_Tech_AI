import httpx
from app.core.config import OPENAI_API_BASE, OPENAI_API_KEY, MODEL_NAME

DEFAULT_BASE = 'https://api.openai.com/v1'


def _chat(messages: list[dict], temperature: float = 0.7) -> str:
    if not OPENAI_API_KEY:
        return 'AI key not configured. Set OPENAI_API_KEY in environment.'
    base = (OPENAI_API_BASE or DEFAULT_BASE).rstrip('/')
    url = f'{base}/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': MODEL_NAME,
        'messages': messages,
        'temperature': temperature,
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content'].strip()
    except httpx.HTTPStatusError as e:
        return f'AI error ({e.response.status_code}): {e.response.text[:200]}'
    except Exception as e:
        return f'AI error: {e}'


def generate_response(prompt: str) -> str:
    return _chat([
        {'role': 'system', 'content': 'You are EduBot, a helpful AI tutor for students in grades 6-12. Explain clearly and encourage curiosity.'},
        {'role': 'user', 'content': prompt},
    ])


def generate_quiz(topic: str, grade: int, num_questions: int) -> str:
    return _chat([
        {'role': 'system', 'content': 'You are a quiz generator. Output numbered questions only, no answers unless asked.'},
        {'role': 'user', 'content': f'Generate {num_questions} quiz questions on "{topic}" for grade {grade}. Number them 1..{num_questions}.'},
    ], temperature=0.5)


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
