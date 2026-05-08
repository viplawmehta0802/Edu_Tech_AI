from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    student_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class QuizRequest(BaseModel):
    topic: str
    grade: int
    num_questions: int = 5

class QuizResponse(BaseModel):
    quiz: str

class ProgressResponse(BaseModel):
    mastery_summary: dict
    weekly_trend: List[dict]
