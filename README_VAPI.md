# VAPI Integration for Expat Housing Assistant

This guide shows how to integrate VAPI with your tenant law knowledge base to create a real-time translation and compliance checking assistant for housing visits.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   VAPI      │────▶│ FastAPI     │────▶│ Qdrant      │
│ (Voice I/O) │     │ Backend     │     │ (Legal KB)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │ Translation │
                   │ Services    │
                   │ (DeepL/Google)│
                   └─────────────┘
```

## Features

1. **Real-time Bidirectional Translation**
   - German ↔ English translation during conversations
   - Low latency (< 500ms)
   - Fallback providers for reliability

2. **Legal Compliance Checking**
   - Real-time analysis of landlord statements
   - Instant warnings for non-compliant terms
   - Based on your Qdrant tenant law knowledge base

3. **Pre-filled Question Prompts**
   - Categorized questions (building, utilities, neighborhood, legal)
   - Voice-activated question suggestions
   - Customizable per visit type

4. **Conversation Recording**
   - Full transcript logging
   - Compliance flag timestamps
   - Export for legal review

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements_vapi.txt
```

### 2. Set Up Environment Variables

Create `.env` file:
```env
# Translation APIs
DEEPL_API_KEY=your_deepl_api_key
GOOGLE_TRANSLATE_API_KEY=your_google_api_key

# VAPI Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_PHONE_NUMBER=your_vapi_phone_number

# Backend
BACKEND_URL=https://your-domain.com
WEBHOOK_SECRET=your_webhook_secret
```

### 3. Start the Backend

```bash
cd src/vapi_integration
python vapi_assistant.py
```

### 4. Configure VAPI

1. Go to VAPI dashboard
2. Create new assistant
3. Import `vapi_config.json`
4. Set server URL to your webhook endpoint
5. Add phone number

## Usage Examples

### During Housing Visit

**Landlord says:** "Die Kaution beträgt 6 Monatsmieten."

**Assistant instantly:**
- Translates: "The security deposit is 6 months' rent."
- ⚠️ **Warning:** This exceeds the legal limit of 3 months' rent
- Suggests: "Ask for written confirmation of deposit amount"

**You can ask:** "Ask about building amenities"

**Assistant asks:** "Is there an elevator? Is parking available? Are pets allowed?"

## API Endpoints

### Webhook Endpoint
```
POST /vapi/webhook
```
Handles VAPI events:
- `call.start` - Initialize conversation
- `speech.update` - Process real-time speech
- `function.update` - Execute functions
- `call.end` - Clean up

### Health Check
```
GET /health
```
Returns service status and Qdrant connectivity.

## Performance Optimization

### For Low Latency (< 500ms)

1. **Run Qdrant Locally**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Enable Streaming**
   - VAPI streams transcripts as they're generated
   - Processing starts before utterance completes

3. **Parallel Processing**
   ```python
   # Translation and compliance check run in parallel
   tasks = [
       translate(text),
       check_compliance(text)
   ]
   results = await asyncio.gather(*tasks)
   ```

4. **Cache Translations**
   ```python
   # Redis cache for common phrases
   @lru_cache(maxsize=1000)
   async def cached_translate(text, from_lang, to_lang):
       return await translate_service.translate(text, from_lang, to_lang)
   ```

## Customization

### Adding New Questions

Edit `src/vapi_integration/vapi_assistant.py`:

```python
class QuestionPrompts:
    QUESTIONS = {
        "your_category": [
            "Your custom question 1",
            "Your custom question 2"
        ]
    }
```

### Adding Compliance Rules

The system uses your existing Qdrant knowledge base. To add new rules:

1. Update `unified_tenant_law_knowledge.json`
2. Re-ingest into Qdrant: `make ingest`
3. Rules are immediately available

### Custom Warning Messages

```python
def generate_compliance_warning(compliance):
    if compliance["risk_level"] == "red flag":
        return "Your custom warning message"
```

## Deployment

### Option 1: Railway (Easy)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Option 2: AWS EC2

```bash
# Setup server
sudo apt update
sudo apt install python3-pip nginx
pip3 install -r requirements_vapi.txt

# Run with gunicorn
gunicorn vapi_assistant:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Option 3: Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/vapi-assistant
gcloud run deploy --image gcr.io/PROJECT_ID/vapi-assistant --platform managed
```

## Monitoring

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log compliance warnings
if compliance["risk_level"] != "normal":
    logger.warning(f"Compliance issue: {compliance}")
```

### Metrics
Track:
- Translation latency
- Compliance check frequency
- Warning rate
- Call duration

## Security

1. **HTTPS Only**
   - All endpoints must use HTTPS
   - VAPI requires secure webhooks

2. **API Key Security**
   - Store keys in environment variables
   - Rotate keys regularly

3. **Data Privacy**
   - Transcripts are encrypted at rest
   - Option to auto-delete after 30 days

## Troubleshooting

### High Latency
- Check Qdrant connection: `curl localhost:6333/collections`
- Monitor translation API response times
- Consider caching frequent translations

### Translation Errors
- Check API key validity
- Verify language codes
- Fallback to secondary provider

### Compliance Not Working
- Ensure Qdrant is running
- Check collection has data
- Verify risk level filters

## Next Steps

1. Add multilingual support (French, Spanish)
2. Implement document scanning for contracts
3. Add appointment scheduling
4. Create mobile app companion
5. Integrate with calendar systems

## Support

- VAPI Documentation: https://docs.vapi.ai
- Qdrant Documentation: https://qdrant.tech/documentation
- DeepL API: https://www.deepl.com/docs-api
- Google Translate API: https://cloud.google.com/translate/docs
