#!/usr/bin/env python3
"""
Test script for VAPI integration without actual VAPI calls.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mock the services for testing
class MockTranslationService:
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        # Simulate translation latency
        await asyncio.sleep(0.1)
        
        # Simple mock translations
        translations = {
            ("Die Kaution beträgt 6 Monatsmieten.", "de", "en"): 
                "The security deposit is 6 months' rent.",
            ("Die Miete ist 800 Euro warm.", "de", "en"):
                "The rent is 800 euros including utilities.",
            ("You must pay 6 months deposit", "en", "de"):
                "Sie müssen 6 Monate Kaution zahlen"
        }
        
        return translations.get((text, source_lang, target_lang), f"[{target_lang}] {text}")

class MockComplianceChecker:
    def __init__(self):
        self.risks = {
            "6 months": {"level": "red flag", "rule": "Maximum 3 months' rent allowed"},
            "no notice": {"level": "red flag", "rule": "3-month notice period required"},
            "cash only": {"level": "caution", "rule": "Bank transfer recommended"}
        }
    
    async def check_compliance(self, text: str) -> dict:
        await asyncio.sleep(0.05)  # Simulate Qdrant query
        
        text_lower = text.lower()
        for pattern, risk in self.risks.items():
            if pattern in text_lower:
                return {
                    "risk_level": risk["level"],
                    "rule": risk["rule"],
                    "warning": self.generate_warning(risk["level"])
                }
        
        return {"risk_level": "normal", "warning": ""}
    
    def generate_warning(self, level: str) -> str:
        if level == "red flag":
            return "⚠️ WARNING: This may violate tenant protection laws!"
        elif level == "caution":
            return "⚡ CAUTION: Verify this in writing."
        return ""

async def simulate_conversation():
    """Simulate a housing visit conversation."""
    print("\n=== Expat Housing Assistant Simulation ===\n")
    
    translator = MockTranslationService()
    compliance_checker = MockComplianceChecker()
    
    # Simulated conversation
    conversations = [
        {"speaker": "landlord", "text": "Die Kaution beträgt 6 Monatsmieten."},
        {"speaker": "tenant", "text": "That seems high. What about utilities?"},
        {"speaker": "landlord", "text": "Die Miete ist 800 Euro warm."},
        {"speaker": "tenant", "text": "Can I have pets?"},
        {"speaker": "landlord", "text": "Pets are not allowed."},
        {"speaker": "landlord", "text": "You must pay 6 months deposit in cash."}
    ]
    
    for i, msg in enumerate(conversations, 1):
        print(f"\n--- Turn {i} ---")
        print(f"{msg['speaker'].title()}: {msg['text']}")
        
        # Process based on speaker
        if msg['speaker'] == 'landlord':
            # Translate to English
            translated = await translator.translate(msg['text'], 'de', 'en')
            print(f"\n🔄 Translation: {translated}")
            
            # Check compliance
            compliance = await compliance_checker.check_compliance(translated)
            if compliance['warning']:
                print(f"\n⚠️  {compliance['warning']}")
                print(f"   Rule: {compliance['rule']}")
        
        await asyncio.sleep(0.5)  # Pause between turns
    
    print("\n=== Simulation Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Real-time translation (German ↔ English)")
    print("✅ Instant compliance checking")
    print("✅ Risk level assessment")
    print("✅ Legal rule references")

async def test_performance():
    """Test latency performance."""
    print("\n=== Performance Test ===\n")
    
    translator = MockTranslationService()
    compliance_checker = MockComplianceChecker()
    
    test_text = "Die Kaution beträgt 6 Monatsmieten."
    
    # Measure translation latency
    start = asyncio.get_event_loop().time()
    translated = await translator.translate(test_text, 'de', 'en')
    translation_time = (asyncio.get_event_loop().time() - start) * 1000
    
    # Measure compliance check latency
    start = asyncio.get_event_loop().time()
    compliance = await compliance_checker.check_compliance(translated)
    compliance_time = (asyncio.get_event_loop().time() - start) * 1000
    
    print(f"Translation latency: {translation_time:.0f}ms")
    print(f"Compliance check latency: {compliance_time:.0f}ms")
    print(f"Total processing time: {translation_time + compliance_time:.0f}ms")
    
    # Target is < 500ms total
    if translation_time + compliance_time < 500:
        print("✅ Meets latency target!")
    else:
        print("⚠️  Exceeds latency target - consider optimization")

async def main():
    """Run all tests."""
    await simulate_conversation()
    await test_performance()

if __name__ == "__main__":
    asyncio.run(main())
