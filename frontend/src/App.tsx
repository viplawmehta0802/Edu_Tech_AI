import { useState, type FC, type ReactElement } from 'react';
import { Award, BarChart3, BookOpen, Cpu, Sparkles } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Tutor from './pages/Tutor';
import Quiz from './pages/Quiz';
import Tools from './pages/Tools';
import Progress from './pages/Progress';

const navItems = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'tutor', label: 'Tutor', icon: BookOpen },
  { key: 'quiz', label: 'Quiz', icon: Sparkles },
  { key: 'tools', label: 'Tools', icon: Cpu },
  { key: 'progress', label: 'Progress', icon: Award },
] as const;

type NavItemKey = (typeof navItems)[number]['key'];

const activeComponents: Record<NavItemKey, FC> = {
  dashboard: Dashboard,
  tutor: Tutor,
  quiz: Quiz,
  tools: Tools,
  progress: Progress,
};

function renderActive(key: NavItemKey): ReactElement {
  const Component = activeComponents[key];
  return <Component />;
}

function App() {
  const [active, setActive] = useState<NavItemKey>('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col lg:flex-row px-4 py-6 gap-6">
        <aside className="w-full max-w-[300px] rounded-3xl bg-slate-900/80 p-6 shadow-soft backdrop-blur-xl border border-slate-700/50 lg:h-fit">
          <div className="mb-8">
            <div className="text-3xl font-semibold">EduBot</div>
            <div className="mt-2 text-slate-400">AI learning assistant for Grades 6–12</div>
          </div>
          <div className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const activeClass = active === item.key ? 'bg-slate-800 text-white' : 'hover:bg-slate-800/80 text-slate-300';
              return (
                <button
                  key={item.key}
                  onClick={() => setActive(item.key)}
                  className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition ${activeClass}`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="mt-10 rounded-3xl border border-slate-700/60 bg-slate-950/80 p-5">
            <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Today</div>
            <div className="mt-4 text-2xl font-semibold">XP streak</div>
            <div className="mt-2 text-slate-400">3 days in a row</div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
              <div className="h-full w-3/4 bg-gradient-to-r from-cyan-400 to-violet-500" />
            </div>
          </div>
        </aside>

        <main className="flex-1">
          <div className="mb-6 rounded-[32px] bg-slate-900/90 p-6 shadow-soft border border-slate-700/40 backdrop-blur-xl">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Welcome back</div>
                <div className="mt-2 text-3xl font-semibold">Ready to learn smarter today?</div>
              </div>
              <button className="inline-flex items-center justify-center rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:brightness-110">
                Start a session
              </button>
            </div>
          </div>

          <div className="space-y-6">
            {renderActive(active)}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
