export default function TypingIndicator() {
  return (
    <div className="flex gap-1 items-center px-5 py-4 w-fit bg-white border border-slate-200 rounded-2xl rounded-tl-sm shadow-sm mb-4">
      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  );
}