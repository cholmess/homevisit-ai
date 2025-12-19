'use client';

import Vapi from '@vapi-ai/web';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type Risk = 'normal' | 'caution' | 'red flag';

type Citation = {
  id: string | number;
  score: number;
  title: string;
  category: string;
  key_rule: string;
  expat_implication: string;
  risk_level: Risk | string;
  source_document: string;
};

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

const LANGS = [
  { code: 'en', label: 'English', flagUrl: 'https://flagcdn.com/w40/gb.png' },
  { code: 'es', label: 'Español', flagUrl: 'https://flagcdn.com/w40/es.png' },
  { code: 'fr', label: 'Français', flagUrl: 'https://flagcdn.com/w40/fr.png' },
  { code: 'de', label: 'Deutsch', flagUrl: 'https://flagcdn.com/w40/de.png' }
] as const;

function riskBadgeClasses(risk: string) {
  if (risk === 'red flag') return 'bg-red-100 text-red-700';
  if (risk === 'caution') return 'bg-amber-100 text-amber-800';
  return 'bg-sky-100 text-sky-800';
}

export default function Page() {
  const [userLanguage, setUserLanguage] = useState<string | null>(null);
  const [landlordLanguage, setLandlordLanguage] = useState<string | null>(null);
  const [started, setStarted] = useState(false);

  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState('Tap the button to start speaking');
  const [transcript, setTranscript] = useState('');

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hello! I'm HomeVisit AI. I’ll help you communicate with the landlord and flag relevant tenant-law guidance."
    }
  ]);
  const [citations, setCitations] = useState<Citation[]>([]);

  const chatRef = useRef<HTMLDivElement | null>(null);
  const vapiRef = useRef<any>(null);
  const messagesRef = useRef<ChatMessage[]>(messages);

  const [textInput, setTextInput] = useState('');
  const [showLegalModal, setShowLegalModal] = useState(false);
  const [legalSearch, setLegalSearch] = useState('');
  const [legalResults, setLegalResults] = useState<Citation[]>([]);
  const [legalLoading, setLegalLoading] = useState(false);
  const [vapiReady, setVapiReady] = useState(true); // npm package is always ready

  // Keep ref in sync with state for use in closures
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const canStart = useMemo(() => Boolean(userLanguage && landlordLanguage), [userLanguage, landlordLanguage]);

  useEffect(() => {
    if (!chatRef.current) return;
    chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, citations]);

  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000', []);

  const initVapi = useCallback(() => {
    if (vapiRef.current) return true;
    const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;
    if (!publicKey) {
      setStatus('Missing NEXT_PUBLIC_VAPI_PUBLIC_KEY');
      return false;
    }

    vapiRef.current = new Vapi(publicKey);

    // Vapi event handlers
    vapiRef.current.on('call-start', () => {
      console.log('[Vapi] Call started');
      setStatus('Connected - speak now!');
    });

    vapiRef.current.on('call-end', () => {
      console.log('[Vapi] Call ended');
      setRecording(false);
      setStatus('Call ended');
    });

    vapiRef.current.on('speech-start', () => {
      console.log('[Vapi] Speech started');
      setTranscript('');
      setStatus('Listening...');
    });

    vapiRef.current.on('speech-end', () => {
      console.log('[Vapi] Speech ended');
      setStatus('Processing...');
    });

    vapiRef.current.on('message', (msg: any) => {
      console.log('[Vapi] Message:', msg);
      // Handle transcript messages
      if (msg.type === 'transcript') {
        if (msg.transcriptType === 'final') {
          setTranscript('');
          if (msg.transcript) {
            void onUserText(msg.transcript);
          }
        } else {
          setTranscript(msg.transcript || '');
        }
      }
      // Handle conversation updates
      if (msg.type === 'conversation-update') {
        const lastMsg = msg.conversation?.[msg.conversation.length - 1];
        if (lastMsg?.role === 'assistant' && lastMsg?.content) {
          setMessages((prev: ChatMessage[]) => [
            ...prev,
            { role: 'assistant', content: lastMsg.content }
          ]);
        }
      }
    });

    vapiRef.current.on('error', (e: any) => {
      console.error('[Vapi] Error:', e);
      setStatus(e?.message || 'Vapi error');
      setRecording(false);
    });

    return true;
  }, [apiBase]);

  // Initialize Vapi when SDK becomes ready
  useEffect(() => {
    if (vapiReady && started && !vapiRef.current) {
      initVapi();
    }
  }, [vapiReady, started, initVapi]);

  const onUserText = useCallback(
    async (text: string) => {
      const userMsg: ChatMessage = { role: 'user', content: text };
      const nextMessages = [...messagesRef.current, userMsg];
      setMessages(nextMessages);
      messagesRef.current = nextMessages;
      setStatus('Thinking...');

      try {
        const res = await fetch(`${apiBase}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: nextMessages,
            user_language: userLanguage,
            landlord_language: landlordLanguage,
            max_results: 4
          })
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail || `API error (${res.status})`);
        }

        const data = (await res.json()) as { answer: string; citations: Citation[] };
        setMessages((prev: ChatMessage[]) => [...prev, { role: 'assistant', content: data.answer }]);
        setCitations(data.citations || []);
        setStatus('Tap the button to speak again');

        if (vapiRef.current && data.answer) {
          try {
            await vapiRef.current.speak(data.answer);
          } catch {
          }
        }
      } catch (e: any) {
        setStatus(e?.message || 'Failed to contact API');
      }
    },
    [apiBase, landlordLanguage, userLanguage]
  );

  const startConversation = useCallback(() => {
    setStarted(true);
    initVapi();
    setStatus('Tap the button to start speaking');
    setMessages((prev: ChatMessage[]) => [
      ...prev,
      {
        role: 'assistant',
        content: `You're set! I’ll answer in your language and use tenant-law knowledge to help you during the viewing.`
      }
    ]);
  }, [initVapi]);

  const toggleRecording = useCallback(async () => {
    if (!initVapi()) {
      // SDK not ready yet, will retry when vapiReady changes
      return;
    }
    const vapi = vapiRef.current;
    if (!vapi) return;

    try {
      if (recording) {
        await vapi.stop();
        setRecording(false);
        setStatus('Tap the button to start speaking');
        return;
      }

      // Request microphone permission explicitly first
      setStatus('Requesting microphone access...');
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Stop the test stream immediately - Vapi will create its own
        stream.getTracks().forEach(track => track.stop());
        console.log('[Mic] Permission granted');
      } catch (micError: any) {
        console.error('[Mic] Permission denied:', micError);
        setStatus('Microphone access denied. Please allow microphone in browser settings.');
        return;
      }

      setStatus('Connecting to Vapi...');
      console.log('[Vapi] Starting call...');

      // Start Vapi with a minimal assistant for transcription
      await vapi.start({
        transcriber: {
          provider: 'deepgram',
          model: 'nova-2',
          language: userLanguage === 'en' ? 'en' : userLanguage === 'es' ? 'es' : userLanguage === 'fr' ? 'fr' : userLanguage === 'de' ? 'de' : 'en'
        },
        model: {
          provider: 'openai',
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: 'You are a helpful rental assistant. Listen to the user and respond briefly.'
            }
          ]
        },
        voice: {
          provider: 'playht',
          voiceId: 'jennifer'
        }
      });
      setRecording(true);
      setStatus('Listening...');
    } catch (e: any) {
      setStatus(e?.message || 'Microphone error');
      setRecording(false);
    }
  }, [initVapi, recording, userLanguage]);

  return (
    <>
      <main className="min-h-screen">
        <div className="mx-auto flex min-h-screen max-w-[640px] flex-col px-5 py-6">
          <header className="mb-6 border-b border-[var(--border)] pb-5 text-center">
            <h1 className="text-3xl font-semibold text-[var(--primary)]">HomeVisit AI</h1>
            <p className="mt-1 text-[var(--text-light)]">Your personal rental assistant</p>
          </header>

          {!started ? (
            <section className="flex-1 rounded-xl bg-[var(--card-bg)] p-6 shadow">
              <h2 className="text-xl font-semibold">Select Languages</h2>
              <p className="mt-1 text-[var(--text-light)]">Choose your language and the landlord&apos;s language</p>

              <div className="mt-6">
                <h3 className="text-sm font-semibold">I speak:</h3>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  {LANGS.map((l) => (
                    <button
                      key={l.code}
                      type="button"
                      onClick={() => setUserLanguage(l.code)}
                      className={
                        'flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition ' +
                        (userLanguage === l.code
                          ? 'border-[var(--primary)] bg-[var(--primary-light)]'
                          : 'border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--primary-light)]')
                      }
                    >
                      <img alt={l.label} src={l.flagUrl} className="h-[22px] w-[30px] rounded" />
                      <span className="font-medium">{l.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-6">
                <h3 className="text-sm font-semibold">Landlord speaks:</h3>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  {LANGS.map((l) => (
                    <button
                      key={l.code}
                      type="button"
                      onClick={() => setLandlordLanguage(l.code)}
                      className={
                        'flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition ' +
                        (landlordLanguage === l.code
                          ? 'border-[var(--primary)] bg-[var(--primary-light)]'
                          : 'border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--primary-light)]')
                      }
                    >
                      <img alt={l.label} src={l.flagUrl} className="h-[22px] w-[30px] rounded" />
                      <span className="font-medium">{l.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                disabled={!canStart}
                onClick={startConversation}
                className={
                  'mt-6 w-full rounded-lg px-4 py-3 font-semibold text-white transition ' +
                  (canStart ? 'bg-[var(--primary)] hover:opacity-95' : 'bg-[var(--primary)] opacity-60')
                }
              >
                Start Conversation
              </button>

              <div className="mt-3 text-center text-xs text-[var(--text-light)]">
                API: <span className="font-mono">{apiBase}</span>
              </div>
            </section>
          ) : (
            <section className="flex-1 rounded-xl bg-[var(--card-bg)] p-6 shadow">
              <div ref={chatRef} className="h-[420px] overflow-y-auto rounded-lg bg-[#F9FAFB] p-4">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={
                      'mb-4 max-w-[80%] rounded-xl px-4 py-2 text-sm ' +
                      (m.role === 'user'
                        ? 'ml-auto rounded-br-sm bg-[var(--primary)] text-white'
                        : 'mr-auto rounded-bl-sm bg-[#E5E7EB] text-[var(--text)]')
                    }
                  >
                    {m.content}
                  </div>
                ))}

                {citations.length ? (
                  <div className="mt-2 rounded-lg border border-[var(--border)] bg-white p-3">
                    <div className="text-xs font-semibold text-[var(--text-light)]">Relevant tenant-law knowledge</div>
                    <div className="mt-3 grid gap-3">
                      {citations.map((c) => (
                        <div key={String(c.id)} className="rounded-lg border border-[var(--border)] p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="text-sm font-semibold">{c.title}</div>
                            <span className={'shrink-0 rounded-full px-2 py-1 text-xs font-semibold ' + riskBadgeClasses(c.risk_level)}>
                              {c.risk_level}
                            </span>
                          </div>
                          <div className="mt-2 text-sm">
                            <span className="font-semibold">Rule:</span> {c.key_rule}
                          </div>
                          <div className="mt-2 text-xs text-[var(--text-light)]">{c.expat_implication}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mt-3 rounded-lg bg-[#F3F4F6] px-3 py-2 text-sm text-[var(--text-light)]">
                {status}
              </div>

              <div className={'mt-3 rounded-lg px-3 py-2 text-sm ' + (recording ? 'bg-blue-50 text-blue-800' : 'bg-[#F5F5F5] text-[var(--text-light)]')}>
                {transcript || (recording ? 'Listening…' : '')}
              </div>

              <button
                type="button"
                onClick={toggleRecording}
                className={
                  'mt-4 w-full rounded-lg px-4 py-3 font-semibold text-white transition ' +
                  (recording ? 'bg-red-600 hover:opacity-95' : 'bg-[var(--primary)] hover:opacity-95')
                }
              >
                {recording ? 'Stop' : 'Speak'}
              </button>

              <button
                type="button"
                onClick={() => setShowLegalModal(true)}
                className="mt-3 w-full rounded-lg border border-[var(--primary)] bg-white px-4 py-3 font-semibold text-[var(--primary)] transition hover:bg-[var(--primary-light)]"
              >
                ℹ️ Rental Law Help
              </button>

              {/* Text input fallback */}
              <form
                className="mt-4 flex gap-2"
                onSubmit={(e: React.FormEvent) => {
                  e.preventDefault();
                  if (textInput.trim()) {
                    void onUserText(textInput.trim());
                    setTextInput('');
                  }
                }}
              >
                <input
                  type="text"
                  value={textInput}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTextInput(e.target.value)}
                  placeholder="Or type your question here…"
                  className="flex-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm focus:border-[var(--primary)] focus:outline-none"
                />
                <button
                  type="submit"
                  className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-semibold text-white hover:opacity-95"
                >
                  Send
                </button>
              </form>
            </section>
          )}
        </div>
      </main>

      {/* Legal Help Modal */}
      {showLegalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Rental Law Help</h2>
              <button
                type="button"
                onClick={() => setShowLegalModal(false)}
                className="text-2xl text-[var(--text-light)] hover:text-[var(--text)]"
              >
                &times;
              </button>
            </div>

            <form
              className="flex gap-2"
              onSubmit={async (e: React.FormEvent) => {
                e.preventDefault();
                if (!legalSearch.trim()) return;
                setLegalLoading(true);
                try {
                  const res = await fetch(`${apiBase}/search`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: legalSearch, limit: 5 })
                  });
                  if (res.ok) {
                    const data = (await res.json()) as { results: Citation[] };
                    setLegalResults(data.results || []);
                  }
                } catch {
                  // ignore
                } finally {
                  setLegalLoading(false);
                }
              }}
            >
              <input
                type="text"
                value={legalSearch}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLegalSearch(e.target.value)}
                placeholder="Search rental laws (e.g., deposit, notice)…"
                className="flex-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm focus:border-[var(--primary)] focus:outline-none"
              />
              <button
                type="submit"
                disabled={legalLoading}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-semibold text-white hover:opacity-95 disabled:opacity-60"
              >
                {legalLoading ? '…' : 'Search'}
              </button>
            </form>

            {legalResults.length > 0 && (
              <div className="mt-4 grid gap-3">
                {legalResults.map((c: Citation) => (
                  <div key={String(c.id)} className="rounded-lg border border-[var(--border)] p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-semibold">{c.title}</div>
                      <span className={'shrink-0 rounded-full px-2 py-1 text-xs font-semibold ' + riskBadgeClasses(c.risk_level)}>
                        {c.risk_level}
                      </span>
                    </div>
                    <div className="mt-2 text-sm">
                      <span className="font-semibold">Rule:</span> {c.key_rule}
                    </div>
                    <div className="mt-2 text-xs text-[var(--text-light)]">{c.expat_implication}</div>
                  </div>
                ))}
              </div>
            )}

            {legalResults.length === 0 && !legalLoading && (
              <p className="mt-4 text-center text-sm text-[var(--text-light)]">
                Search for topics like &quot;deposit&quot;, &quot;notice period&quot;, &quot;contract&quot;, etc.
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
