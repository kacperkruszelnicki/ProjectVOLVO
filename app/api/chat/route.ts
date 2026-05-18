import { NextRequest, NextResponse } from 'next/server';

// Mock odpowiedzi — do podmiany na fetch do backendu RAG
const mockAnswer = {
  content: 'To jest przykładowa odpowiedź z systemu RAG. Backend architekta zwróci tutaj prawdziwą odpowiedź opartą na dokumentacji Confluence.',
  sources: [
    { title: 'ETL Architecture v3.2 · Confluence', url: '#' },
    { title: 'Data Platform Overview · Confluence', url: '#' },
  ],
  confidence: 92,
};

export async function POST(req: NextRequest) {
  const { question, persona } = await req.json();

  // TODO: podmień na prawdziwy backend RAG
  // const response = await fetch('http://localhost:8000/query', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ question, persona }),
  // });
  // const data = await response.json();

  // Symulacja opóźnienia
  await new Promise((r) => setTimeout(r, 1000));

  return NextResponse.json(mockAnswer);
}