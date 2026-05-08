from fastapi import APIRouter
from app.core.models import ChatRequest, ChatResponse
from app.services.ai_service import generate_response

router = APIRouter()

@router.post('/chat', response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = generate_response(req.message)
    return ChatResponse(reply=reply)
