const Dashboard = () => {
  return (
    <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-6 rounded-[32px] bg-slate-900/90 p-6 shadow-soft border border-slate-700/40">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Today’s focus</p>
            <h2 className="mt-2 text-2xl font-semibold">Master photosynthesis practice</h2>
          </div>
          <div className="rounded-3xl bg-slate-800/90 px-4 py-3 text-sm text-slate-300">Grade 11 • Science</div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {[
            { heading: 'Upcoming quiz', value: 'Biology checkpoint', detail: 'Tomorrow 10:00 AM' },
            { heading: 'Weak topic', value: 'Photosynthesis', detail: 'Review light reactions' },
          ].map((card) => (
            <div key={card.heading} className="rounded-3xl border border-slate-700/60 bg-slate-950/90 p-5 shadow-soft">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">{card.heading}</p>
              <div className="mt-3 text-xl font-semibold text-white">{card.value}</div>
              <p className="mt-2 text-sm text-slate-400">{card.detail}</p>
            </div>
          ))}
        </div>

        <div className="rounded-3xl border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Progress</p>
              <h3 className="mt-2 text-xl font-semibold">Study streak</h3>
            </div>
            <div className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-200">+34 XP today</div>
          </div>
          <div className="mt-6 h-3 rounded-full bg-slate-800">
            <div className="h-full w-3/5 rounded-full bg-gradient-to-r from-cyan-400 via-indigo-500 to-violet-500" />
          </div>
          <div className="mt-3 flex items-center justify-between text-sm text-slate-400">
            <span>3 of 5 goals completed</span>
            <span>60% mastery</span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Personalized AI message</p>
              <h3 className="mt-2 text-xl font-semibold">You’re on a strong streak, keep it going!</h3>
            </div>
          </div>
          <p className="mt-4 text-slate-400">EduBot suggests a short science quiz now, then a quick coding concept review later today.</p>
        </div>

        <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Quick actions</p>
          <div className="mt-4 grid gap-3">
            {['Continue lesson', 'Generate study plan', 'Take an adaptive quiz'].map((label) => (
              <button key={label} className="rounded-2xl bg-slate-900 px-4 py-3 text-left text-sm text-white transition hover:bg-slate-800">
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;
