import { useState } from 'react';
import { Send, Loader } from 'lucide-react';
import { useChat } from '../hooks';

const Tutor = () => {
  const { messages, loading, sendMessage } = useChat('Av');
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    await sendMessage(input);
    setInput('');
  };

  return (
    <section className="grid gap-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft flex flex-col h-[600px]">
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs rounded-3xl px-5 py-3 ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-400 to-violet-500 text-slate-950 font-semibold'
                      : 'bg-slate-900/90 border border-slate-700/60 text-slate-100'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-3xl bg-slate-900/90 px-5 py-3 flex items-center gap-2 text-slate-400">
                  <Loader className="h-4 w-4 animate-spin" />
                  Thinking...
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question..."
              className="flex-1 rounded-3xl border border-slate-700/60 bg-slate-900/90 px-5 py-3 text-slate-100 outline-none transition focus:border-cyan-400"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="rounded-3xl bg-gradient-to-r from-cyan-400 to-violet-500 p-3 text-slate-950 transition hover:brightness-110 disabled:opacity-50"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {[
            { title: 'Hint mode', text: 'Step-by-step guidance' },
            { title: 'Voice input', text: 'Speak your question' },
            { title: 'Image upload', text: 'Share homework photos' },
          ].map((card) => (
            <div key={card.title} className="rounded-3xl border border-slate-700/60 bg-slate-950/90 p-4 shadow-soft">
              <h3 className="font-semibold text-white text-sm">{card.title}</h3>
              <p className="mt-1 text-xs text-slate-400">{card.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Tutor;
