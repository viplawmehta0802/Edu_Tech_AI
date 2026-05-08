---
title: EduBot AI Tutor
emoji: 🎓
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Personalized AI tutor with RAG-powered curriculum knowledge
---

# 🎓 EduBot AI Tutor

A personalized AI tutoring agent built with FastAPI, OpenAI, and ChromaDB.

## Features
- 💬 Chat with an AI tutor that adapts to each student's grade and weak topics
- 📝 Generate quizzes on any topic
- 📚 Upload your own PDF curriculum — the bot answers from your content (RAG)
- 👨‍💼 Admin panel for managing students and knowledge base

## How to use
1. Click **New Student** on the landing page to create an account
2. Save your Student ID — you'll need it to log in next time
3. Chat with EduBot, take quizzes, or upload curriculum PDFs (Admin → password: `admin123`)

## Configuration (Space Secrets)
- `OPENAI_API_KEY` — required
- `MODEL_NAME` — defaults to `gpt-4o-mini` (cheap & fast)
- `ADMIN_PASSWORD` — change from default!
