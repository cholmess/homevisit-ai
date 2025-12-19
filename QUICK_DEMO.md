# 🚀 Quick Demo Setup (45 minutes)

## Step 1: Deploy to Railway (0-10 minutes)
1. Go to [railway.app](https://railway.app)
2. "Deploy from GitHub repo" → homevisit-ai
3. Select `vect_db` branch
4. Add environment variables:
   ```
   DEEPL_API_KEY=1ab59204-5951-4457-b8a7-ef9526aea168:fx
   VAPI_API_KEY=2bbba06c-c673-4b4b-8017-f0350f39d84b
   ```
5. Click Deploy
6. Wait for deployment → Get your Railway URL

## Step 2: Setup Frontend (10-20 minutes)
```bash
cd apps/web
npm install
```

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=https://your-railway-url.railway.app
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key
```

Run frontend:
```bash
npm run dev
```

## Step 3: Test Demo (20-30 minutes)
1. Open http://localhost:3000
2. Test the chat interface
3. Show tenant law search
4. Demo VAPI integration (simulated)

## Step 4: Prepare Demo Script (30-45 minutes)

### Demo Flow:
1. **Problem Statement** (1 min)
   - "Expats face language barriers during housing visits"
   - "Legal terms in German contracts can be confusing"

2. **Solution Overview** (1 min)
   - "HomeVisit AI: Real-time translation + legal protection"
   - "Built with VAPI for voice, DeepL for translation, Qdrant for legal knowledge"

3. **Live Demo - Web Interface** (3 mins)
   - Show chat interface asking about tenant rights
   - Search for "security deposit" → Show results
   - Display legal warnings

4. **Live Demo - Voice Translation** (3 mins)
   - Option A: Use VAPI Web SDK in browser
   - Option B: Show simulated demo with `python demo_setup.py`
   - Show German → English translation
   - Show compliance warning for "6 months deposit"

5. **Tech Stack** (1 min)
   - Frontend: Next.js + VAPI Web SDK
   - Backend: FastAPI + DeepL + Qdrant
   - Deployment: Railway

## Key Features to Highlight:
- ✅ Real-time bidirectional translation
- ✅ Legal compliance checking
- ✅ Tenant law knowledge base (56 rules)
- ✅ Voice and text interfaces
- ✅ Sub-300ms latency optimization

## Backup Plans:
- If Railway is slow → Use local demo
- If VAPI fails → Show simulated demo
- If translation fails → Show mock translations

## Success Metrics:
- Working translation demo
- Legal compliance warnings
- Clean UI/UX
- All features functional
