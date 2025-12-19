# CodeRabbit Review Request

This PR is created to trigger an automated code review by CodeRabbit.

## Features to Review

### Frontend (Next.js + React)
- `apps/web/src/app/page.tsx` - Main application component
- Real-time speech recognition using native Web Speech API
- Real-time translation between languages
- Vapi voice integration (fallback)
- Chat interface with RAG-powered responses
- Rental Law Help modal with Qdrant search

### Backend (FastAPI)
- `apps/api/main.py` - API endpoints
- `/chat` - RAG-based chat with Qdrant + OpenAI
- `/search` - Direct Qdrant vector search
- `/translate` - Real-time translation
- `/suggestions` - LLM-generated follow-up questions

## Tech Stack
- **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS
- **Backend**: FastAPI, Qdrant Cloud, OpenAI GPT-4o-mini
- **Voice**: Native Web Speech API, Vapi SDK
