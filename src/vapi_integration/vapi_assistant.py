#!/usr/bin/env python3
"""
VAPI Integration for Expat Housing Visit Assistant
Provides real-time translation and legal compliance checking.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import QDRANT_CONFIG
from src.ingestion.qdrant_ingestion import TenantLawQdrant

# Initialize FastAPI
app = FastAPI(title="Expat Housing Assistant", version="1.0.0")

# Initialize services
qdrant_client = None

class TranslationService:
    """Handles real-time translation using multiple providers."""
    
    def __init__(self):
        self.providers = {
            'deepl': {
                'api_key': os.getenv('DEEPL_API_KEY'),
                'url': 'https://api-free.deepl.com/v2/translate'
            },
            'google': {
                'api_key': os.getenv('GOOGLE_TRANSLATE_API_KEY'),
                'url': 'https://translation.googleapis.com/language/translate/v2'
            }
        }
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text with fallback providers."""
        # Try DeepL first (better quality)
        if self.providers['deepl']['api_key']:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.providers['deepl']['url'],
                        headers={'Authorization': f"DeepL-Auth-Key {self.providers['deepl']['api_key']}"},
                        data={
                            'text': text,
                            'source_lang': source_lang.upper(),
                            'target_lang': target_lang.upper()
                        },
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result['translations'][0]['text']
            except Exception as e:
                print(f"DeepL translation failed: {e}")
        
        # Fallback to Google Translate
        if self.providers['google']['api_key']:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.providers['google']['url'],
                        params={
                            'key': self.providers['google']['api_key'],
                            'q': text,
                            'source': source_lang,
                            'target': target_lang,
                            'format': 'text'
                        },
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result['data']['translations'][0]['translatedText']
            except Exception as e:
                print(f"Google translation failed: {e}")
        
        return text  # Return original if all fail

class ComplianceChecker:
    """Checks statements against tenant law knowledge base."""
    
    def __init__(self, qdrant_client: TenantLawQdrant):
        self.qdrant = qdrant_client
        # Pre-compile risky patterns for quick detection
        self.risk_patterns = [
            "deposit more than",
            "6 months deposit",
            "no notice period",
            "immediate eviction",
            "cash only",
            "no contract",
            "you must pay",
            "illegal fee"
        ]
    
    async def check_compliance(self, text: str, language: str = "en") -> Dict:
        """Check if text contains non-compliant statements."""
        # Quick pattern check first
        text_lower = text.lower()
        quick_risks = [pattern for pattern in self.risk_patterns if pattern in text_lower]
        
        # Full semantic search for detailed compliance
        results = self.qdrant.search(
            text,
            limit=3,
            risk_filter="red flag"
        )
        
        # Determine risk level
        risk_level = "normal"
        if quick_risks or any(r['score'] > 0.7 for r in results):
            risk_level = "caution"
        if any(r['score'] > 0.85 for r in results):
            risk_level = "red flag"
        
        return {
            "risk_level": risk_level,
            "quick_matches": quick_risks,
            "related_rules": [
                {
                    "title": r['title'],
                    "rule": r['key_rule'],
                    "implication": r['expat_implication']
                } for r in results
            ]
        }

class QuestionPrompts:
    """Pre-filled questions for housing visits."""
    
    QUESTIONS = {
        "general": [
            "How long is the rental contract?",
            "What is the monthly rent including utilities?",
            "Is there a security deposit? How much?",
            "When can I move in?",
            "What is the notice period for termination?"
        ],
        "building": [
            "Is the building pet-friendly?",
            "Is there an elevator?",
            "Is there parking available?",
            "What floor is the apartment on?",
            "Are there shared spaces?"
        ],
        "utilities": [
            "Which utilities are included in rent?",
            "How is heating charged?",
            "Is internet included?",
            "Who handles repairs?",
            "Is the apartment energy efficient?"
        ],
        "neighborhood": [
            "What schools are nearby?",
            "How far is the nearest public transport?",
            "Are there supermarkets nearby?",
            "Is the area quiet?",
            "What is the neighborhood like?"
        ],
        "legal": [
            "Can I see the rental contract?",
            "Are there any additional fees?",
            "Who is responsible for minor repairs?",
            "Can I sublet if needed?",
            "Is the rental price registered?"
        ]
    }
    
    @classmethod
    def get_questions(cls, category: str = None) -> List[str]:
        """Get questions by category or all questions."""
        if category and category in cls.QUESTIONS:
            return cls.QUESTIONS[category]
        return [q for questions in cls.QUESTIONS.values() for q in questions]

# Initialize services
translator = TranslationService()
compliance_checker = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global qdrant_client, compliance_checker
    qdrant_client = TenantLawQdrant()
    compliance_checker = ComplianceChecker(qdrant_client)

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Handle VAPI webhook events."""
    data = await request.json()
    
    # Handle different VAPI events
    if data.get("message") == "call.start":
        return await handle_call_start(data)
    elif data.get("message") == "speech.update":
        return await handle_speech_update(data)
    elif data.get("message") == "function.update":
        return await handle_function_call(data)
    elif data.get("message") == "call.end":
        return await handle_call_end(data)
    
    return JSONResponse({"status": "ok"})

async def handle_call_start(data: Dict) -> JSONResponse:
    """Initialize call with welcome message and options."""
    return JSONResponse({
        "instructions": {
            "actions": [
                {
                    "type": "speak",
                    "text": "Welcome to the Ex Housing Assistant. I can translate conversations and check rental terms for legal compliance. Which language are we speaking today?"
                },
                {
                    "type": "listen",
                    "context": "language_detection"
                }
            ]
        }
    })

async def handle_speech_update(data: Dict) -> JSONResponse:
    """Process real-time speech updates."""
    transcript = data.get("transcript", "")
    speaker = data.get("speaker", "user")
    
    if not transcript:
        return JSONResponse({"status": "no_transcript"})
    
    # Detect language if needed
    # For now, assume we know the languages
    
    # Process in parallel for low latency
    tasks = []
    
    # Add translation task
    if speaker == "landlord":
        tasks.append(translate_and_check(transcript, "de", "en"))
    else:
        tasks.append(translate_and_check(transcript, "en", "de"))
    
    # Execute tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Prepare response
    response = {
        "translation": results[0] if not isinstance(results[0], Exception) else None,
        "compliance": None
    }
    
    # Add compliance warning if needed
    if results[0] and not isinstance(results[0], Exception):
        compliance = await compliance_checker.check_compliance(results[0])
        if compliance["risk_level"] != "normal":
            response["compliance"] = compliance
            response["warning"] = generate_compliance_warning(compliance)
    
    return JSONResponse(response)

async def translate_and_check(text: str, from_lang: str, to_lang: str) -> str:
    """Translate text and check for compliance."""
    # Translate
    translated = await translator.translate(text, from_lang, to_lang)
    
    # Quick compliance check
    # This runs in parallel with translation return
    asyncio.create_task(
        compliance_checker.check_compliance(translated)
    )
    
    return translated

def generate_compliance_warning(compliance: Dict) -> str:
    """Generate a user-friendly compliance warning."""
    if compliance["risk_level"] == "red flag":
        return "⚠️ Warning: This statement may violate tenant protection laws. Please verify before agreeing."
    elif compliance["risk_level"] == "caution":
        return "⚡ Caution: This requires clarification. Ask for written confirmation."
    
    return ""

async def handle_function_call(data: Dict) -> JSONResponse:
    """Handle VAPI function calls."""
    function = data.get("function", "")
    parameters = data.get("parameters", {})
    
    if function == "ask_questions":
        category = parameters.get("category", "general")
        questions = QuestionPrompts.get_questions(category)
        
        return JSONResponse({
            "instructions": {
                "actions": [
                    {
                        "type": "speak",
                        "text": f"Here are some important questions to ask: {'. '.join(questions[:3])}"
                    }
                ]
            }
        })
    
    elif function == "check_compliance":
        statement = parameters.get("statement", "")
        compliance = await compliance_checker.check_compliance(statement)
        
        return JSONResponse({
            "compliance": compliance,
            "warning": generate_compliance_warning(compliance)
        })
    
    return JSONResponse({"status": "unknown_function"})

async def handle_call_end(data: Dict) -> JSONResponse:
    """Clean up after call ends."""
    # Log call summary, save transcripts, etc.
    return JSONResponse({"status": "call_ended"})

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "services": {"qdrant": qdrant_client is not None}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
