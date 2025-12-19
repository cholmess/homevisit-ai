#!/usr/bin/env python3
"""
Simple Localhost Demo: Qdrant + DeepL
Clean interface for hackathon presentation
"""

import os
import httpx
from dotenv import load_dotenv
from src.ingestion.qdrant_ingestion import TenantLawQdrant
import asyncio

load_dotenv()

class HomeVisitAI:
    def __init__(self):
        # Initialize Qdrant
        self.qdrant = TenantLawQdrant(
            collection_name="tenant_law",
            embedding_model="all-MiniLM-L6-v2",
            qdrant_url="http://localhost:6333"
        )
        
        # DeepL translator
        self.deepl_key = os.getenv("DEEPL_API_KEY")
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text using DeepL."""
        if not self.deepl_key:
            # Simple fallback
            translations = {
                "Die Kaution beträgt 6 Monatsmieten.": "The security deposit is 6 months' rent.",
                "Die Miete ist 800 Euro warm.": "The rent is 800 euros including utilities."
            }
            return translations.get(text, f"[EN] {text}")
        
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
    
    def search_laws(self, query):
        """Search tenant laws."""
        results = self.qdrant.search(query, limit=3)
        return results
    
    def check_compliance(self, text):
        """Check if text has legal issues."""
        risks = {
            "6 months": "⚠️ WARNING: Maximum 3 months deposit allowed!",
            "sofort": "⚠️ WARNING: 3-month notice period required!",
            "cash only": "⚡ CAUTION: Bank transfer recommended!"
        }
        
        text_lower = text.lower()
        for pattern, warning in risks.items():
            if pattern in text_lower:
                return {
                    "warning": warning,
                    "risk_level": "red flag" if "WARNING" in warning else "caution"
                }
        return {"risk_level": "normal"}

async def main():
    print("\n=== 🏠 HomeVisit AI - Simple Demo ===\n")
    
    ai = HomeVisitAI()
    
    print("📝 Simulating housing visit conversation...\n")
    
    # Example 1: Landlord speaks German
    print("--- Scenario 1: Security Deposit ---")
    landlord_text = "Die Kaution beträgt 6 Monatsmieten."
    print(f"Landlord (DE): {landlord_text}")
    
    # Translate
    translated = await ai.translate(landlord_text, "de", "en")
    print(f"Tenant (EN): {translated}")
    
    # Check compliance
    compliance = ai.check_compliance(translated)
    if compliance.get("risk_level") != "normal":
        print(f"⚠️ Legal Alert: {compliance['warning']}")
    
    # Search relevant laws
    print("\n🔍 Searching relevant laws...")
    laws = ai.search_laws("security deposit maximum")
    for law in laws[:2]:
        print(f"• {law['title']} - {law['key_rule']}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Tenant asks about pets
    print("--- Scenario 2: Pet Policy ---")
    tenant_question = "Are pets allowed in the apartment?"
    print(f"Tenant (EN): {tenant_question}")
    
    # Search for pet policies
    laws = ai.search_laws("pet policy")
    for law in laws[:2]:
        print(f"• {law['title']} - {law['expat_implication'][:100]}...")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Notice period
    print("--- Scenario 3: Notice Period ---")
    landlord_text = "Sie können sofort kündigen."
    print(f"Landlord (DE): {landlord_text}")
    
    translated = await ai.translate(landlord_text, "de", "en")
    print(f"Tenant (EN): {translated}")
    
    compliance = ai.check_compliance(translated)
    if compliance.get("risk_level") != "normal":
        print(f"⚠️ Legal Alert: {compliance['warning']}")
    
    # Search notice period laws
    print("\n🔍 Searching notice period laws...")
    laws = ai.search_laws("termination notice")
    for law in laws[:2]:
        print(f"• {law['title']} - Risk: {law['risk_level']}")
    
    print("\n✅ Demo Complete!")
    print("\n🛠️  Tech Stack:")
    print("  • Qdrant: Vector database for tenant laws")
    print("  • DeepL: Professional translation")
    print("  • Python: Backend logic")
    print("  • Docker: Local Qdrant instance")

if __name__ == "__main__":
    asyncio.run(main())
