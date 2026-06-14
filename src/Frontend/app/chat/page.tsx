'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Persona } from '@/lib/types';
import PersonaSelector from '@/components/PersonaSelector';
import MessageBubble from '@/components/MessageBubble';
import TypingIndicator from '@/components/TypingIndicator';

const formatFilename = (fullString: string) => {
  if (!fullString) return 'Nieznany plik';
  const pathPart = fullString.split('|')[0].trim(); 
  const segments = pathPart.split(/[\/\\]/);
  return segments[segments.length - 1];
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [persona, setPersona] = useState<Persona>('engineer');
  const [isLoading, setIsLoading] = useState(false);
  
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const [currentSources, setCurrentSources] = useState<{title: string, score?: number, url?: string}[]>([]);
  const [currentRejected, setCurrentRejected] = useState<{rejected_doc: string, rejected_score: number}[]>([]);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

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
    setExpandedDoc(null);
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage.content, persona }),
      });

      const data = await res.json();

      setCurrentSources(data.sources || []);
      setCurrentRejected(data.rejected || []);

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
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden text-slate-800">
      
      {/* Poszerzono lekko pasek boczny (w-[340px]), aby zrobić miejsce na ogromne marginesy */}
      <aside 
        className={`${isSidebarOpen ? 'w-[340px] border-r border-slate-200' : 'w-0 border-r-0'} bg-white flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20 overflow-hidden relative shadow-sm`}
      >
        <div className="w-[340px] h-full flex flex-col flex-shrink-0">
          
          {/* POTĘŻNE ODSUNIĘCIE LOGO OD LEWEJ KRAWĘDZI (px-8) */}
          <div className="px-8 py-6 border-b border-slate-200 flex items-center justify-between bg-white">
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-full border-[3px] border-blue-900 flex items-center justify-center text-[15px] font-bold text-blue-900 shadow-sm">
                V
              </div>
              <div>
                <div className="text-[17px] font-extrabold text-slate-800 tracking-tight">Volvo</div>
                <div className="text-[12px] font-medium text-slate-400">Knowledge Assistant</div>
              </div>
            </div>
            <button onClick={() => setIsSidebarOpen(false)} className="text-slate-400 hover:text-slate-700 p-2 bg-slate-50 rounded-full hover:bg-slate-100 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
            </button>
          </div>

          {/* ODSUNIĘCIE WYBORU PERSONY OD LEWEJ KRAWĘDZI (px-8) */}
          <div className="px-8 pt-6 pb-2">
            <PersonaSelector current={persona} onChange={setPersona} />
          </div>

          {/* ODSUNIĘCIE ANALIZY KONTEKSTU OD LEWEJ KRAWĘDZI (px-8) */}
          <div className="px-8 py-6 overflow-y-auto flex-1 custom-scrollbar bg-white">
            <p className="text-[12px] font-extrabold uppercase tracking-widest text-slate-400 mb-6">Analiza Kontekstu</p>
            
            {currentSources.length === 0 && currentRejected.length === 0 && (
              <p className="text-[13px] text-slate-400 italic">Brak dokumentów. Zadaj pytanie.</p>
            )}

            {currentSources.length > 0 && (
              <div className="mb-10">
                <span className="text-[11px] font-bold uppercase tracking-wider text-green-600 mb-4 flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"/> Użyte jako źródło
                </span>
                <div className="flex flex-col gap-3">
                  {currentSources.map((s, idx) => (
                    <div key={`src-${idx}`} className="border border-slate-200 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
                      <button 
                        onClick={() => setExpandedDoc(expandedDoc === `src-${idx}` ? null : `src-${idx}`)}
                        className="w-full text-left px-4 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors min-w-0"
                      >
                        <span className="text-[13px] font-semibold text-slate-700 truncate pr-3 flex-1 min-w-0">
                          {formatFilename(s.title)}
                        </span>
                        <span className="text-slate-400 text-xs flex-shrink-0">{expandedDoc === `src-${idx}` ? '▼' : '▶'}</span>
                      </button>
                      
                      {expandedDoc === `src-${idx}` && (
                        <div className="px-4 pb-4 pt-2 bg-slate-50/50 border-t border-slate-100 flex flex-col gap-3">
                          <div className="flex flex-wrap gap-2 mt-1">
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded-md text-[10px] font-bold uppercase tracking-wider border border-green-200">✔ Zaakceptowano</span>
                          </div>
                          <div className="bg-white p-3 rounded-md border border-slate-200 text-slate-500 text-[11px] break-all font-mono shadow-inner">
                            <span className="font-bold text-slate-400 uppercase text-[9px] block mb-1.5 tracking-wider">Pełna ścieżka pliku:</span>
                            {s.title}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {currentRejected.length > 0 && (
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-red-500 mb-4 flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400"/> Odrzucone przez RAG
                </span>
                <div className="flex flex-col gap-3">
                  {currentRejected.map((r, idx) => (
                    <div key={`rej-${idx}`} className="border border-red-100 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
                      <button 
                        onClick={() => setExpandedDoc(expandedDoc === `rej-${idx}` ? null : `rej-${idx}`)}
                        className="w-full text-left px-4 py-3.5 flex items-center justify-between hover:bg-red-50/30 transition-colors min-w-0"
                      >
                        <span className="text-[13px] font-semibold text-slate-600 truncate pr-3 flex-1 min-w-0">
                          {formatFilename(r.rejected_doc)}
                        </span>
                        <span className="text-red-300 text-xs flex-shrink-0">{expandedDoc === `rej-${idx}` ? '▼' : '▶'}</span>
                      </button>
                      
                      {expandedDoc === `rej-${idx}` && (
                        <div className="px-4 pb-4 pt-2 bg-red-50/30 border-t border-red-100 flex flex-col gap-3">
                          <div className="flex flex-wrap gap-2 mt-1">
                            <span className="px-2 py-1 bg-red-100 text-red-700 rounded-md text-[10px] font-bold uppercase tracking-wider border border-red-200">✖ Odrzucono</span>
                            <span className="px-2 py-1 bg-white text-slate-600 rounded-md text-[10px] font-bold tracking-wider border border-slate-200 shadow-sm">
                              Wynik: {r.rejected_score.toFixed(3)}
                            </span>
                          </div>
                          <div className="bg-white p-3 rounded-md border border-red-100 text-slate-500 text-[11px] break-all font-mono shadow-inner">
                            <span className="font-bold text-slate-400 uppercase text-[9px] block mb-1.5 tracking-wider">Pełna ścieżka pliku:</span>
                            {r.rejected_doc}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0 bg-white relative">
        
        {!isSidebarOpen && (
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="absolute top-6 left-6 z-10 p-3 bg-white rounded-xl shadow-md border border-slate-200 text-slate-500 hover:text-blue-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
          </button>
        )}

        <div className="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col items-center messages-container">
          <div className="w-full max-w-3xl flex flex-col gap-6 pb-6 min-w-0">
            
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-[65vh] text-center gap-6">
                <div className="w-24 h-24 bg-blue-900 rounded-[2rem] flex items-center justify-center text-5xl shadow-xl ring-8 ring-blue-900/5">🤖</div>
                <div>
                  <h2 className="text-3xl font-extrabold text-slate-800 mb-4 tracking-tight">Volvo Knowledge Assistant</h2>
                  <p className="text-[16px] text-slate-500 max-w-lg mx-auto leading-relaxed">
                    Zadaj pytanie, a przeanalizuję dostępną dokumentację, aby dostarczyć Ci precyzyjną odpowiedź.
                  </p>
                </div>
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} className="h-6" />
          </div>
        </div>

        <div className="px-6 py-6 bg-gradient-to-t from-white via-white to-white/0 flex justify-center pb-8">
          <div className="w-full max-w-3xl flex flex-col">
            
            <div className="flex gap-4 items-end bg-slate-50 border border-slate-300 shadow-sm rounded-3xl pl-6 pr-2.5 py-2 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all">
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Zadaj pytanie dotyczące dokumentacji Volvo..."
                rows={1}
                className="flex-1 bg-transparent resize-none outline-none text-[15px] text-slate-800 placeholder-slate-400 max-h-[180px] overflow-y-auto py-2.5 custom-scrollbar"
                style={{ wordBreak: 'break-word' }}
              />
              
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="w-10 h-10 mb-1 bg-blue-900 hover:bg-blue-800 disabled:bg-slate-300 rounded-full flex items-center justify-center transition-transform hover:scale-105 active:scale-95 disabled:scale-100 flex-shrink-0 shadow-sm"
              >
                <svg className="w-4 h-4 fill-white translate-x-[1px]" viewBox="0 0 24 24">
                  <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
                </svg>
              </button>

            </div>

            <p className="text-[13px] font-medium text-slate-400 mt-4 text-center">
              Wybrana rola: <span className="font-bold text-slate-600">{persona === 'business' ? 'Business User' : persona === 'engineer' ? 'Data Engineer' : 'Architect'}</span> · Enter aby wysłać · Shift+Enter nowa linia
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}