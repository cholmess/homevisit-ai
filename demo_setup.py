#!/usr/bin/env python3
"""
Quick hackathon demo setup for VAPI integration.
Simplified version that works easily for demos.
"""

import asyncio
import json
import time
from typing import Dict, List
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Simple mock for demo
class DemoAssistant:
    """Simplified demo version for hackathon."""
    
    def __init__(self):
        self.translations = {
            "Die Kaution beträgt 6 Monatsmieten.": "The security deposit is 6 months' rent.",
            "Die Miete ist 800 Euro warm.": "The rent is 800 euros including utilities.",
            "Haustiere sind nicht erlaubt.": "Pets are not allowed.",
            "Sie können sofort kündigen.": "You can terminate immediately."
        }
        
        self.warnings = {
            "6 months": "⚠️ WARNING: Maximum 3 months allowed by law!",
            "sofort": "⚠️ WARNING: 3-month notice period required!",
            "nicht erlaubt": "⚡ CAUTION: Check lease terms carefully"
        }
    
    def process_message(self, message: str, is_landlord: bool = True) -> Dict:
        """Process a message and return translation + compliance."""
        
        # Simulate processing time for demo
        time.sleep(0.5)
        
        result = {
            "original": message,
            "is_landlord": is_landlord,
            "timestamp": time.time()
        }
        
        # Translate if German
        if any(char in message for char in "äöüß") or any(word in message.lower() for word in ["die", "der", "das", "ist", "nicht"]):
            # Simple mock translation
            translated = self.translations.get(message, f"[EN] {message}")
            result["translation"] = translated
            
            # Check compliance
            warning = None
            for pattern, warn_msg in self.warnings.items():
                if pattern.lower() in translated.lower():
                    warning = warn_msg
                    break
            
            if warning:
                result["compliance_warning"] = warning
                result["risk_level"] = "red flag" if "WARNING" in warning else "caution"
            else:
                result["risk_level"] = "normal"
        else:
            result["translation"] = f"[DE] {message}"
            result["risk_level"] = "normal"
        
        return result
    
    def get_suggested_questions(self, category: str = None) -> List[str]:
        """Get suggested questions for the demo."""
        questions = {
            "general": [
                "How much is the security deposit?",
                "What's included in the rent?",
                "When can I move in?"
            ],
            "legal": [
                "Can I see the written contract?",
                "What's the notice period?",
                "Are there additional fees?"
            ],
            "building": [
                "Is pets allowed?",
                "Is there parking?",
                "Which floor is it?"
            ]
        }
        
        if category and category in questions:
            return questions[category]
        return questions["general"]

async def demo_conversation():
    """Run a demo conversation."""
    print("\n=== VAPI Housing Assistant Demo ===\n")
    
    assistant = DemoAssistant()
    
    # Demo conversation
    demo_messages = [
        {"speaker": "landlord", "text": "Die Kaution beträgt 6 Monatsmieten."},
        {"speaker": "tenant", "text": "That seems high. What about pets?"},
        {"speaker": "landlord", "text": "Haustiere sind nicht erlaubt."},
        {"speaker": "tenant", "text": "What's the notice period?"},
        {"speaker": "landlord", "text": "Sie können sofort kündigen."}
    ]
    
    print("Simulating real-time processing...\n")
    
    for i, msg in enumerate(demo_messages, 1):
        print(f"--- Turn {i} ---")
        print(f"{msg['speaker'].title()}: {msg['text']}")
        
        # Process message
        result = assistant.process_message(msg['text'], msg['speaker'] == 'landlord')
        
        print(f"\n🔄 Translation: {result.get('translation', 'N/A')}")
        
        if 'compliance_warning' in result:
            print(f"\n{result['compliance_warning']}")
            print(f"   Risk Level: {result['risk_level']}")
        
        print("\n" + "-"*50 + "\n")
        await asyncio.sleep(1)
    
    # Show suggested questions
    print("\n📝 Suggested Questions for Tenant:")
    for q in assistant.get_suggested_questions():
        print(f"  • {q}")
    
    print("\n✅ Demo Complete! Features shown:")
    print("  • Real-time translation")
    print("  • Legal compliance checking")
    print("  • Risk level assessment")
    print("  • Suggested questions")

def main():
    """Run the demo."""
    print("Starting VAPI Housing Assistant Demo...")
    print("(This simulates what would happen during a real call)")
    
    asyncio.run(demo_conversation())
    
    print("\n🚀 For the actual hackathon demo:")
    print("1. Use ngrok to expose port 8000: ngrok http 8000")
    print("2. Run: python src/vapi_integration/vapi_assistant_optimized.py")
    print("3. Set VAPI webhook to your ngrok URL")
    print("4. Call your VAPI number to show live translation!")

if __name__ == "__main__":
    main()
