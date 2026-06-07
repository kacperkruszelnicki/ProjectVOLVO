import { NextRequest, NextResponse } from 'next/server';

// Mock odpowiedzi — do podmiany na fetch do backendu RAG
/*const mockAnswer = {
  content: 'To jest przykładowa odpowiedź z systemu RAG. Backend architekta zwróci tutaj prawdziwą odpowiedź opartą na dokumentacji Confluence.',
  sources: [
    { title: 'ETL Architecture v3.2 · Confluence', url: '#' },
    { title: 'Data Platform Overview · Confluence', url: '#' },
  ],
  confidence: 92,
};*/

export async function POST(req: NextRequest) {
  const { question, persona } = await req.json();

  try{
    const response = await fetch('http://127.0.0.1:5000/ask', {
      method: 'POST',
      headers:{'Content-Type': 'application/json'},
      body: JSON.stringify({ question: question, profile: persona}),
    }); 

    if (!response.ok){
      throw new Error('Bład API: ${response.status}');
    }

    const data = await response.json();

    const formattedSources = data.sources ? data.sources.map((src: string) => ({
      title: src,
      url: '#'
    })) : [];

    return NextResponse.json({
      content: data.answer,
      sources: formattedSources,
      confidence: 100,
      status: data.status,
      rejected: data.rejected
    });
  } catch (error){
    console.error("Błąd zapytania do Pythona:", error);
    return NextResponse.json(
      { content: "Wystąpił błąd przy łączeniu z Pythonem. Upewnij się, że backend_faiss.py działa na porcie 5000." },
      { status: 500 }
    );
  }

  // Symulacja opóźnienia
  /*
  await new Promise((r) => setTimeout(r, 1000));

  return NextResponse.json(mockAnswer);
  */
}