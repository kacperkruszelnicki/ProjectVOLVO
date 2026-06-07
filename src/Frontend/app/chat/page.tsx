'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Persona } from '@/lib/types';
import PersonaSelector from '@/components/PersonaSelector';
import MessageBubble from '@/components/MessageBubble';
import TypingIndicator from '@/components/TypingIndicator';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [persona, setPersona] = useState<Persona>('engineer');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const [currentSources, setCurrentSources] = useState<{title: string, url: string}[]>([]);
  const [currentRejected, setCurrentRejected] = useState<{rejected_doc: string, rejected_score: number}[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>('');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  async function sendMessage() {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage.content, persona }),
      });

      const data = await res.json();

      setCurrentSources(data.sources || []);
      setCurrentRejected(data.rejected || []);
      setCurrentStatus(data.status || '');

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.content,
        sources: data.sources,
        confidence: data.confidence,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Błąd połączenia z serwerem. Spróbuj ponownie.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex h-screen bg-slate-100">
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="px-4 py-4 border-b border-slate-200 flex items-center gap-3 bg-slate-50">
          <div className="w-8 h-8 rounded-full border-2 border-blue-900 flex items-center justify-center text-xs font-bold text-blue-900 bg-white">
            V
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">Volvo</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Knowledge RAG</div>
          </div>
        </div>

        <PersonaSelector current={persona} onChange={setPersona} />

        {/* --- DYNAMICZNY PANEL DANYCH Z BACKENDU --- */}
        <div className="p-3 overflow-y-auto flex-1 custom-scrollbar">
          
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 px-1">
            Użyte dokumenty (FAISS)
          </p>
          {currentSources.length === 0 && (
            <div className="text-xs text-slate-400 px-2 italic">Brak danych. Zadaj pytanie.</div>
          )}
          <div className="flex flex-col gap-2">
            {currentSources.map((s, idx) => (
              <div key={idx} className="flex items-start gap-2 px-2 text-xs text-slate-600 bg-green-50/50 p-2 rounded border border-green-100">
                <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0 mt-0.5 shadow-sm" />
                <span className="break-words leading-tight">{s.title}</span>
              </div>
            ))}
          </div>

          {currentRejected.length > 0 && (
            <>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mt-6 mb-3 px-1 border-t border-slate-200 pt-4">
                Odrzucone z powodu wyniku
              </p>
              <div className="flex flex-col gap-2">
                {currentRejected.map((r, idx) => (
                  <div key={idx} className="flex flex-col gap-1 px-2 text-xs text-slate-500 bg-red-50/50 p-2 rounded border border-red-100">
                    <div className="flex items-start gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-400 flex-shrink-0 mt-0.5 shadow-sm" />
                      <span className="break-words leading-tight">{r.rejected_doc}</span>
                    </div>
                    <span className="pl-4 text-[10px] font-mono text-red-500 font-semibold">
                      Wynik: {r.rejected_score.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}

          {currentStatus && (
            <div className="mt-6 border-t border-slate-200 pt-4 px-1">
              <p className="text-[10px] uppercase font-bold text-slate-400 mb-1">Status RAG</p>
              <div className="bg-slate-800 text-green-400 p-2 rounded-md text-[10px] font-mono shadow-inner break-words">
                {'>'} {currentStatus}
              </div>
            </div>
          )}

        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5 messages-container">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="w-14 h-14 bg-blue-900 rounded-2xl flex items-center justify-center text-2xl shadow-lg">
                🤖
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-700 mb-1">
                  Volvo Knowledge Assistant
                </h2>
                <p className="text-sm text-slate-400 max-w-sm">
                  Odpowiadam na podstawie dokumentacji RAG. Zobacz panel po lewej, aby śledzić metadane i punktację dokumentów.
                </p>
              </div>
            </div>
          )}

          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}

          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <div className="p-4 bg-white border-t border-slate-200 shadow-sm z-10">
          <div className="flex gap-3 items-end bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 focus-within:border-blue-400 focus-within:bg-white focus-within:shadow-sm transition-all">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Zadaj pytanie dotyczące dokumentacji Volvo..."
              rows={1}
              className="flex-1 bg-transparent resize-none outline-none text-sm text-slate-800 placeholder-slate-400 leading-relaxed max-h-32"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="w-9 h-9 bg-blue-900 hover:bg-blue-700 disabled:bg-slate-300 rounded-full flex items-center justify-center transition-colors flex-shrink-0 shadow-sm"
            >
              <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
              </svg>
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">
            Wybrana Persona: <span className="font-bold text-slate-600 uppercase tracking-wide">
              {persona}
            </span> · Enter aby wysłać, Shift+Enter nowa linia
          </p>
        </div>
      </main>
    </div>
  );
}