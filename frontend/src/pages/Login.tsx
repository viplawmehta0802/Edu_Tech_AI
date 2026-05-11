import { useEffect, useState } from 'react';
import { Loader, LogIn, Mail, UserPlus } from 'lucide-react';
import { apiClient, type StudentProfile } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type Tab = 'existing' | 'new';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const Login = () => {
  const { loginStudent } = useAuth();
  const [tab, setTab] = useState<Tab>('existing');
  const [students, setStudents] = useState<Record<string, StudentProfile>>({});
  const [signInEmail, setSignInEmail] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // signup form
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newGrade, setNewGrade] = useState(8);

  useEffect(() => {
    void refresh();
  }, []);

  const refresh = async () => {
    try {
      const data = await apiClient.listStudents();
      setStudents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load students');
    }
  };

  // Try to find a student id whose email or id equals the given value (case-insensitive).
  const findStudentId = (value: string): string | null => {
    const v = value.trim().toLowerCase();
    if (!v) return null;
    for (const [id, p] of Object.entries(students)) {
      if (id.toLowerCase() === v) return id;
      if (p.email && p.email.toLowerCase() === v) return id;
    }
    return null;
  };

  const handleSignIn = async () => {
    setError(null);
    setInfo(null);
    const target = selected || findStudentId(signInEmail);
    if (!target) {
      setError("No account found for that email. Use “New student” to sign up.");
      return;
    }
    setLoading(true);
    try {
      await loginStudent(target);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setError(null);
    setInfo(null);
    const email = newEmail.trim().toLowerCase();
    if (!EMAIL_RE.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!newName.trim()) {
      setError('Please enter your name.');
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient.createStudent({
        email,
        name: newName.trim(),
        grade: newGrade,
      });
      if (res.email_sent) {
        setInfo(`Welcome email sent to ${email}.`);
      } else if (res.email_configured === false) {
        setInfo('Account created. (Welcome email skipped — SMTP not configured on server.)');
      } else {
        setInfo('Account created. Welcome email could not be sent.');
      }
      await loginStudent(res.student_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create account');
    } finally {
      setLoading(false);
    }
  };

  const studentEntries = Object.entries(students);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-indigo-950 to-violet-950 p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-700/60 bg-slate-900/90 shadow-2xl overflow-hidden backdrop-blur-xl">
        <div className="px-8 pt-8 pb-6 text-center">
          <div className="text-4xl mb-2">🎓</div>
          <h1 className="text-2xl font-bold text-white">Welcome to EduBot</h1>
          <p className="mt-2 text-sm text-slate-400">
            AI learning assistant for Grades 6–12
          </p>
        </div>

        <div className="flex border-t border-slate-800">
          <button
            className={`flex-1 px-4 py-3 text-sm font-semibold transition ${
              tab === 'existing'
                ? 'text-white border-b-2 border-cyan-400 bg-slate-800/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setTab('existing')}
          >
            <LogIn className="inline h-4 w-4 mr-2" />
            Sign in
          </button>
          <button
            className={`flex-1 px-4 py-3 text-sm font-semibold transition ${
              tab === 'new'
                ? 'text-white border-b-2 border-cyan-400 bg-slate-800/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setTab('new')}
          >
            <UserPlus className="inline h-4 w-4 mr-2" />
            New student
          </button>
        </div>

        <div className="p-6">
          {tab === 'existing' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Email
              </label>
              <div className="relative mb-3">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="email"
                  value={signInEmail}
                  onChange={(e) => {
                    setSignInEmail(e.target.value);
                    setSelected(null);
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleSignIn()}
                  placeholder="you@example.com"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 pl-9 pr-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                />
              </div>

              {studentEntries.length > 0 && (
                <>
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-2 mt-4">
                    Or pick a saved account
                  </div>
                  <div className="max-h-48 overflow-y-auto pr-1 space-y-2">
                    {studentEntries.map(([id, p]) => {
                      const initials = (p.name || id)
                        .split(' ')
                        .map((s: string) => s[0])
                        .join('')
                        .slice(0, 2)
                        .toUpperCase();
                      const sel = selected === id;
                      const subtitle = p.email || id;
                      return (
                        <button
                          key={id}
                          onClick={() => {
                            setSelected(id);
                            setSignInEmail(p.email || '');
                          }}
                          className={`w-full flex items-center gap-3 rounded-2xl border-2 p-3 text-left transition ${
                            sel
                              ? 'border-cyan-400 bg-cyan-500/10'
                              : 'border-slate-700 hover:border-slate-500 bg-slate-950/40'
                          }`}
                        >
                          <div className="h-11 w-11 flex items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 text-slate-950 font-bold text-sm">
                            {initials}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-white text-sm truncate">
                              {p.name}
                            </div>
                            <div className="text-xs text-slate-400 truncate">
                              {subtitle} • Grade {p.grade}
                            </div>
                          </div>
                          {sel && <div className="text-cyan-400 text-xl">✓</div>}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}

              <button
                onClick={handleSignIn}
                disabled={loading || (!selected && !signInEmail.trim())}
                className="mt-6 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
              >
                {loading && <Loader className="h-4 w-4 animate-spin" />}
                Sign in
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/80 pl-9 pr-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                  />
                </div>
                <p className="mt-1 text-[11px] text-slate-500">
                  We’ll send a welcome email to this address.
                </p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Full name
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g., Alex Doe"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Grade
                </label>
                <select
                  value={newGrade}
                  onChange={(e) => setNewGrade(parseInt(e.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                >
                  {Array.from({ length: 7 }, (_, i) => i + 6).map((g) => (
                    <option key={g} value={g}>
                      Grade {g}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleCreate}
                disabled={loading}
                className="w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-400 to-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
              >
                {loading && <Loader className="h-4 w-4 animate-spin" />}
                Sign up & send welcome email
              </button>
            </div>
          )}

          {info && (
            <div className="mt-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {info}
            </div>
          )}
          {error && (
            <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
