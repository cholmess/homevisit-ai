from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from src.ingestion.qdrant_ingestion import TenantLawQdrant

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


# VAPI Translation Models
class VapiMessage(BaseModel):
    message: str
    call: dict = {}
    transcript: str = ""
    speaker: str = ""
    is_final: bool = False


class VapiRequest(BaseModel):
    message: str
    call: dict = {}
    transcript: str = ""
    speaker: str = ""
    is_final: bool = False
    function: str = ""
    parameters: dict = {}


# Translation Service
class TranslationService:
    def __init__(self):
        self.deepl_key = os.getenv("DEEPL_API_KEY")
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using DeepL."""
        if not self.deepl_key:
            # Fallback translations for demo
            translations = {
                ("Die Kaution beträgt 6 Monatsmieten.", "de", "en"): "The security deposit is 6 months' rent.",
                ("The rent is 800 euros", "en", "de"): "Die Miete ist 800 Euro."
            }
            key = (text, source_lang, target_lang)
            return translations.get(key, f"[{target_lang.upper()}] {text}")
        
        try:
            response = await self.client.post(
                "https://api-free.deepl.com/v2/translate",
                headers={"Authorization": f"DeepL-Auth-Key {self.deepl_key}"},
                data={
                    "text": text,
                    "source_lang": source_lang.upper(),
                    "target_lang": target_lang.upper()
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["translations"][0]["text"]
            
        except Exception as e:
            print(f"Translation error: {e}")
        
        return text


# Initialize services
translator = TranslationService()
sessions = {}  # Store language preferences per call


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
    suggestions: list[str] = Field(default_factory=list)


class SuggestionsRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    context: str = ""


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1)
    source_language: str = "en"
    target_language: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str


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

        # Generate follow-up suggestions
        suggestions: list[str] = []
        try:
            suggestion_completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Based on the conversation about rental/tenant topics, suggest 3 brief follow-up questions "
                            "the user might want to ask. Focus on practical concerns for someone viewing a rental property. "
                            "Return ONLY the 3 questions, one per line, no numbering or bullets."
                        )
                    },
                    {"role": "user", "content": f"Conversation context: {user_text}\n\nAssistant's answer: {answer[:500]}"},
                ],
                temperature=0.7,
                max_tokens=150,
            )
            suggestion_text = suggestion_completion.choices[0].message.content or ""
            suggestions = [s.strip() for s in suggestion_text.strip().split("\n") if s.strip()][:3]
        except Exception:
            suggestions = [
                "What should I check during the viewing?",
                "What are my rights regarding the deposit?",
                "Can the landlord increase the rent?"
            ]

        return ChatResponse(answer=answer, citations=citations, suggestions=suggestions)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/suggestions", response_model=SuggestionsResponse)
def get_suggestions(req: SuggestionsRequest) -> SuggestionsResponse:
    """Generate follow-up question suggestions based on conversation context."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Default suggestions if no OpenAI
    default_suggestions = [
        "What should I check during the apartment viewing?",
        "What are the rules about security deposits?",
        "How much notice do I need to give to move out?",
        "What repairs is the landlord responsible for?",
        "Can the landlord enter my apartment without permission?"
    ]

    if not openai_api_key or OpenAI is None:
        return SuggestionsResponse(suggestions=default_suggestions[:3])

    try:
        client = OpenAI(api_key=openai_api_key)

        # Build context from messages
        context = req.context or ""
        if req.messages:
            context += "\n".join([f"{m.role}: {m.content}" for m in req.messages[-6:]])

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are helping someone prepare for a rental property viewing. "
                        "Based on the conversation, suggest 3 relevant follow-up questions they should ask. "
                        "Focus on practical tenant concerns. Return ONLY the 3 questions, one per line."
                    )
                },
                {"role": "user", "content": f"Context: {context}" if context else "Generate 3 general rental viewing questions."},
            ],
            temperature=0.7,
            max_tokens=150,
        )

        suggestion_text = completion.choices[0].message.content or ""
        suggestions = [s.strip() for s in suggestion_text.strip().split("\n") if s.strip()][:3]

        if not suggestions:
            suggestions = default_suggestions[:3]

        return SuggestionsResponse(suggestions=suggestions)

    except Exception:
        return SuggestionsResponse(suggestions=default_suggestions[:3])


# VAPI Webhook Endpoints
@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """VAPI webhook for bidirectional translation."""
    data = await request.json()
    
    # Extract session info
    call_id = data.get("call", {}).get("id", "default")
    message = data.get("message", "")
    
    # Initialize session
    if call_id not in sessions:
        sessions[call_id] = {
            "landlord_language": "de",  # Default
            "tenant_language": "en",   # Default
            "current_speaker": None
        }
    
    session = sessions[call_id]
    
    # Handle different events
    if message == "call.start":
        return {
            "instructions": {
                "actions": [{
                    "type": "speak",
                    "text": "Hello! I'm your housing translator. I'll translate between English and German, and check for any legal issues. Which language does the landlord speak?"
                }]
            }
        }
    
    elif message == "speech.update":
        # Handle speech transcription
        transcript = data.get("transcript", "")
        speaker = data.get("speaker", "user")
        is_final = data.get("is_final", False)
        
        if not transcript or not is_final:
            return {"status": "processing"}
        
        # Store speaker
        session["current_speaker"] = speaker
        
        # Determine languages
        if speaker == "landlord":
            source_lang = session["landlord_language"]
            target_lang = session["tenant_language"]
        else:
            source_lang = session["tenant_language"]
            target_lang = session["landlord_language"]
        
        # Detect language if needed
        if any(char in transcript for char in "äöüß"):
            source_lang = "de"
        elif any(word in transcript.lower() for word in ["the", "and", "is", "you"]):
            source_lang = "en"
        
        # Translate to other language
        translated = await translator.translate(transcript, source_lang, target_lang)
        
        # Check compliance (always check in English)
        compliance_result = await check_compliance(
            translated if source_lang == "en" else transcript
        )
        
        # Prepare response
        actions = []
        
        # Speak the translation
        if translated != transcript:
            actions.append({
                "type": "speak",
                "text": translated
            })
        
        # Add compliance warning if needed
        if compliance_result.get("risk_level") != "normal":
            actions.append({
                "type": "speak",
                "text": compliance_result["warning"]
            })
        
        return {
            "instructions": {"actions": actions},
            "translation": {
                "original": transcript,
                "translated": translated,
                "from": source_lang,
                "to": target_lang
            },
            "compliance": compliance_result
        }
    
    elif message == "function.update":
        # Handle function calls
        function = data.get("function", "")
        params = data.get("parameters", {})
        
        if function == "set_language":
            lang = params.get("language", "en")
            speaker = params.get("speaker", "landlord")
            
            if speaker == "landlord":
                session["landlord_language"] = lang
            else:
                session["tenant_language"] = lang
            
            return {
                "instructions": {
                    "actions": [{
                        "type": "speak",
                        "text": f"Language set to {lang} for {speaker}"
                    }]
                }
            }
        
        elif function == "translate_text":
            text = params.get("text", "")
            from_lang = params.get("from", "auto")
            to_lang = params.get("to", "en")
            
            translated = await translator.translate(text, from_lang, to_lang)
            
            return {
                "translation": translated,
                "instructions": {
                    "actions": [{
                        "type": "speak",
                        "text": translated
                    }]
                }
            }
    
    return {"status": "ok"}


async def check_compliance(text: str) -> dict:
    """Check text for compliance issues."""
    risks = {
        "6 months": "⚠️ WARNING: Maximum 3 months deposit allowed!",
        "sofort": "⚠️ WARNING: 3-month notice period required!",
        "cash only": "⚡ CAUTION: Bank transfer recommended!"
    }
    
    text_lower = text.lower()
    for pattern, warning in risks.items():
        if pattern in text_lower:
            return {
                "warning": warning,
                "risk_level": "red flag" if "WARNING" in warning else "caution"
            }
    return {"risk_level": "normal"}


@app.post("/vapi/set-language")
async def set_language(call_id: str, speaker: str, language: str):
    """API to set language preference."""
    if call_id not in sessions:
        sessions[call_id] = {
            "landlord_language": "de",
            "tenant_language": "en"
        }
    
    if speaker == "landlord":
        sessions[call_id]["landlord_language"] = language
    else:
        sessions[call_id]["tenant_language"] = language
    
    return {"status": "language set"}


# Language code mapping for translation
LANG_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    """Translate text between languages using OpenAI."""
    # If same language, return as-is
    if req.source_language == req.target_language:
        return TranslateResponse(
            translated_text=req.text,
            source_language=req.source_language,
            target_language=req.target_language
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not openai_api_key or OpenAI is None:
        # Return original text if no API key
        return TranslateResponse(
            translated_text=req.text,
            source_language=req.source_language,
            target_language=req.target_language
        )

    try:
        client = OpenAI(api_key=openai_api_key)

        source_name = LANG_NAMES.get(req.source_language, req.source_language)
        target_name = LANG_NAMES.get(req.target_language, req.target_language)

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate the following text from {source_name} to {target_name}. Return ONLY the translated text, nothing else."
                },
                {"role": "user", "content": req.text}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        translated = completion.choices[0].message.content or req.text
        return TranslateResponse(
            translated_text=translated.strip(),
            source_language=req.source_language,
            target_language=req.target_language
        )

    except Exception:
        return TranslateResponse(
            translated_text=req.text,
            source_language=req.source_language,
            target_language=req.target_language
        )
