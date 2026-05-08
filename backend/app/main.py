from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.tutor import router as tutor_router
from app.api.quiz import router as quiz_router
from app.api.progress import router as progress_router

app = FastAPI(
    title='EduBot API',
    description='Backend API for EduBot modern learning assistant',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(tutor_router, prefix='/api/tutor')
app.include_router(quiz_router, prefix='/api/quiz')
app.include_router(progress_router, prefix='/api/progress')

@app.get('/')
def root():
    return {'message': 'EduBot backend is running'}
