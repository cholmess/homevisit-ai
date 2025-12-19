#!/usr/bin/env python3
"""
Minimal VAPI webhook for PythonAnywhere deployment
No heavy dependencies - just translation and compliance
"""

from flask import Flask, request, jsonify
import json
import os
import httpx

app = Flask(__name__)

# Simple translation (for demo)
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

@app.route("/vapi/webhook", methods=["POST"])
def vapi_webhook():
    data = request.get_json()
    message = data.get("message", "")
    
    if message == "call.start":
        return jsonify({
            "instructions": {
                "actions": [{
                    "type": "speak",
                    "text": "Hello! I'm your housing translator. I'll translate between English and German."
                }]
            }
        })
    
    elif message == "speech.update":
        transcript = data.get("transcript", "")
        speaker = data.get("speaker", "")
        is_final = data.get("is_final", False)
        
        if not transcript or not is_final:
            return jsonify({"status": "processing"})
        
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

@app.route("/")
def home():
    return "VAPI Housing Assistant is running!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
