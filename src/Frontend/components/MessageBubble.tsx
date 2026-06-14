'use client';

import { Message } from '@/lib/types';
import ReactMarkdown from 'react-markdown';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end w-full mb-6">
        {/* Magiczne wordBreak: 'break-word' sprawia, że tekst łamie się w naturalnych miejscach, ale ratuje ramkę przed wylaniem */}
        <div className="bg-blue-900 text-white px-6 py-4 rounded-[24px] rounded-tr-sm max-w-[85%] md:max-w-[75%] text-[15px] shadow-sm whitespace-pre-wrap leading-relaxed" style={{ wordBreak: 'break-word' }}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 w-full max-w-[95%] md:max-w-[85%] mb-6">
      <div className="bg-white border border-slate-200 text-slate-800 px-7 py-6 rounded-[24px] rounded-tl-sm text-[15px] shadow-sm leading-relaxed 
                      [&_ul]:list-disc [&_ul]:ml-6 [&_ul]:mb-4 
                      [&_ol]:list-decimal [&_ol]:ml-6 [&_ol]:mb-4 
                      [&_li]:mb-2 [&_strong]:font-bold [&_strong]:text-slate-900 [&_p]:mb-4 last:[&_p]:mb-0" 
           style={{ wordBreak: 'break-word' }}>
        <ReactMarkdown>
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}