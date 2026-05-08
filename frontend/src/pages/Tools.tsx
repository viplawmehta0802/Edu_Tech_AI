const Tools = () => {
  const cards = [
    { title: 'Explain like I’m 10', description: 'Simplify any concept in student-friendly language.' },
    { title: 'Summarize notes', description: 'Turn textbook notes into easy study bullets.' },
    { title: 'Mind map generator', description: 'Create a visual concept map for your subject.' },
    { title: 'Essay feedback', description: 'Get feedback on structure, clarity, and grammar.' },
  ];

  return (
    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Learning tools</p>
          <h2 className="mt-2 text-2xl font-semibold">Build stronger study habits with AI support</h2>
        </div>
        <div className="mt-6 grid gap-4">
          {cards.map((card) => (
            <div key={card.title} className="rounded-3xl border border-slate-700/60 bg-slate-900/90 p-5">
              <h3 className="font-semibold text-white">{card.title}</h3>
              <p className="mt-2 text-slate-400">{card.description}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Tool spotlight</p>
        <div className="mt-4 space-y-4">
          <div className="rounded-3xl bg-slate-900/90 p-5">
            <h3 className="font-semibold text-white">Formula sheet generator</h3>
            <p className="mt-2 text-slate-400">Generate quick formula guides for math and science topics.</p>
          </div>
          <div className="rounded-3xl bg-slate-900/90 p-5">
            <h3 className="font-semibold text-white">Grammar helper</h3>
            <p className="mt-2 text-slate-400">Check essays for clarity, tone, and corrections.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Tools;
