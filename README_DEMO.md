# Hackathon Demo Guide

## Quick Demo Setup (5 minutes)

### 1. Run the Demo Script
```bash
python demo_setup.py
```
This shows a simulated conversation with translation and compliance warnings.

### 2. For Live Demo (if you have VAPI account)
```bash
# Terminal 1: Install ngrok
brew install ngrok

# Terminal 2: Start the server
cd src/vapi_integration
python vapi_assistant_optimized.py

# Terminal 3: Expose to internet
ngrok http 8000
```

Copy the ngrok URL and set it in VAPI dashboard.

## What to Show in Demo

### ✅ Core Features:
1. **Real-time Translation**
   - German → English
   - English → German

2. **Legal Compliance**
   - Instant warnings for illegal terms
   - Risk level indicators

3. **Question Prompts**
   - Pre-filled questions
   - Organized by category

### 📱 Demo Flow:
1. Start with the simulated demo (`demo_setup.py`)
2. Show how it catches illegal deposit requirements
3. Explain the architecture (VAPI + FastAPI + Qdrant)
4. If time, show live call with actual VAPI

## Quick Talking Points

- "Protects expats from unfair rental terms"
- "Real-time translation during housing visits"
- "Based on actual German tenant laws"
- "Sub-300ms response time"
- "Works offline with local models"

## Troubleshooting

- If ngrok doesn't work, just show the pre-recorded demo
- If translation models take time to load, mention they're cached after first use
- For any errors, fall back to the demo script

Good luck with the hackathon! 🚀
