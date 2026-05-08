from fastapi import APIRouter
from app.core.models import ProgressResponse
from app.services.ai_service import get_progress_summary

router = APIRouter()

@router.get('/', response_model=ProgressResponse)
def progress():
    return get_progress_summary('default-student')
