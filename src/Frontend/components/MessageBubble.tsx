'use client';

import { Message } from '@/lib/types';
import ReactMarkdown from 'react-markdown';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  // --- WIDOK UŻYTKOWNIKA ---
  if (isUser) {
    return (
      <div className="flex justify-end w-full mb-4">
        {/* whitespace-pre-wrap pozwala zachować entery, które wpisujesz w okienku */}
        <div className="bg-blue-900 text-white px-5 py-3 rounded-2xl rounded-tr-sm max-w-[80%] text-sm shadow-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  // --- WIDOK SYSTEMU AI ---
  return (
    <div className="flex flex-col gap-2 w-full max-w-[85%] mb-4">
      {/* Tutaj użyliśmy react-markdown oraz specjalnych klas Tailwind:
        [&_ul]:list-disc - przywraca kropki w listach
        [&_ol]:list-decimal - przywraca cyfry w listach
        [&_strong]:font-bold - przywraca pogrubienia
        [&_p]:mb-3 - dodaje odstępy między akapitami
      */}
      <div className="bg-white border border-slate-200 text-slate-800 px-5 py-4 rounded-2xl rounded-tl-sm text-sm shadow-sm leading-relaxed 
                      [&_ul]:list-disc [&_ul]:ml-5 [&_ul]:mb-3 
                      [&_ol]:list-decimal [&_ol]:ml-5 [&_ol]:mb-3 
                      [&_li]:mb-1 [&_strong]:font-semibold [&_p]:mb-3 last:[&_p]:mb-0">
        <ReactMarkdown>
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}