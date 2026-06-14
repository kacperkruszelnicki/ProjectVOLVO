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
        content: 'Server error. Try again.',
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
      
      {/* PASEK BOCZNY */}
      <aside 
        className={`${isSidebarOpen ? 'border-r border-slate-200' : 'w-0 border-r-0'} bg-white flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20 overflow-hidden relative shadow-sm`}
        style={{ width: isSidebarOpen ? '340px' : '0px' }}
      >
        <div className="h-full flex flex-col flex-shrink-0" style={{ width: '340px' }}>
          
          
          <div className="border-b border-slate-200 flex items-center justify-between bg-white" style={{ padding: '24px 20px' }}>
            <div className="flex items-center gap-4">
              <div className="rounded-full border-[3px] border-blue-900 flex items-center justify-center text-[15px] font-bold text-blue-900 shadow-sm" style={{ width: '44px', height: '44px' }}>
                V
              </div>
              <div>
                <div className="text-[17px] font-extrabold text-slate-800 tracking-tight">Volvo</div>
                <div className="text-[12px] font-medium text-slate-400">Knowledge Assistant</div>
              </div>
            </div>
            <button onClick={() => setIsSidebarOpen(false)} className="text-slate-400 hover:text-slate-700 bg-slate-50 rounded-full hover:bg-slate-100 transition-colors" style={{ padding: '8px' }}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
            </button>
          </div>

          <div style={{ padding: '20px 20px 8px 20px' }}>
            <PersonaSelector current={persona} onChange={setPersona} />
          </div>

          <div className="overflow-y-auto flex-1 custom-scrollbar bg-white" style={{ padding: '20px 20px' }}>
            <p className="text-[12px] font-extrabold uppercase tracking-widest text-slate-400" style={{ marginBottom: '24px' }}>Analiza Kontekstu</p>
            
            {currentSources.length === 0 && currentRejected.length === 0 && (
              <p className="text-[13px] text-slate-400 italic">No documents. Ask question.</p>
            )}

            {currentSources.length > 0 && (
              <div style={{ marginBottom: '40px' }}>
                <span className="text-[11px] font-bold uppercase tracking-wider text-green-600 flex items-center gap-2" style={{ marginBottom: '16px' }}>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"/> Used as a source.
                </span>
                
                <div className="flex flex-col" style={{ gap: '16px' }}>
                  {currentSources.map((s, idx) => (
                    <div key={`src-${idx}`} className="border border-slate-200 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
                      <button 
                        onClick={() => setExpandedDoc(expandedDoc === `src-${idx}` ? null : `src-${idx}`)}
                        className="w-full text-left flex items-center justify-between hover:bg-slate-50 transition-colors min-w-0"
                        style={{ padding: '14px 16px' }}
                      >
                        <span className="text-[13px] font-semibold text-slate-700 truncate pr-3 flex-1 min-w-0">
                          {formatFilename(s.title)}
                        </span>
                        <span className="text-slate-400 text-xs flex-shrink-0">{expandedDoc === `src-${idx}` ? '▼' : '▶'}</span>
                      </button>
                      
                      {expandedDoc === `src-${idx}` && (
                        <div className="bg-slate-50/50 border-t border-slate-100 flex flex-col" style={{ padding: '8px 16px 16px 16px', gap: '12px' }}>
                          <div className="flex flex-wrap gap-2" style={{ marginTop: '4px' }}>
                            <span className="bg-green-100 text-green-700 rounded-md text-[10px] font-bold uppercase tracking-wider border border-green-200" style={{ padding: '4px 8px' }}>✔ Accepted</span>
                          </div>
                          <div className="bg-white rounded-md border border-slate-200 text-slate-500 text-[12px] leading-relaxed break-all font-mono shadow-inner" style={{ padding: '14px' }}>
                            <span className="font-bold text-slate-400 uppercase text-[9px] block tracking-wider" style={{ marginBottom: '8px' }}>Full length path:</span>
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
                <span className="text-[11px] font-bold uppercase tracking-wider text-red-500 flex items-center gap-2" style={{ marginBottom: '16px' }}>
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400"/> Rejected by RAG
                </span>
                <div className="flex flex-col" style={{ gap: '16px' }}>
                  {currentRejected.map((r, idx) => (
                    <div key={`rej-${idx}`} className="border border-red-100 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
                      <button 
                        onClick={() => setExpandedDoc(expandedDoc === `rej-${idx}` ? null : `rej-${idx}`)}
                        className="w-full text-left flex items-center justify-between hover:bg-red-50/30 transition-colors min-w-0"
                        style={{ padding: '14px 16px' }}
                      >
                        <span className="text-[13px] font-semibold text-slate-600 truncate pr-3 flex-1 min-w-0">
                          {formatFilename(r.rejected_doc)}
                        </span>
                        <span className="text-red-300 text-xs flex-shrink-0">{expandedDoc === `rej-${idx}` ? '▼' : '▶'}</span>
                      </button>
                      
                      {expandedDoc === `rej-${idx}` && (
                        <div className="bg-red-50/30 border-t border-red-100 flex flex-col" style={{ padding: '8px 16px 16px 16px', gap: '12px' }}>
                          <div className="flex flex-wrap gap-2" style={{ marginTop: '4px' }}>
                            <span className="bg-red-100 text-red-700 rounded-md text-[10px] font-bold uppercase tracking-wider border border-red-200" style={{ padding: '4px 8px' }}>✖ Rejected</span>
                            <span className="bg-white text-slate-600 rounded-md text-[10px] font-bold tracking-wider border border-slate-200 shadow-sm" style={{ padding: '4px 8px' }}>
                              Wynik: {r.rejected_score.toFixed(3)}
                            </span>
                          </div>
                          <div className="bg-white rounded-md border border-red-100 text-slate-500 text-[12px] leading-relaxed break-all font-mono shadow-inner" style={{ padding: '14px' }}>
                            <span className="font-bold text-slate-400 uppercase text-[9px] block tracking-wider" style={{ marginBottom: '8px' }}>Full length path:</span>
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

      {/* --- GŁÓWNA SEKCJA CZATU --- */}
      <main className="flex-1 flex flex-col min-w-0 bg-white relative">
        
        {!isSidebarOpen && (
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="absolute z-10 bg-white rounded-xl shadow-md border border-slate-200 text-slate-500 hover:text-blue-600 transition-colors"
            style={{ top: '24px', left: '24px', padding: '12px' }}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
          </button>
        )}
      
        <div className="flex-1 overflow-y-auto flex flex-col items-center messages-container" style={{ padding: '40px 32px' }}>
          <div className="w-full max-w-3xl flex flex-col min-w-0" style={{ gap: '24px', paddingBottom: '24px' }}>
            
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center text-center" style={{ height: '65vh', gap: '24px' }}>
                <div className="bg-blue-900 flex items-center justify-center text-5xl shadow-xl ring-8 ring-blue-900/5" style={{ width: '96px', height: '96px', borderRadius: '32px' }}>🤖</div>
                <div>
                  <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight" style={{ marginBottom: '16px' }}>Volvo Knowledge Assistant</h2>
                  <p className="text-[16px] text-slate-500 max-w-lg mx-auto leading-relaxed">
                    Ask a question and I will analyze the available documentation to provide you with a precise answer.
                  </p>
                </div>
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} style={{ height: '24px' }} />
          </div>
        </div>

        <div className="bg-gradient-to-t from-white via-white to-white/0 flex justify-center" style={{ padding: '24px 24px 32px 24px' }}>
          <div className="w-full max-w-3xl flex flex-col">
            
            <div className="flex items-end bg-slate-50 border border-slate-300 shadow-sm rounded-3xl focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all" 
                 style={{ padding: '10px 10px 10px 20px', gap: '16px' }}>
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Zadaj pytanie..."
                rows={1}
                
                className="flex-1 bg-transparent resize-none outline-none text-[15px] text-slate-800 placeholder-slate-400 custom-scrollbar"
                style={{ wordBreak: 'break-word', padding: '10px 0px 10px 4px', maxHeight: '180px' }}
              />
              
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="bg-blue-900 hover:bg-blue-800 disabled:bg-slate-300 rounded-full flex items-center justify-center transition-transform hover:scale-105 active:scale-95 disabled:scale-100 flex-shrink-0 shadow-sm"
                style={{ width: '40px', height: '40px', marginBottom: '4px' }}
              >
                <svg className="w-4 h-4 fill-white" style={{ transform: 'translateX(1px)' }} viewBox="0 0 24 24">
                  <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
                </svg>
              </button>

            </div>

            <p className="text-[13px] font-medium text-slate-400 text-center" style={{ marginTop: '16px' }}>
              Chosen role: <span className="font-bold text-slate-600">{persona === 'business' ? 'Business User' : persona === 'engineer' ? 'Data Engineer' : 'Architect'}</span> · Enter to send · Shift+Enter new line
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}