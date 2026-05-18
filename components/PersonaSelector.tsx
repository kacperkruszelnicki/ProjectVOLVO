'use client';

import { Persona } from '@/lib/types';

interface Props {
  current: Persona;
  onChange: (p: Persona) => void;
}

const personas = [
  { id: 'business' as Persona, label: 'Business User', icon: '👔', desc: 'Uproszczone odpowiedzi' },
  { id: 'engineer' as Persona, label: 'Data Engineer', icon: '⚙️', desc: 'Techniczne szczegóły' },
  { id: 'architect' as Persona, label: 'Architect',    icon: '🏗️', desc: 'Kontekst systemowy' },
];

export default function PersonaSelector({ current, onChange }: Props) {
  return (
    <div className="p-3 border-b border-slate-200">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-1">
        Persona
      </p>
      <div className="flex flex-col gap-1">
        {personas.map((p) => (
          <button
            key={p.id}
            onClick={() => onChange(p.id)}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all text-sm
              ${current === p.id
                ? 'bg-blue-50 text-blue-800 font-medium'
                : 'text-slate-600 hover:bg-slate-100'}`}
          >
            <span className="text-base">{p.icon}</span>
            <div>
              <div className="font-medium leading-tight">{p.label}</div>
              <div className="text-xs text-slate-400">{p.desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}