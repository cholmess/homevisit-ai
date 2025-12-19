#!/usr/bin/env python3
"""
Simple web server for HomeVisit AI demo
No npm needed - pure Python
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
from src.ingestion.qdrant_ingestion import TenantLawQdrant
import httpx

app = Flask(__name__)

# Initialize Qdrant
qdrant = TenantLawQdrant(
    collection_name="tenant_law",
    embedding_model="all-MiniLM-L6-v2",
    qdrant_url="http://localhost:6333"
)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HomeVisit AI - Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .demo-section {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .translation {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 10px 0;
        }
        .warning {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 10px 0;
        }
        .law-result {
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
            padding: 15px;
            margin: 10px 0;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover {
            background: #45a049;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .tech-stack {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }
        .tech-item {
            text-align: center;
            padding: 15px;
            background: #e0e0e0;
            border-radius: 5px;
            flex: 1;
        }
        .result-box {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 HomeVisit AI</h1>
            <p>Real-time translation and legal protection for expats</p>
        </div>

        <div class="demo-section">
            <h2>🔍 Search Tenant Laws</h2>
            <input type="text" id="searchInput" placeholder="e.g., security deposit, pets, eviction">
            <button onclick="searchLaws()">Search</button>
            <div id="searchResults" class="result-box"></div>
        </div>

        <div class="demo-section">
            <h2>🔄 Translation Demo</h2>
            <input type="text" id="translateInput" placeholder="Enter German text to translate">
            <button onclick="translateText()">Translate to English</button>
            <div id="translateResult" class="result-box"></div>
        </div>

        <div class="demo-section">
            <h2>📝 Pre-set Scenarios</h2>
            <button onclick="runScenario('deposit')">Security Deposit Issue</button>
            <button onclick="runScenario('pets')">Pet Policy Question</button>
            <button onclick="runScenario('notice')">Notice Period Problem</button>
            <div id="scenarioResult" class="result-box"></div>
        </div>

        <div class="tech-stack">
            <div class="tech-item">
                <h3>Qdrant</h3>
                <p>Vector Database</p>
                <p>56 tenant laws</p>
            </div>
            <div class="tech-item">
                <h3>DeepL</h3>
                <p>Translation API</p>
                <p>German ↔ English</p>
            </div>
            <div class="tech-item">
                <h3>Python</h3>
                <p>Flask Backend</p>
                <p>Localhost</p>
            </div>
        </div>
    </div>

    <script>
        async function searchLaws() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            
            const response = await fetch('/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            });
            
            const results = await response.json();
            const div = document.getElementById('searchResults');
            div.innerHTML = results.map(r => 
                `<div class="law-result">
                    <strong>${r.title}</strong> (Risk: ${r.risk_level})<br>
                    ${r.key_rule}<br>
                    <em>${r.expat_implication.substring(0, 100)}...</em>
                </div>`
            ).join('');
        }

        async function translateText() {
            const text = document.getElementById('translateInput').value;
            if (!text) return;
            
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            });
            
            const result = await response.json();
            const div = document.getElementById('translateResult');
            div.innerHTML = `<div class="translation">
                <strong>Original:</strong> ${text}<br>
                <strong>Translation:</strong> ${result.translation}
            </div>`;
            
            if (result.warning) {
                div.innerHTML += `<div class="warning">⚠️ ${result.warning}</div>`;
            }
        }

        async function runScenario(type) {
            const response = await fetch('/scenario/' + type);
            const result = await response.json();
            const div = document.getElementById('scenarioResult');
            div.innerHTML = result.html;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML_TEMPLATE

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")
    results = qdrant.search(query, limit=3)
    return jsonify(results)

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    
    # Simple translation mock
    translations = {
        "Die Kaution beträgt 6 Monatsmieten.": "The security deposit is 6 months' rent.",
        "Haustiere sind nicht erlaubt.": "Pets are not allowed.",
        "Die Miete ist 800 Euro.": "The rent is 800 euros."
    }
    
    translated = translations.get(text, f"[EN] {text}")
    
    # Check compliance
    warning = None
    if "6 months" in translated.lower():
        warning = "WARNING: Maximum 3 months deposit allowed!"
    
    return jsonify({
        "translation": translated,
        "warning": warning
    })

@app.route("/scenario/<scenario_type>")
def scenario(scenario_type):
    scenarios = {
        "deposit": """
            <div class="translation">
                <strong>Landlord (DE):</strong> "Die Kaution beträgt 6 Monatsmieten."<br>
                <strong>Tenant (EN):</strong> "The security deposit is 6 months' rent."
            </div>
            <div class="warning">
                ⚠️ WARNING: Maximum 3 months deposit allowed!
            </div>
            <div class="law-result">
                <strong>Relevant Law:</strong> Security Deposit Limits<br>
                <strong>Rule:</strong> Maximum 3 months' net rent as security deposit
            </div>
        """,
        "pets": """
            <div class="translation">
                <strong>Tenant (EN):</strong> "Are pets allowed in the apartment?"
            </div>
            <div class="law-result">
                <strong>Found:</strong> Pet Policy<br>
                <strong>Advice:</strong> Get pet permission in writing before signing
            </div>
        """,
        "notice": """
            <div class="translation">
                <strong>Landlord (DE):</strong> "Sie können sofort kündigen."<br>
                <strong>Tenant (EN):</strong> "You can terminate immediately."
            </div>
            <div class="warning">
                ⚠️ WARNING: 3-month notice period required!
            </div>
        """
    }
    
    return jsonify({"html": scenarios.get(scenario_type, "")})

if __name__ == "__main__":
    print("🚀 Starting HomeVisit AI Web Server...")
    print("📱 Open http://localhost:5000 in your browser")
    print("✅ Features: Search, Translation, Scenarios")
    app.run(host="0.0.0.0", port=5000)
