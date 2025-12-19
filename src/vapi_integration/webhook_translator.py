#!/usr/bin/env python3
"""
Enhanced VAPI webhook with bidirectional translation
Translates speech and speaks back in target language
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
import httpx
from typing import Dict, Optional
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VAPI Housing Translator")

# Translation service
class TranslationService:
    def __init__(self):
        self.deepl_key = os.getenv("DEEPL_API_KEY")
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using DeepL."""
        if not self.deepl_key:
            # Fallback to mock translation
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

# Legal compliance checker
class ComplianceChecker:
    def __init__(self):
        self.risks = {
            "6 months": "⚠️ WARNING: Maximum 3 months deposit allowed!",
            "sofort": "⚠️ WARNING: 3-month notice period required!",
            "cash only": "⚡ CAUTION: Bank transfer recommended!"
        }
    
    async def check(self, text: str) -> Dict:
        """Check text for compliance issues."""
        text_lower = text.lower()
        for pattern, warning in self.risks.items():
            if pattern in text_lower:
                return {
                    "warning": warning,
                    "risk_level": "red flag" if "WARNING" in warning else "caution"
                }
        return {"risk_level": "normal"}

# Initialize services
translator = TranslationService()
compliance = ComplianceChecker()

# Session storage for language preferences
sessions = {}

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Enhanced VAPI webhook with translation."""
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
        return JSONResponse({
            "instructions": {
                "actions": [{
                    "type": "speak",
                    "text": "Hello! I'm your housing translator. I'll translate between English and German, and check for any legal issues. Which language does the landlord speak?"
                }]
            }
        })
    
    elif message == "speech.update":
        # Handle speech transcription
        transcript = data.get("transcript", "")
        speaker = data.get("speaker", "user")
        is_final = data.get("is_final", False)
        
        if not transcript or not is_final:
            return JSONResponse({"status": "processing"})
        
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
        compliance_result = await compliance.check(
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
        
        return JSONResponse({
            "instructions": {"actions": actions},
            "translation": {
                "original": transcript,
                "translated": translated,
                "from": source_lang,
                "to": target_lang
            },
            "compliance": compliance_result
        })
    
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
            
            return JSONResponse({
                "instructions": {
                    "actions": [{
                        "type": "speak",
                        "text": f"Language set to {lang} for {speaker}"
                    }]
                }
            })
        
        elif function == "translate_text":
            text = params.get("text", "")
            from_lang = params.get("from", "auto")
            to_lang = params.get("to", "en")
            
            translated = await translator.translate(text, from_lang, to_lang)
            
            return JSONResponse({
                "translation": translated,
                "instructions": {
                    "actions": [{
                        "type": "speak",
                        "text": translated
                    }]
                }
            })
    
    return JSONResponse({"status": "ok"})

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

@app.get("/")
async def root():
    """Health check."""
    return {"status": "VAPI translator webhook is running!"}

@app.get("/health")
async def health():
    """Health check with services status."""
    return {
        "status": "healthy",
        "services": {
            "translation": bool(os.getenv("DEEPL_API_KEY")),
            "compliance": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting VAPI translator webhook on port 8000...")
    print("Features:")
    print("- Automatic bidirectional translation")
    print("- Legal compliance checking")
    print("- Language preference storage")
    print("\nUse ngrok: ngrok http 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
