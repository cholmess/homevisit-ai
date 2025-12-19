# HomeVisit AI App

This folder contains the full-stack HomeVisit AI application:

- **`api/`** — FastAPI backend (Python) that connects to Qdrant Cloud and OpenAI
- **`web/`** — Next.js frontend (React + Tailwind) with Vapi voice integration

## Quick Start

### 1. Backend (API)

```bash
cd apps/api

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Check health at `http://localhost:8000/health`.

### 2. Frontend (Web)

```bash
cd apps/web

# Install dependencies
npm install

# Copy and configure environment variables
cp .env.local.example .env.local
# Edit .env.local with your NEXT_PUBLIC_VAPI_PUBLIC_KEY

# Run the dev server
npm run dev
```

The web app will be available at `http://localhost:3000`.

## API Endpoints

| Method | Endpoint  | Description                                      |
|--------|-----------|--------------------------------------------------|
| GET    | /health   | Health check                                     |
| POST   | /search   | Semantic search in Qdrant knowledge base         |
| POST   | /chat     | RAG chat — retrieves from Qdrant + OpenAI answer |

### Example: `/chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "How much deposit can a landlord ask for?"}]}'
```

## Environment Variables

### Backend (`apps/api/.env`)

| Variable           | Required | Description                           |
|--------------------|----------|---------------------------------------|
| QDRANT_URL         | Yes      | Qdrant Cloud URL                      |
| QDRANT_API_KEY     | Yes      | Qdrant API key                        |
| OPENAI_API_KEY     | No*      | OpenAI key for chat answers           |
| OPENAI_MODEL       | No       | Model name (default: gpt-4o-mini)     |
| QDRANT_COLLECTION  | No       | Collection name (default: tenant_law) |
| CORS_ORIGINS       | No       | Comma-separated origins               |

*Without OpenAI key, chat responses will be a formatted list of retrieved snippets.

### Frontend (`apps/web/.env.local`)

| Variable                     | Required | Description                   |
|------------------------------|----------|-------------------------------|
| NEXT_PUBLIC_API_BASE         | No       | API URL (default: localhost)  |
| NEXT_PUBLIC_VAPI_PUBLIC_KEY  | No*      | Vapi public key for voice     |

*Without Vapi key, voice features won't work, but text input will still function.
