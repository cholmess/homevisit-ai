#!/usr/bin/env python3
"""
Optimized VAPI Integration with Local Translation for Sub-300ms Latency
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import QDRANT_CONFIG
from src.ingestion.qdrant_ingestion import TenantLawQdrant

# Initialize FastAPI
app = FastAPI(title="Expat Housing Assistant - Optimized", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance monitoring
@dataclass
class Metrics:
    translation_latency: float = 0
    compliance_latency: float = 0
    total_latency: float = 0
    request_count: int = 0

metrics = Metrics()

class LocalTranslationService:
    """Local translation models for ultra-low latency."""
    
    def __init__(self):
        self.models = {}
        self.cache = {}
        self.cache_size = 1000
        self._load_models()
    
    def _load_models(self):
        """Load translation models on startup."""
        try:
            # Try to load local models
            from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
            
            # German to English
            logger.info("Loading DE->EN translation model...")
            self.de_to_en = pipeline(
                "translation_de_to_en",
                model="Helsinki-NLP/opus-mt-de-en",
                device="mps" if sys.platform == "darwin" else "cpu"
            )
            
            # English to German
            logger.info("Loading EN->DE translation model...")
            self.en_to_de = pipeline(
                "translation_en_to_de", 
                model="Helsinki-NLP/opus-mt-en-de",
                device="mps" if sys.platform == "darwin" else "cpu"
            )
            
            logger.info("Translation models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load local models: {e}")
            self.de_to_en = None
            self.en_to_de = None
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text with local models and caching."""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{text[:100]}:{source_lang}:{target_lang}"
        if cache_key in self.cache:
            metrics.translation_latency = (time.time() - start_time) * 1000
            return self.cache[cache_key]
        
        # Use local models if available
        if source_lang == "de" and target_lang == "en" and self.de_to_en:
            result = await self._run_translation(self.de_to_en, text)
        elif source_lang == "en" and target_lang == "de" and self.en_to_de:
            result = await self._run_translation(self.en_to_de, text)
        else:
            # Fallback to simple placeholder
            result = f"[{target_lang.upper()}] {text}"
        
        # Update cache
        if len(self.cache) < self.cache_size:
            self.cache[cache_key] = result
        
        metrics.translation_latency = (time.time() - start_time) * 1000
        return result
    
    async def _run_translation(self, pipeline_model, text: str) -> str:
        """Run translation in thread pool to avoid blocking."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            result = await loop.run_in_executor(
                executor, 
                pipeline_model, 
                text
            )
            return result[0]['translation_text']

class StreamingProcessor:
    """Process streaming transcripts for real-time response."""
    
    def __init__(self, translator, compliance_checker):
        self.translator = translator
        self.compliance_checker = compliance_checker
        self.buffer = ""
        self.last_processed = ""
        
    async def process_stream(self, transcript: str, is_final: bool = False) -> Dict:
        """Process streaming transcript chunks."""
        start_time = time.time()
        
        # Add to buffer
        self.buffer += " " + transcript
        
        # Check for complete sentences
        sentences = self._extract_sentences(self.buffer)
        
        if not sentences:
            return {"status": "buffering"}
        
        # Process the latest complete sentence
        latest_sentence = sentences[-1]
        
        # Run translation and compliance in parallel
        tasks = [
            self.translator.translate(latest_sentence, "de", "en"),
            self.compliance_checker.check_compliance(latest_sentence)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            translation = results[0] if not isinstance(results[0], Exception) else latest_sentence
            compliance = results[1] if not isinstance(results[1], Exception) else {"risk_level": "normal"}
            
            # Update metrics
            metrics.total_latency = (time.time() - start_time) * 1000
            
            response = {
                "translation": translation,
                "compliance": compliance,
                "is_final": is_final,
                "latency_ms": metrics.total_latency
            }
            
            # Generate warning if needed
            if compliance.get("risk_level") != "normal":
                response["warning"] = self._generate_warning(compliance)
            
            return response
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract complete sentences from text."""
        import re
        # Simple sentence detection - can be improved
        sentences = re.findall(r'[^.!?]+[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _generate_warning(self, compliance: Dict) -> str:
        """Generate compliance warning."""
        if compliance.get("risk_level") == "red flag":
            return "⚠️ WARNING: This may violate tenant protection laws!"
        elif compliance.get("risk_level") == "caution":
            return "⚡ CAUTION: Verify this in writing."
        return ""

class OptimizedComplianceChecker:
    """Optimized compliance checking with pre-computed embeddings."""
    
    def __init__(self, qdrant_client: TenantLawQdrant):
        self.qdrant = qdrant_client
        self.risk_patterns = {
            "red_flag": [
                "6 monate", "sechs monate", "deposit more than",
                "no notice", "sofort", "immediate", "cash only",
                "bar nur", "no contract", "kein vertrag"
            ],
            "caution": [
                "3 monate", "drei monate", "additional fees",
                "sondergebühren", "non-refundable", "nicht erstattungsfähig"
            ]
        }
        
        # Pre-embed risk patterns for fast matching
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """Pre-compute embeddings for risk patterns."""
        self.pattern_embeddings = {}
        for level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                # Generate embedding once
                embedding = self.qdrant.model.encode(pattern, convert_to_tensor=False)
                self.pattern_embeddings[pattern] = embedding
    
    async def check_compliance(self, text: str) -> Dict:
        """Ultra-fast compliance check."""
        start_time = time.time()
        
        text_lower = text.lower()
        
        # Quick pattern matching (sub-10ms)
        for level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    metrics.compliance_latency = (time.time() - start_time) * 1000
                    return {
                        "risk_level": level.replace("_", " "),
                        "pattern": pattern,
                        "warning": self._get_warning_message(level)
                    }
        
        # If no quick match, do semantic search (50-100ms)
        try:
            results = self.qdrant.search(
                text,
                limit=2,
                risk_filter="red flag"
            )
            
            if results and results[0]['score'] > 0.8:
                metrics.compliance_latency = (time.time() - start_time) * 1000
                return {
                    "risk_level": "red flag",
                    "match": results[0]['title'],
                    "warning": "⚠️ WARNING: This may violate tenant protection laws!"
                }
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
        
        metrics.compliance_latency = (time.time() - start_time) * 1000
        return {"risk_level": "normal"}
    
    def _get_warning_message(self, level: str) -> str:
        """Get warning message for risk level."""
        if level == "red_flag":
            return "⚠️ WARNING: This may violate tenant protection laws!"
        elif level == "caution":
            return "⚡ CAUTION: Verify this in writing."
        return ""

# Initialize services
translator = LocalTranslationService()
qdrant_client = TenantLawQdrant()
compliance_checker = OptimizedComplianceChecker(qdrant_client)
stream_processor = StreamingProcessor(translator, compliance_checker)

# WebSocket connection for streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for ultra-low latency streaming."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "transcript":
                # Process streaming transcript
                result = await stream_processor.process_stream(
                    message.get("text", ""),
                    message.get("is_final", False)
                )
                
                await manager.send_personal_message(
                    json.dumps(result),
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Handle VAPI webhook events with optimization."""
    data = await request.json()
    start_time = time.time()
    
    metrics.request_count += 1
    
    # Route to appropriate handler
    if data.get("message") == "speech.update":
        # Use streaming endpoint for real-time
        result = await stream_processor.process_stream(
            data.get("transcript", ""),
            data.get("is_final", False)
        )
        
        # Log performance
        logger.info(f"Request {metrics.request_count}: {metrics.total_latency:.0f}ms")
        
        return JSONResponse(result)
    
    # Handle other events...
    return JSONResponse({"status": "ok"})

@app.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    return {
        "translation_latency_ms": metrics.translation_latency,
        "compliance_latency_ms": metrics.compliance_latency,
        "total_latency_ms": metrics.total_latency,
        "requests_processed": metrics.request_count,
        "cache_size": len(translator.cache)
    }

@app.post("/test/latency")
async def test_latency():
    """Test end-to-end latency."""
    test_sentences = [
        "Die Kaution beträgt drei Monatsmieten.",
        "Die Miete ist warm 800 Euro.",
        "Sie können nicht kündigen."
    ]
    
    results = []
    for sentence in test_sentences:
        start = time.time()
        
        # Process full pipeline
        translation = await translator.translate(sentence, "de", "en")
        compliance = await compliance_checker.check_compliance(translation)
        
        latency = (time.time() - start) * 1000
        results.append({
            "original": sentence,
            "translation": translation,
            "compliance": compliance,
            "latency_ms": latency
        })
    
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    
    return {
        "results": results,
        "average_latency_ms": avg_latency,
        "target_met": avg_latency < 300
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
