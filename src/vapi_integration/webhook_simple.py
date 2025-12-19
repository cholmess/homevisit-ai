#!/usr/bin/env python3
"""
Simplified VAPI webhook for easy deployment
No external dependencies needed for basic functionality
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
from typing import Dict

app = FastAPI(title="VAPI Housing Assistant")

# Simple mock data for demo
LEGAL_RISKS = {
    "6 months": "⚠️ WARNING: Maximum 3 months deposit allowed by law!",
    "sofort": "⚠️ WARNING: 3-month notice period required!",
    "cash only": "⚡ CAUTION: Bank transfer recommended!",
    "no contract": "🚨 RED FLAG: Always get written contract!"
}

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Simple VAPI webhook handler."""
    data = await request.json()
    
    # Handle different VAPI events
    message = data.get("message", "")
    
    if message == "call.start":
        return JSONResponse({
            "instructions": {
                "actions": [{
                    "type": "speak",
                    "text": "Hello! I'm your housing assistant. I can translate conversations and check for legal compliance."
                }]
            }
        })
    
    elif message == "function.update":
        function = data.get("function", "")
        
        if function == "check_compliance":
            statement = data.get("parameters", {}).get("statement", "")
            warning = check_compliance(statement)
            return JSONResponse({"result": warning})
        
        elif function == "ask_questions":
            category = data.get("parameters", {}).get("category", "general")
            questions = get_questions(category)
            return JSONResponse({
                "instructions": {
                    "actions": [{
                        "type": "speak",
                        "text": f"Here are some questions: {'. '.join(questions[:3])}"
                    }]
                }
            })
    
    return JSONResponse({"status": "ok"})

def check_compliance(text: str) -> Dict:
    """Simple compliance check."""
    text_lower = text.lower()
    
    for pattern, warning in LEGAL_RISKS.items():
        if pattern in text_lower:
            return {
                "warning": warning,
                "risk_level": "red flag" if "RED FLAG" in warning else "caution"
            }
    
    return {"risk_level": "normal", "warning": ""}

def get_questions(category: str) -> list:
    """Get questions by category."""
    questions = {
        "general": [
            "How much is the rent?",
            "What's the security deposit?",
            "When can I move in?"
        ],
        "legal": [
            "Can I see the contract?",
            "What's the notice period?",
            "Are there additional fees?"
        ],
        "building": [
            "Are pets allowed?",
            "Is there parking?",
            "Which floor is it?"
        ]
    }
    return questions.get(category, questions["general"])

@app.get("/")
async def root():
    """Health check."""
    return {"status": "VAPI webhook is running!"}

@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "healthy"}

# For local testing
if __name__ == "__main__":
    import uvicorn
    print("Starting VAPI webhook on port 8000...")
    print("Use ngrok: ngrok http 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
