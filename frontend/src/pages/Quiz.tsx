import { useState } from 'react';
import { useQuiz } from '../hooks';
import { Loader } from 'lucide-react';

const Quiz = () => {
  const { quiz, loading, error, generateQuiz: generateQuizRequest, reset } = useQuiz();
  const [topic, setTopic] = useState('');
  const [grade, setGrade] = useState(11);
  const [numQuestions, setNumQuestions] = useState(5);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    await generateQuizRequest(topic, grade, numQuestions);
  };

  return (
    <section className="space-y-6">
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Adaptive quiz</p>
            <h2 className="mt-2 text-2xl font-semibold">Generate a rapid practice set</h2>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            className="rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Loader className="h-4 w-4 animate-spin" />}
            {loading ? 'Generating...' : 'Create quiz'}
          </button>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
            <label className="text-sm text-slate-400">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="mt-3 w-full rounded-3xl border border-slate-700 bg-slate-950/90 p-4 text-white outline-none focus:border-cyan-400"
              placeholder="e.g., Photosynthesis"
            />
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
            <label className="text-sm text-slate-400">Grade</label>
            <select
              value={grade}
              onChange={(e) => setGrade(parseInt(e.target.value))}
              className="mt-3 w-full rounded-3xl border border-slate-700 bg-slate-950/90 p-4 text-white outline-none focus:border-cyan-400"
            >
              {Array.from({ length: 7 }, (_, i) => i + 6).map((g) => (
                <option key={g} value={g}>
                  Grade {g}
                </option>
              ))}
            </select>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
            <label className="text-sm text-slate-400">Questions</label>
            <select
              value={numQuestions}
              onChange={(e) => setNumQuestions(parseInt(e.target.value))}
              className="mt-3 w-full rounded-3xl border border-slate-700 bg-slate-950/90 p-4 text-white outline-none focus:border-cyan-400"
            >
              {[3, 5, 10, 15].map((n) => (
                <option key={n} value={n}>
                  {n} questions
                </option>
              ))}
            </select>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
            <label className="text-sm text-slate-400">Mode</label>
            <select className="mt-3 w-full rounded-3xl border border-slate-700 bg-slate-950/90 p-4 text-white outline-none focus:border-cyan-400">
              <option>MCQ</option>
              <option>True / False</option>
              <option>Fill in the blanks</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-3xl bg-red-900/20 border border-red-600/40 p-4 text-red-200">
            {error}
          </div>
        )}

        {quiz && (
          <div className="mt-6 rounded-3xl bg-slate-900/90 border border-slate-700/60 p-6 whitespace-pre-wrap text-slate-200 text-sm">
            {quiz}
            <button onClick={reset} className="mt-4 rounded-2xl bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700 block">
              Generate another
            </button>
          </div>
        )}
      </div>
    </section>
  );
};

export default Quiz;
