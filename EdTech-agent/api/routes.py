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
        msg = str(e)
        if "api_key" in msg.lower() or "authentication" in msg.lower() or "401" in msg:
            raise HTTPException(status_code=500, detail="❌ OpenAI API key is invalid or missing. Edit edtech-agent/.env and set OPENAI_API_KEY, then restart the server.")
        if "quota" in msg.lower() or "insufficient" in msg.lower() or "429" in msg:
            raise HTTPException(status_code=500, detail="❌ OpenAI quota exceeded or billing issue. Check your account at platform.openai.com.")
        raise HTTPException(status_code=500, detail=f"AI error: {msg[:200]}")
    return ChatResponse(reply=reply)


@router.post("/chat/reset", summary="Reset conversation history for a student")
def reset_chat(student_id: str):
    if student_id in _sessions:
        _sessions[student_id].reset_history()
    return {"message": "Conversation history cleared"}


@router.post("/quiz", summary="Generate a quiz on a topic")
def quiz(req: QuizRequest):
    result = generate_quiz(req.topic, req.grade, req.num_questions)
    return {"quiz": result}


@router.post("/evaluate", summary="Evaluate a student's answer")
def evaluate(req: EvaluateRequest):
    feedback = evaluate_answer(req.question, req.student_answer, req.correct_answer, req.grade)
    return {"feedback": feedback}


@router.post("/simplify", summary="Simplify an explanation for a grade level")
def simplify(req: SimplifyRequest):
    result = simplify_explanation(req.text, req.grade)
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
    return {"message": f"Lesson '{lesson}' marked complete"}


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

