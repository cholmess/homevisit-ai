'use client';

import { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, AlertTriangle, Scale, Globe } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'nl', name: 'Dutch', flag: '🇳🇱' },
  { code: 'pl', name: 'Polish', flag: '🇵🇱' }
];

type Message = {
  id: string;
  sender: 'personA' | 'personB';
  text: string;
  translated?: string;
  timestamp: Date;
  type?: 'warning' | 'normal';
};

type LegalInfo = {
  type: 'warning' | 'info';
  content: string;
};

export default function ExchangePage() {
  const [personALang, setPersonALang] = useState('de');
  const [personBLang, setPersonBLang] = useState('en');
  const [personAInput, setPersonAInput] = useState('');
  const [personBInput, setPersonBInput] = useState('');
  const [messagesA, setMessagesA] = useState<Message[]>([]);
  const [messagesB, setMessagesB] = useState<Message[]>([]);
  const [legalInfo, setLegalInfo] = useState<LegalInfo | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);

  // Mock translation function (replace with real API call)
  const translateText = async (text: string, from: string, to: string): Promise<string> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock translations for demo
    const translations: Record<string, Record<string, Record<string, string>>> = {
      de: {
        en: {
          'Die Kaution beträgt 3 Monatsmieten.': 'The security deposit is 3 months\' rent.',
          'Die Miete ist 800 Euro warm.': 'The rent is 800 euros including utilities.',
          'Haustiere sind nicht erlaubt.': 'Pets are not allowed.',
          'Wann können Sie einziehen?': 'When can you move in?',
          'Die Wohnung ist im 3. Stock.': 'The apartment is on the 3rd floor.'
        }
      },
      en: {
        de: {
          'The rent is 800 euros.': 'Die Miete ist 800 Euro.',
          'I have a cat.': 'Ich habe eine Katze.',
          'Can I move in next month?': 'Kann ich nächsten Monat einziehen?',
          'Is parking available?': 'Ist ein Parkplatz vorhanden?',
          'The deposit is too high.': 'Die Kaution ist zu hoch.'
        }
      }
    };
    
    return translations[from]?.[to]?.[text] || `[${to.toUpperCase()}] ${text}`;
  };

  // Check for legal compliance
  const checkCompliance = (text: string): LegalInfo | null => {
    const risks = [
      { pattern: /6 months|6 monatsmieten/i, warning: '⚠️ WARNING: Maximum 3 months deposit allowed!' },
      { pattern: /sofort|immediately/i, warning: '⚠️ WARNING: 3-month notice period required!' },
      { pattern: /cash only|nur bar/i, warning: '⚡ CAUTION: Bank transfer recommended!' }
    ];
    
    for (const risk of risks) {
      if (risk.pattern.test(text)) {
        return { type: 'warning', content: risk.warning };
      }
    }
    
    return null;
  };

  // Send message from Person A to Person B
  const sendPersonAMessage = async () => {
    if (!personAInput.trim()) return;
    
    setIsTranslating(true);
    
    const messageId = Date.now().toString();
    const message: Message = {
      id: messageId,
      sender: 'personA',
      text: personAInput,
      timestamp: new Date()
    };
    
    // Add to Person A's chat
    setMessagesA(prev => [...prev, message]);
    
    // Translate and add to Person B's chat
    const translated = await translateText(personAInput, personALang, personBLang);
    const translatedMessage: Message = {
      ...message,
      text: translated,
      translated: personAInput
    };
    
    setMessagesB(prev => [...prev, translatedMessage]);
    
    // Check compliance (always check in English)
    const textToCheck = personBLang === 'en' ? translated : await translateText(translated, personBLang, 'en');
    const compliance = checkCompliance(textToCheck);
    
    if (compliance) {
      setLegalInfo(compliance);
      const warningMessage: Message = {
        id: messageId + '-warning',
        sender: 'personB',
        text: compliance.content,
        timestamp: new Date(),
        type: 'warning'
      };
      setMessagesB(prev => [...prev, warningMessage]);
    }
    
    // Search for relevant laws (mock)
    if (textToCheck.toLowerCase().includes('deposit')) {
      setLegalInfo({
        type: 'info',
        content: '📚 Relevant Law: Security Deposit Limits - Maximum 3 months\' net rent allowed'
      });
    }
    
    setPersonAInput('');
    setIsTranslating(false);
  };

  // Send message from Person B to Person A
  const sendPersonBMessage = async () => {
    if (!personBInput.trim()) return;
    
    setIsTranslating(true);
    
    const messageId = Date.now().toString();
    const message: Message = {
      id: messageId,
      sender: 'personB',
      text: personBInput,
      timestamp: new Date()
    };
    
    // Add to Person B's chat
    setMessagesB(prev => [...prev, message]);
    
    // Translate and add to Person A's chat
    const translated = await translateText(personBInput, personBLang, personALang);
    const translatedMessage: Message = {
      ...message,
      text: translated,
      translated: personBInput
    };
    
    setMessagesA(prev => [...prev, translatedMessage]);
    
    setPersonBInput('');
    setIsTranslating(false);
  };

  const getLanguageDisplay = (code: string) => {
    const lang = LANGUAGES.find(l => l.code === code);
    return lang ? `${lang.flag} ${lang.name}` : code;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold">🏠 HomeVisit AI</h1>
            <span className="text-blue-200">Multi-language Exchange</span>
          </div>
          <div className="flex items-center space-x-4 text-sm">
            <span className="flex items-center space-x-1">
              <Globe className="w-4 h-4" />
              <span>WindSurf + Qdrant</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          
          {/* Person A */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gray-100 p-4 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold flex items-center space-x-2">
                  <span>🏢 Person A</span>
                </h2>
                <select
                  value={personALang}
                  onChange={(e) => setPersonALang(e.target.value)}
                  className="px-3 py-1 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LANGUAGES.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* Chat Area */}
            <div className="h-96 overflow-y-auto p-4 space-y-3">
              {messagesA.map(msg => (
                <div key={msg.id} className={`flex ${msg.sender === 'personA' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-4 py-2 rounded-lg ${
                    msg.sender === 'personA' 
                      ? 'bg-blue-600 text-white' 
                      : msg.type === 'warning'
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    <p className="text-sm">{msg.text}</p>
                    {msg.translated && (
                      <p className="text-xs opacity-75 mt-1 italic">Original: {msg.translated}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Input Area */}
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={personAInput}
                  onChange={(e) => setPersonAInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendPersonAMessage()}
                  placeholder={`Type in ${getLanguageDisplay(personALang).split(' ')[1]}...`}
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isTranslating}
                />
                <button
                  onClick={sendPersonAMessage}
                  disabled={isTranslating}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-1"
                >
                  <span>Send</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Person B */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gray-100 p-4 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold flex items-center space-x-2">
                  <span>👤 Person B</span>
                </h2>
                <select
                  value={personBLang}
                  onChange={(e) => setPersonBLang(e.target.value)}
                  className="px-3 py-1 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LANGUAGES.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* Chat Area */}
            <div className="h-96 overflow-y-auto p-4 space-y-3">
              {messagesB.map(msg => (
                <div key={msg.id} className={`flex ${msg.sender === 'personB' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-4 py-2 rounded-lg ${
                    msg.sender === 'personB' 
                      ? 'bg-blue-600 text-white' 
                      : msg.type === 'warning'
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    <p className="text-sm">{msg.text}</p>
                    {msg.translated && (
                      <p className="text-xs opacity-75 mt-1 italic">Original: {msg.translated}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Input Area */}
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <button
                  onClick={sendPersonBMessage}
                  disabled={isTranslating}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-1"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Send</span>
                </button>
                <input
                  type="text"
                  value={personBInput}
                  onChange={(e) => setPersonBInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendPersonBMessage()}
                  placeholder={`Type in ${getLanguageDisplay(personBLang).split(' ')[1]}...`}
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isTranslating}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Legal Assistance Bar */}
        <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Scale className="w-5 h-5 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-amber-800">⚖️ Legal Assistance</h3>
              <p className="text-sm text-amber-700 mt-1">
                {legalInfo ? legalInfo.content : "Type a message to get legal help..."}
              </p>
            </div>
            {legalInfo?.type === 'warning' && (
              <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-4 bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">Instructions:</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Select languages for Person A and Person B using dropdowns</li>
            <li>• Type messages in your selected language</li>
            <li>• Messages are automatically translated to the other person's language</li>
            <li>• Legal warnings appear for risky terms (e.g., "6 months deposit")</li>
            <li>• Tech Stack: WindSurf IDE + Qdrant Vector Database</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
