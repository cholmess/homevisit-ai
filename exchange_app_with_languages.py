#!/usr/bin/env python3
"""
Landlord-Tenant Exchange App with Language Selection
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
        
        # Supported languages
        self.languages = {
            "English": "en",
            "German": "de",
            "French": "fr",
            "Spanish": "es",
            "Italian": "it",
            "Dutch": "nl",
            "Polish": "pl"
        }
        
        # Conversation history
        self.messages = []
        
        # Create GUI
        self.create_gui()
    
    async def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text using DeepL."""
        if not self.deepl_key:
            # Simple fallback translations for demo
            translations = {
                ("Die Kaution beträgt 3 Monatsmieten.", "de", "en"): "The security deposit is 3 months' rent.",
                ("Die Miete ist 800 Euro warm.", "de", "en"): "The rent is 800 euros including utilities.",
                ("Haustiere sind nicht erlaubt.", "de", "en"): "Pets are not allowed.",
                ("Sie können mit 3 Monaten kündigen.", "de", "en"): "You can terminate with 3 months notice.",
                ("Wann können Sie einziehen?", "de", "en"): "When can you move in?",
                ("Haben Sie Haustiere?", "de", "en"): "Do you have pets?",
                ("The rent is 800 euros.", "en", "de"): "Die Miete ist 800 Euro.",
                ("I have a cat.", "en", "de"): "Ich habe eine Katze.",
                ("Can I move in next month?", "en", "de"): "Kann ich nächsten Monat einziehen?",
                ("Le loyer est de 800 euros.", "fr", "en"): "The rent is 800 euros.",
                ("El alquiler es de 800 euros.", "es", "en"): "The rent is 800 euros."
            }
            key = (text, source_lang, target_lang)
            return translations.get(key, f"[{target_lang.upper()}] {text}")
        
        try:
            response = await self.client.post(
                "https://api-free.deepl.com/v2/translate",
                headers={"Authorization": f"DeepL-Auth-Key {self.deepl_key}"},
                data={
                    "text": text,
                    "source_lang": source_lang.upper() if source_lang != "auto" else "",
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
        self.root.title("🏠 HomeVisit AI - Multi-language Exchange")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f0f0f0")
        
        # Title
        title_frame = tk.Frame(self.root, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="🏠 HomeVisit AI - Real-time Multi-language Communication", 
                font=("Arial", 18, "bold"), bg="#2196F3", fg="white").pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Person A
        left_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Language selector for Person A
        lang_frame_a = tk.Frame(left_frame, bg="white")
        lang_frame_a.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(lang_frame_a, text="🏢 Person A", font=("Arial", 14, "bold"), 
                bg="white").pack(side=tk.LEFT)
        
        self.lang_a_var = tk.StringVar(value="German")
        self.lang_a_dropdown = ttk.Combobox(lang_frame_a, textvariable=self.lang_a_var, 
                                            values=list(self.languages.keys()), 
                                            state="readonly", width=10)
        self.lang_a_dropdown.pack(side=tk.RIGHT, padx=5)
        self.lang_a_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)
        
        self.landlord_input = scrolledtext.ScrolledText(left_frame, height=5, width=40, 
                                                        font=("Arial", 12))
        self.landlord_input.pack(padx=10, pady=5)
        
        tk.Button(left_frame, text="Send →", command=self.send_person_a_message,
                 bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=5)
        
        self.landlord_chat = scrolledtext.ScrolledText(left_frame, height=10, width=40, 
                                                      font=("Arial", 10), state=tk.DISABLED)
        self.landlord_chat.pack(padx=10, pady=10)
        
        # Right side - Person B
        right_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Language selector for Person B
        lang_frame_b = tk.Frame(right_frame, bg="white")
        lang_frame_b.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(lang_frame_b, text="👤 Person B", font=("Arial", 14, "bold"), 
                bg="white").pack(side=tk.LEFT)
        
        self.lang_b_var = tk.StringVar(value="English")
        self.lang_b_dropdown = ttk.Combobox(lang_frame_b, textvariable=self.lang_b_var, 
                                            values=list(self.languages.keys()), 
                                            state="readonly", width=10)
        self.lang_b_dropdown.pack(side=tk.RIGHT, padx=5)
        self.lang_b_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)
        
        self.tenant_input = scrolledtext.ScrolledText(right_frame, height=5, width=40, 
                                                     font=("Arial", 12))
        self.tenant_input.pack(padx=10, pady=5)
        
        tk.Button(right_frame, text="← Send", command=self.send_person_b_message,
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
• Select languages for Person A and Person B using dropdowns
• Type messages in your selected language
• Messages are automatically translated to the other person's language
• Legal warnings appear for risky terms
• Use "deposit", "pets", "notice" to test legal search
        """
        tk.Label(self.root, text=instructions, bg="#f0f0f0", justify=tk.LEFT).pack()
    
    def on_language_change(self, event=None):
        """Handle language change."""
        # Update labels based on selected languages
        lang_a = self.lang_a_var.get()
        lang_b = self.lang_b_var.get()
        
        # Clear chats when language changes
        self.landlord_chat.config(state=tk.NORMAL)
        self.landlord_chat.delete("1.0", tk.END)
        self.landlord_chat.config(state=tk.DISABLED)
        
        self.tenant_chat.config(state=tk.NORMAL)
        self.tenant_chat.delete("1.0", tk.END)
        self.tenant_chat.config(state=tk.DISABLED)
        
        self.legal_info.config(text="Languages updated. Start a new conversation!")
    
    def send_person_a_message(self):
        """Send message from Person A to Person B."""
        message = self.landlord_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Get selected languages
        lang_a = self.languages[self.lang_a_var.get()]
        lang_b = self.languages[self.lang_b_var.get()]
        
        # Add to Person A chat
        self.add_message(self.landlord_chat, f"Person A: {message}", "sender")
        
        # Translate and add to Person B chat
        async def translate_and_send():
            translated = await self.translate(message, lang_a, lang_b)
            self.add_message(self.tenant_chat, f"Person A: {translated}", "other")
            
            # Check compliance (always check in English)
            compliance = self.check_compliance(
                translated if lang_b == "en" else await self.translate(translated, lang_b, "en")
            )
            if compliance["risk_level"] != "normal":
                warning = compliance["warning"]
                self.add_message(self.tenant_chat, f"⚠️ {warning}", "warning")
                self.legal_info.config(text=f"Legal Alert: {warning}")
            
            # Search for relevant laws
            search_query = message if lang_a == "en" else await self.translate(message, lang_a, "en")
            laws = self.search_laws(search_query)
            if laws:
                law_text = f"Relevant: {laws[0]['title']} - {laws[0]['key_rule'][:50]}..."
                self.legal_info.config(text=law_text)
        
        # Run async in thread
        threading.Thread(target=lambda: asyncio.run(translate_and_send())).start()
        
        # Clear input
        self.landlord_input.delete("1.0", tk.END)
    
    def send_person_b_message(self):
        """Send message from Person B to Person A."""
        message = self.tenant_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Get selected languages
        lang_a = self.languages[self.lang_a_var.get()]
        lang_b = self.languages[self.lang_b_var.get()]
        
        # Add to Person B chat
        self.add_message(self.tenant_chat, f"Person B: {message}", "sender")
        
        # Translate and add to Person A chat
        async def translate_and_send():
            translated = await self.translate(message, lang_b, lang_a)
            self.add_message(self.landlord_chat, f"Person B: {translated}", "other")
            
            # Search for relevant laws
            search_query = message if lang_b == "en" else await self.translate(message, lang_b, "en")
            laws = self.search_laws(search_query)
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
    print("🏠 Starting HomeVisit AI Multi-language Exchange App...")
    print("📚 Tech Stack: WindSurf IDE + Qdrant Vector Database")
    print("🌍 Features: Multi-language support + Real-time translation + Legal assistance")
    
    app = ExchangeApp()
    app.run()
