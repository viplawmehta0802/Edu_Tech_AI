from fastapi import APIRouter
from app.core.models import QuizRequest, QuizResponse
from app.services.ai_service import generate_quiz

router = APIRouter()

@router.post('/', response_model=QuizResponse)
def quiz(req: QuizRequest):
    quiz_text = generate_quiz(req.topic, req.grade, req.num_questions)
    return QuizResponse(quiz=quiz_text)
