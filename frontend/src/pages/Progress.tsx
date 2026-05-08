import { useProgress } from '../hooks';
import { Loader } from 'lucide-react';

const Progress = () => {
  const { progress, loading } = useProgress();

  if (loading) {
    return (
      <section className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <Loader className="h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-slate-400">Loading your progress...</p>
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-6">
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Progress analytics</p>
            <h2 className="mt-2 text-2xl font-semibold">Track your confidence and mastery</h2>
          </div>
          <div className="rounded-2xl bg-slate-900 px-4 py-3 text-sm text-slate-300">Predicted exam readiness: 72%</div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {Object.entries(progress?.mastery_summary || {}).map(([key, value]) => (
            <div key={key} className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
              <div className="text-xl font-semibold text-white">{value}</div>
              <p className="mt-2 text-sm text-slate-400">{key} mastery</p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Weekly activity</p>
            <h3 className="mt-2 text-xl font-semibold">Your learning trends</h3>
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          <div className="flex items-end gap-2 h-48">
            {progress?.weekly_trend.map((item) => (
              <div key={item.day} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-gradient-to-t from-cyan-400 to-violet-500 rounded-t-2xl transition hover:opacity-80"
                  style={{ height: `${(item.xp / 30) * 100}%` }}
                />
                <span className="text-xs text-slate-400">{item.day}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center justify-between gap-4 mb-4">
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Insights</p>
        </div>

        <div className="space-y-3">
          <div className="rounded-3xl bg-slate-900/90 border border-slate-700/60 p-4">
            <p className="text-sm text-slate-200">
              🎯 You're on a strong learning streak! Keep practicing to maintain your momentum.
            </p>
          </div>
          <div className="rounded-3xl bg-slate-900/90 border border-slate-700/60 p-4">
            <p className="text-sm text-slate-200">
              📈 Focus on weak topics this week — a quick review could boost your mastery by 10%.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Progress;
