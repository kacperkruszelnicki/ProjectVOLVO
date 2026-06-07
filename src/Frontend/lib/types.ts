export type Persona = 'business' | 'engineer' | 'architect';

export interface Source {
  title: string;
  url: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  confidence?: number;
  timestamp: Date;
}