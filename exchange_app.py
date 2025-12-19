#!/usr/bin/env python3
"""
Landlord-Tenant Exchange App
WindSurf + Qdrant: Local app for real-time communication
"""

import os
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from src.ingestion.qdrant_ingestion import TenantLawQdrant
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

load_dotenv()

class ExchangeApp:
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
        
        # Conversation history
        self.messages = []
        
        # Create GUI
        self.create_gui()
    
    async def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text using DeepL."""
        if not self.deepl_key:
            # Simple fallback translations
            translations = {
                "Die Kaution beträgt 3 Monatsmieten.": "The security deposit is 3 months' rent.",
                "Die Miete ist 800 Euro warm.": "The rent is 800 euros including utilities.",
                "Haustiere sind nicht erlaubt.": "Pets are not allowed.",
                "Sie können mit 3 Monaten kündigen.": "You can terminate with 3 months notice.",
                "Wann können Sie einziehen?": "When can you move in?",
                "Haben Sie Haustiere?": "Do you have pets?",
                "The rent is 800 euros.": "Die Miete ist 800 Euro.",
                "I have a cat.": "Ich habe eine Katze.",
                "Can I move in next month?": "Kann ich nächsten Monat einziehen?"
            }
            return translations.get(text, f"[{'DE' if target_lang == 'de' else 'EN'}] {text}")
        
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
    
    def search_laws(self, query):
        """Search tenant laws."""
        try:
            results = self.qdrant.search(query, limit=3)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def create_gui(self):
        """Create the GUI interface."""
        self.root = tk.Tk()
        self.root.title("🏠 HomeVisit AI - Landlord-Tenant Exchange")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Title
        title_frame = tk.Frame(self.root, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="🏠 HomeVisit AI - Real-time Communication", 
                font=("Arial", 18, "bold"), bg="#2196F3", fg="white").pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Landlord (German)
        left_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_frame, text="🏢 Landlord (German)", font=("Arial", 14, "bold"), 
                bg="white").pack(pady=10)
        
        self.landlord_input = scrolledtext.ScrolledText(left_frame, height=5, width=40, 
                                                        font=("Arial", 12))
        self.landlord_input.pack(padx=10, pady=5)
        
        tk.Button(left_frame, text="Send →", command=self.send_landlord_message,
                 bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=5)
        
        self.landlord_chat = scrolledtext.ScrolledText(left_frame, height=10, width=40, 
                                                      font=("Arial", 10), state=tk.DISABLED)
        self.landlord_chat.pack(padx=10, pady=10)
        
        # Right side - Tenant (English)
        right_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right_frame, text="👤 Tenant (English)", font=("Arial", 14, "bold"), 
                bg="white").pack(pady=10)
        
        self.tenant_input = scrolledtext.ScrolledText(right_frame, height=5, width=40, 
                                                     font=("Arial", 12))
        self.tenant_input.pack(padx=10, pady=5)
        
        tk.Button(right_frame, text="← Send", command=self.send_tenant_message,
                 bg="#2196F3", fg="white", font=("Arial", 12)).pack(pady=5)
        
        self.tenant_chat = scrolledtext.ScrolledText(right_frame, height=10, width=40, 
                                                    font=("Arial", 10), state=tk.DISABLED)
        self.tenant_chat.pack(padx=10, pady=10)
        
        # Bottom - Legal Assistance
        legal_frame = tk.Frame(self.root, bg="#FFF3E0", relief=tk.RAISED, bd=2)
        legal_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(legal_frame, text="⚖️ Legal Assistance", font=("Arial", 12, "bold"), 
                bg="#FFF3E0").pack(side=tk.LEFT, padx=10, pady=5)
        
        self.legal_info = tk.Label(legal_frame, text="Type a message to get legal help...", 
                                  bg="#FFF3E0", font=("Arial", 10))
        self.legal_info.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Instructions
        instructions = """
Instructions:
• Landlord types in German, Tenant types in English
• Messages are automatically translated
• Legal warnings appear for risky terms
• Use "deposit", "pets", "notice" to test legal search
        """
        tk.Label(self.root, text=instructions, bg="#f0f0f0", justify=tk.LEFT).pack()
    
    def send_landlord_message(self):
        """Send message from landlord to tenant."""
        message = self.landlord_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Add to landlord chat
        self.add_message(self.landlord_chat, f"Landlord: {message}", "sender")
        
        # Translate and add to tenant chat
        async def translate_and_send():
            translated = await self.translate(message, "de", "en")
            self.add_message(self.tenant_chat, f"Landlord: {translated}", "other")
            
            # Check compliance
            compliance = self.check_compliance(translated)
            if compliance["risk_level"] != "normal":
                warning = compliance["warning"]
                self.add_message(self.tenant_chat, f"⚠️ {warning}", "warning")
                self.legal_info.config(text=f"Legal Alert: {warning}")
            
            # Search for relevant laws
            laws = self.search_laws(translated)
            if laws:
                law_text = f"Relevant: {laws[0]['title']} - {laws[0]['key_rule'][:50]}..."
                self.legal_info.config(text=law_text)
        
        # Run async in thread
        threading.Thread(target=lambda: asyncio.run(translate_and_send())).start()
        
        # Clear input
        self.landlord_input.delete("1.0", tk.END)
    
    def send_tenant_message(self):
        """Send message from tenant to landlord."""
        message = self.tenant_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Add to tenant chat
        self.add_message(self.tenant_chat, f"Tenant: {message}", "sender")
        
        # Translate and add to landlord chat
        async def translate_and_send():
            translated = await self.translate(message, "en", "de")
            self.add_message(self.landlord_chat, f"Tenant: {translated}", "other")
            
            # Search for relevant laws
            laws = self.search_laws(message)
            if laws:
                law_text = f"Relevant: {laws[0]['title']} - {laws[0]['key_rule'][:50]}..."
                self.legal_info.config(text=law_text)
        
        # Run async in thread
        threading.Thread(target=lambda: asyncio.run(translate_and_send())).start()
        
        # Clear input
        self.tenant_input.delete("1.0", tk.END)
    
    def add_message(self, chat_widget, message, msg_type="normal"):
        """Add message to chat widget."""
        chat_widget.config(state=tk.NORMAL)
        
        if msg_type == "sender":
            chat_widget.insert(tk.END, message + "\n\n", "sender")
        elif msg_type == "other":
            chat_widget.insert(tk.END, message + "\n\n", "other")
        elif msg_type == "warning":
            chat_widget.insert(tk.END, message + "\n\n", "warning")
        else:
            chat_widget.insert(tk.END, message + "\n\n")
        
        chat_widget.config(state=tk.DISABLED)
        chat_widget.see(tk.END)
        
        # Configure text tags
        chat_widget.tag_config("sender", foreground="blue", font=("Arial", 10, "bold"))
        chat_widget.tag_config("other", foreground="green")
        chat_widget.tag_config("warning", foreground="red", font=("Arial", 10, "bold"))
    
    def run(self):
        """Run the app."""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    print("🏠 Starting HomeVisit AI Exchange App...")
    print("📚 Tech Stack: WindSurf IDE + Qdrant Vector Database")
    print("🔄 Features: Real-time translation + Legal assistance")
    
    app = ExchangeApp()
    app.run()
