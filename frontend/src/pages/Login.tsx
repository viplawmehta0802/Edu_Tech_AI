import { useState } from 'react';
import { Loader, Lock, LogIn, Mail, UserPlus } from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type Tab = 'existing' | 'new';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const Login = () => {
  const { loginStudent, setSession } = useAuth();
  const [tab, setTab] = useState<Tab>('existing');
  const [signInEmail, setSignInEmail] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // signup form
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newGrade, setNewGrade] = useState(8);

  const handleSignIn = async () => {
    setError(null);
    setInfo(null);
    const email = signInEmail.trim().toLowerCase();
    if (!EMAIL_RE.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!signInPassword) {
      setError('Please enter your password.');
      return;
    }
    setLoading(true);
    try {
      await loginStudent(email, signInPassword);
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
        setInfo(`Welcome email sent to ${email}. Check your inbox for your password.`);
      } else if (res.email_configured === false && res.password) {
        setInfo(`Account created. Email is not configured on the server, so save this password now: ${res.password}`);
      } else if (res.password) {
        setInfo(`Account created, but the welcome email failed. Save this password now: ${res.password}`);
      } else {
        setInfo('Account created.');
      }
      // Auto-login the new user using the profile returned by the server.
      setSession(res.student_id, res.profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create account');
    } finally {
      setLoading(false);
    }
  };

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
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type="email"
                    value={signInEmail}
                    onChange={(e) => setSignInEmail(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSignIn()}
                    placeholder="you@example.com"
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/80 pl-9 pr-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type="password"
                    value={signInPassword}
                    onChange={(e) => setSignInPassword(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSignIn()}
                    placeholder="Your password"
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/80 pl-9 pr-4 py-3 text-white text-sm outline-none focus:border-cyan-400"
                  />
                </div>
                <p className="mt-1 text-[11px] text-slate-500">
                  Use the password sent to your email at signup.
                </p>
              </div>

              <button
                onClick={handleSignIn}
                disabled={loading || !signInEmail.trim() || !signInPassword}
                className="mt-2 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
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
                  We’ll email a welcome message with your auto-generated password.
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
