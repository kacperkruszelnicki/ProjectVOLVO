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
      <aside className="w-56 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
        <div className="px-4 py-4 border-b border-slate-200 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-blue-900 flex items-center justify-center text-xs font-bold text-blue-900">
            V
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">Volvo</div>
            <div className="text-xs text-slate-400">Knowledge Assistant</div>
          </div>
        </div>

        <PersonaSelector current={persona} onChange={setPersona} />

        <div className="p-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1">
            Źródła danych
          </p>
          {['Confluence', 'Stack Overflow', 'Architecture Docs'].map((s) => (
            <div key={s} className="flex items-center gap-2 px-2 py-1.5 text-xs text-slate-500">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              {s}
            </div>
          ))}
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5 messages-container">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="w-14 h-14 bg-blue-900 rounded-2xl flex items-center justify-center text-2xl">
                🤖
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-700 mb-1">
                  Volvo Knowledge Assistant
                </h2>
                <p className="text-sm text-slate-400 max-w-sm">
                  Odpowiadam wyłącznie na podstawie dokumentacji wewnętrznej Volvo.
                  Każda odpowiedź zawiera źródła i poziom pewności.
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

        <div className="p-4 bg-white border-t border-slate-200">
          <div className="flex gap-3 items-end bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 focus-within:border-blue-400 focus-within:bg-white transition-all">
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
              className="w-9 h-9 bg-blue-900 hover:bg-blue-700 disabled:bg-slate-300 rounded-full flex items-center justify-center transition-colors flex-shrink-0"
            >
              <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
              </svg>
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">
            Persona: <span className="font-medium text-slate-500">
              {persona === 'business' ? 'Business User' : persona === 'engineer' ? 'Data Engineer' : 'Architect'}
            </span> · Enter aby wysłać, Shift+Enter nowa linia
          </p>
        </div>
      </main>
    </div>
  );
}