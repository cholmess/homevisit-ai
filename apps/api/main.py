from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from src.ingestion.qdrant_ingestion import TenantLawQdrant

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    category: str | None = None
    risk: str | None = None


class SearchResult(BaseModel):
    score: float
    id: Any
    title: str
    category: str
    key_rule: str
    expat_implication: str
    risk_level: str
    source_document: str


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    user_language: str | None = None
    landlord_language: str | None = None
    max_results: int = Field(default=4, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    citations: list[SearchResult]


app = FastAPI(title="HomeVisit AI API")

allowed_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


def _qdrant() -> TenantLawQdrant:
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION", "tenant_law")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if qdrant_url and qdrant_api_key:
        return TenantLawQdrant(
            collection_name=collection_name,
            embedding_model=embedding_model,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
        )

    raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set for cloud Qdrant")


def _latest_user_text(messages: list[ChatMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user" and m.content.strip():
            return m.content.strip()
    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    try:
        q = _qdrant()
        results = q.search(
            req.query,
            limit=req.limit,
            category_filter=req.category,
            risk_filter=req.risk,
        )
        return SearchResponse(results=[SearchResult(**r) for r in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    user_text = _latest_user_text(req.messages)
    if not user_text:
        raise HTTPException(status_code=400, detail="No user message provided")

    try:
        q = _qdrant()
        retrieved = q.search(user_text, limit=req.max_results)
        citations = [SearchResult(**r) for r in retrieved]

        openai_api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not openai_api_key or OpenAI is None:
            answer = "I found relevant tenant-law guidance, but the chat model is not configured. Here are the top items:\n\n" + "\n\n".join(
                f"- {c.title}: {c.key_rule} (risk: {c.risk_level})\n  {c.expat_implication}" for c in citations
            )
            return ChatResponse(answer=answer, citations=citations)

        client = OpenAI(api_key=openai_api_key)

        system_prompt = (
            "You are HomeVisit AI, a rental viewing assistant. "
            "Answer the user's question with concise, practical guidance. "
            "Use the provided tenant-law knowledge snippets as authoritative context. "
            "If the snippets don't contain enough information, say what is missing and ask a clarifying question. "
            "Do not fabricate legal rules. "
            "Format your answer as short paragraphs and, when appropriate, a short checklist."
        )

        knowledge_block = "\n\n".join(
            f"[Snippet {i+1}]\nTitle: {c.title}\nCategory: {c.category}\nRisk: {c.risk_level}\nRule: {c.key_rule}\nExpat implication: {c.expat_implication}"
            for i, c in enumerate(citations)
        )

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": "Tenant-law knowledge snippets:\n\n" + knowledge_block},
                *[{"role": m.role, "content": m.content} for m in req.messages[-12:]],
            ],
            temperature=0.3,
        )

        answer = completion.choices[0].message.content or ""
        return ChatResponse(answer=answer, citations=citations)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
