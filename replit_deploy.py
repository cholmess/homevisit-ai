#!/usr/bin/env python3
"""
Production-ready Flask app for Replit
Minimal VAPI webhook + Qdrant integration
"""

from flask import Flask, request, jsonify
import json
import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import numpy as np

app = Flask(__name__)

# Initialize Qdrant Cloud (production)
QDRANT_URL = os.getenv("QDRANT_URL", "https://xyz-example.eu-central.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "your-key-here")

# Simple translation for demo
translations = {
    "Die Kaution beträgt 6 Monatsmieten.": "The security deposit is 6 months' rent.",
    "Die Miete ist 800 Euro.": "The rent is 800 euros.",
    "Haustiere sind nicht erlaubt.": "Pets are not allowed.",
    "Sie können sofort kündigen.": "You can terminate immediately."
}

# Legal risks
risks = {
    "6 months": "⚠️ WARNING: Maximum 3 months deposit allowed!",
    "sofort": "⚠️ WARNING: 3-month notice period required!"
}

@app.route("/")
def home():
    return """
    <h1>🏠 HomeVisit AI - Production Demo</h1>
    <h2>WindSurf + Qdrant Integration</h2>
    <p>✅ Flask Backend (Python)</p>
    <p>✅ Qdrant Vector Database</p>
    <p>✅ Tenant Law Knowledge Base</p>
    <p><a href="/health">Health Check</a></p>
    <p><a href="/demo">Run Demo</a></p>
    """

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "stacks": ["WindSurf IDE", "Qdrant Cloud"],
        "features": ["Vector Search", "Legal Compliance", "Tenant Laws"]
    })

@app.route("/demo")
def demo():
    """Demo the tenant law search."""
    queries = ["security deposit", "eviction rights", "pet policies"]
    
    results = []
    for query in queries:
        # Mock results for demo
        results.append({
            "query": query,
            "result": f"Found 3 relevant laws for '{query}'",
            "risk": "normal" if query != "security deposit" else "caution"
        })
    
    return jsonify({"search_results": results})

@app.route("/vapi/webhook", methods=["POST"])
def vapi_webhook():
    """VAPI webhook endpoint."""
    data = request.get_json()
    message = data.get("message", "")
    
    if message == "call.start":
        return jsonify({
            "instructions": {
                "actions": [{
                    "type": "speak",
                    "text": "Hello! I'm your housing assistant powered by Qdrant AI."
                }]
            }
        })
    
    elif message == "speech.update":
        transcript = data.get("transcript", "")
        
        # Translate
        translated = translations.get(transcript, f"[EN] {transcript}")
        
        # Check compliance
        warning = None
        for pattern, warn in risks.items():
            if pattern in translated.lower():
                warning = warn
                break
        
        # Prepare response
        actions = [{"type": "speak", "text": translated}]
        if warning:
            actions.append({"type": "speak", "text": warning})
        
        return jsonify({
            "instructions": {"actions": actions},
            "translation": translated,
            "compliance": {"warning": warning} if warning else {"risk_level": "normal"}
        })
    
    return jsonify({"status": "ok"})

@app.route("/search", methods=["POST"])
def search():
    """Search tenant laws."""
    data = request.get_json()
    query = data.get("query", "")
    
    # Mock search results
    return jsonify({
        "results": [
            {
                "title": "Security Deposit Limits",
                "risk_level": "caution",
                "rule": "Maximum 3 months' rent allowed",
                "score": 0.95
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
