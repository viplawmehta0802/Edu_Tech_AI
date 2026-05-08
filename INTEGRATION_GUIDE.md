# EduBot Frontend + Backend Integration Guide

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd /workspaces/Edu_Tech_AI/backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

4. Run the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

✅ Backend runs on: `http://localhost:8000`

---

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd /workspaces/Edu_Tech_AI/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

✅ Frontend runs on: `http://localhost:4173` (or `http://localhost:5173`)

---

## Testing the Integration

1. Open the frontend in your browser
2. Navigate to the **Tutor** tab
3. Type a question: *"Explain photosynthesis"*
4. The frontend will call `POST /api/tutor/chat` on the backend
5. You should see a response from EduBot AI

---

## API Endpoints

### Chat (Tutor)
- **Endpoint**: `POST /api/tutor/chat`
- **Request**: `{ "student_id": "Av", "message": "Explain X" }`
- **Response**: `{ "reply": "AI response" }`

### Quiz Generation
- **Endpoint**: `POST /api/quiz/`
- **Request**: `{ "topic": "Biology", "grade": 11, "num_questions": 5 }`
- **Response**: `{ "quiz": "Quiz content..." }`

### Progress Analytics
- **Endpoint**: `GET /api/progress/`
- **Response**: `{ "mastery_summary": {...}, "weekly_trend": [...] }`

---

## Next Steps

1. ✅ Connect frontend to backend (Done)
2. 📝 Replace placeholder AI with real OpenAI/OpenRouter calls
3. 🔧 Add database layer for user profiles and quiz history
4. 🎨 Polish UI and add animations
5. 🚀 Deploy to Vercel (frontend) and Railway (backend)

---

## Troubleshooting

### Backend not responding
- Check if backend is running on port 8000
- Verify CORS middleware in `app/main.py`
- Check `.env` file for `OPENAI_API_KEY`

### Frontend not calling backend
- Verify `VITE_API_URL` in `frontend/.env.local`
- Check browser console for API errors
- Ensure both frontend and backend are running

### CORS errors
- Backend CORS is already configured for all origins (`allow_origins=["*"]`)
- If issues persist, check API response headers

---

*Happy learning! 🎓*
