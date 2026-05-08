import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from agent.agent import EdTechAgent
from agent.tools import generate_quiz, evaluate_answer, simplify_explanation, get_study_tip
from agent import rag
from memory.student_memory import StudentMemory
from config import ADMIN_PASSWORD

router = APIRouter()
memory = StudentMemory()

# In-memory session store: { student_id: EdTechAgent }
_sessions: dict[str, EdTechAgent] = {}


def _get_agent(student_id: str) -> EdTechAgent:
    if student_id not in _sessions:
        _sessions[student_id] = EdTechAgent(student_id)
    return _sessions[student_id]


# ── Request / Response Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    student_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class StudentCreateRequest(BaseModel):
    student_id: str
    name: str
    grade: int

class QuizRequest(BaseModel):
    topic: str
    grade: int
    num_questions: int = 5

class EvaluateRequest(BaseModel):
    question: str
    student_answer: str
    correct_answer: str
    grade: int

class SimplifyRequest(BaseModel):
    text: str
    grade: int

class StudyTipRequest(BaseModel):
    student_id: str

class StudyPlanRequest(BaseModel):
    student_id: str
    subject: str
    duration_weeks: int = 4

class QuizResultRequest(BaseModel):
    student_id: str
    topic: str
    score_percentage: float
    questions_count: int
    correct_count: int
    time_spent_minutes: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/admin/login", summary="Verify admin password")
def admin_login(payload: dict):
    if payload.get("password") == ADMIN_PASSWORD:
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid password")


@router.post("/students", summary="Register a new student")
def create_student(req: StudentCreateRequest):
    profile = memory.create_student(req.student_id, req.name, req.grade)
    return {"message": "Student created", "profile": profile}


@router.get("/students/{student_id}", summary="Get student profile")
def get_student(student_id: str):
    profile = memory.get_student(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return profile


@router.get("/students", summary="List all students")
def list_students():
    return memory.get_all_students()


@router.post("/chat", response_model=ChatResponse, summary="Chat with the tutor")
def chat(req: ChatRequest):
    if not memory.get_student(req.student_id):
        raise HTTPException(status_code=404, detail="Student not found. Register first via POST /students")
    agent = _get_agent(req.student_id)
    try:
        reply = agent.chat(req.message)
    except Exception as e:
        raise _format_ai_exception(e)
    return ChatResponse(reply=reply)


def _format_ai_exception(e: Exception) -> HTTPException:
    msg = str(e)
    if "api_key" in msg.lower() or "authentication" in msg.lower() or "401" in msg:
        return HTTPException(status_code=500, detail="❌ OpenAI API key is invalid or missing. Edit edtech-agent/.env and set OPENAI_API_KEY, then restart the server.")
    if "quota" in msg.lower() or "insufficient" in msg.lower() or "429" in msg:
        return HTTPException(status_code=500, detail="❌ OpenAI quota exceeded or billing issue. Check your account and credits.")
    if "402" in msg.lower() or "credits" in msg.lower() or "more credits" in msg.lower():
        return HTTPException(status_code=500, detail="❌ OpenRouter credits are insufficient for this request. Please top up credits or lower the quiz size/model.")
    return HTTPException(status_code=500, detail=f"AI error: {msg[:200]}")


@router.post("/chat/reset", summary="Reset conversation history for a student")
def reset_chat(student_id: str):
    if student_id in _sessions:
        _sessions[student_id].reset_history()
    return {"message": "Conversation history cleared"}


@router.post("/quiz", summary="Generate a quiz on a topic")
def quiz(req: QuizRequest):
    try:
        result = generate_quiz(req.topic, req.grade, req.num_questions)
    except Exception as e:
        raise _format_ai_exception(e)
    return {"quiz": result}


@router.post("/evaluate", summary="Evaluate a student's answer")
def evaluate(req: EvaluateRequest):
    try:
        feedback = evaluate_answer(req.question, req.student_answer, req.correct_answer, req.grade)
    except Exception as e:
        raise _format_ai_exception(e)
    return {"feedback": feedback}


@router.post("/simplify", summary="Simplify an explanation for a grade level")
def simplify(req: SimplifyRequest):
    try:
        result = simplify_explanation(req.text, req.grade)
    except Exception as e:
        raise _format_ai_exception(e)
    return {"simplified": result}


@router.post("/study-tip", summary="Get a personalized study tip")
def study_tip(req: StudyTipRequest):
    profile = memory.get_student(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    tip = get_study_tip(profile.get("weak_topics", []))
    return {"tip": tip}


@router.post("/students/{student_id}/complete-lesson", summary="Mark a lesson as complete")
def complete_lesson(student_id: str, lesson: str):
    if not memory.get_student(student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    memory.mark_lesson_complete(student_id, lesson)
    # Award points for completing a lesson
    memory.update_gamification(student_id, points_earned=10, badge=None, activity=True)
    return {"message": f"Lesson '{lesson}' marked complete", "points_earned": 10}


# ── New Enhanced Features ──────────────────────────────────────────

@router.post("/study-plan", summary="Generate a personalized study plan")
def generate_study_plan(req: StudyPlanRequest):
    profile = memory.get_student(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        plan = generate_study_plan_ai(
            subject=req.subject,
            grade=profile["grade"],
            weak_topics=profile.get("weak_topics", []),
            completed_lessons=profile.get("completed_lessons", []),
            duration_weeks=req.duration_weeks
        )
        memory.add_study_plan(req.student_id, plan)
        # Award points for creating a study plan
        memory.update_gamification(req.student_id, points_earned=25, badge="Planner", activity=True)
        return {"study_plan": plan, "points_earned": 25}
    except Exception as e:
        raise _format_ai_exception(e)


@router.get("/students/{student_id}/study-plans", summary="Get student's study plans")
def get_student_study_plans(student_id: str):
    if not memory.get_student(student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"study_plans": memory.get_study_plans(student_id)}


@router.post("/quiz/result", summary="Record quiz results for analytics")
def record_quiz_result(req: QuizResultRequest):
    if not memory.get_student(req.student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    # Update analytics
    memory.update_analytics(
        student_id=req.student_id,
        quiz_score=req.score_percentage,
        questions_count=req.questions_count,
        correct_count=req.correct_count,
        time_spent=req.time_spent_minutes,
        subject=req.topic
    )

    # Award points based on performance
    points_earned = 0
    badge = None

    if req.score_percentage >= 90:
        points_earned = 50
        badge = "Quiz Master"
    elif req.score_percentage >= 80:
        points_earned = 30
        badge = "Good Student"
    elif req.score_percentage >= 70:
        points_earned = 15
    else:
        points_earned = 5  # Participation points

    memory.update_gamification(req.student_id, points_earned=points_earned, badge=badge, activity=True)

    return {"message": "Quiz result recorded", "points_earned": points_earned, "badge_earned": badge}


@router.get("/students/{student_id}/gamification", summary="Get student's gamification data")
def get_gamification(student_id: str):
    profile = memory.get_student(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"gamification": profile.get("gamification", {})}


@router.get("/students/{student_id}/analytics", summary="Get student's analytics data")
def get_analytics(student_id: str):
    profile = memory.get_student(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"analytics": profile.get("analytics", {})}


# ── Curriculum / RAG endpoints ─────────────────────────────────────

@router.post("/curriculum/upload", summary="Upload a PDF and index it for RAG")
async def upload_curriculum(file: UploadFile = File(...), grade: int = Form(0)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    save_path = os.path.join(rag.CURRICULUM_DIR, file.filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        file.file.close()

    try:
        stats = rag.ingest_pdf(save_path, source_name=file.filename, grade=grade if grade > 0 else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    return {"message": f"'{file.filename}' uploaded and indexed", **stats}


@router.get("/curriculum", summary="List all indexed PDFs")
def list_curriculum():
    return {"sources": rag.list_sources(), "total_chunks": rag.total_chunks()}


@router.delete("/curriculum/{source_name}", summary="Remove a PDF from the index")
def delete_curriculum(source_name: str):
    removed = rag.delete_source(source_name)
    file_path = os.path.join(rag.CURRICULUM_DIR, source_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    return {"message": f"Removed '{source_name}'", "chunks_removed": removed}

