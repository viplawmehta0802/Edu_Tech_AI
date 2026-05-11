import { useEffect, useRef, useState } from 'react';
import { FileUp, Loader, Lock, LogOut, Trash2, Users, FileText } from 'lucide-react';
import {
  apiClient,
  type CurriculumSource,
  type StudentProfile,
} from '../lib/api';
import { useAuth } from '../context/AuthContext';

const Admin = () => {
  const { isAdmin, loginAdmin, logoutAdmin } = useAuth();
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [sources, setSources] = useState<CurriculumSource[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [students, setStudents] = useState<Record<string, StudentProfile>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [grade, setGrade] = useState(0);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAdmin) void refresh();
  }, [isAdmin]);

  const refresh = async () => {
    try {
      const [c, s] = await Promise.all([
        apiClient.listCurriculum(),
        apiClient.listStudents(),
      ]);
      setSources(c.sources);
      setTotalChunks(c.total_chunks);
      setStudents(s);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Refresh failed');
    }
  };

  const handleLogin = async () => {
    setAuthLoading(true);
    setAuthError(null);
    try {
      await loginAdmin(password);
      setPassword('');
    } catch (e) {
      setAuthError(e instanceof Error ? e.message : 'Login failed');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErr('Only PDF files are accepted');
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await apiClient.uploadCurriculum(file, grade);
      setMsg(`Indexed “${res.source}” — ${res.pages} pages, ${res.chunks} chunks`);
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = '';
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Remove “${name}” and all its indexed chunks?`)) return;
    setBusy(true);
    setErr(null);
    try {
      await apiClient.deleteCurriculum(name);
      setMsg(`Removed ${name}`);
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setBusy(false);
    }
  };

  // ── Login gate ──────────────────────────────────────────────────
  if (!isAdmin) {
    return (
      <section className="max-w-md mx-auto">
        <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-8 shadow-soft">
          <div className="flex items-center gap-3 mb-4">
            <Lock className="h-6 w-6 text-cyan-400" />
            <h2 className="text-2xl font-semibold">Admin sign-in</h2>
          </div>
          <p className="text-sm text-slate-400 mb-6">
            Enter the admin password (set via <code className="text-cyan-300">ADMIN_PASSWORD</code> in
            the EdTech-agent <code className="text-cyan-300">.env</code>).
          </p>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
            placeholder="Password"
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-400"
          />
          <button
            onClick={handleLogin}
            disabled={!password || authLoading}
            className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
          >
            {authLoading && <Loader className="h-4 w-4 animate-spin" />}
            Sign in
          </button>
          {authError && (
            <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {authError}
            </div>
          )}
        </div>
      </section>
    );
  }

  // ── Admin panel ─────────────────────────────────────────────────
  return (
    <section className="space-y-6">
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-300/80">Admin</p>
            <h2 className="mt-2 text-2xl font-semibold">Manage study material & students</h2>
            <p className="mt-1 text-sm text-slate-400">
              {sources.length} document(s) indexed • {totalChunks} chunks •{' '}
              {Object.keys(students).length} student(s)
            </p>
          </div>
          <button
            onClick={logoutAdmin}
            className="inline-flex items-center gap-2 rounded-2xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </div>

      {/* Upload */}
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center gap-3 mb-4">
          <FileUp className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold">Upload study material (PDF)</h3>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          PDFs are stored in <code className="text-cyan-300">EdTech-agent/curriculum/</code>{' '}
          and indexed into ChromaDB at{' '}
          <code className="text-cyan-300">EdTech-agent/chroma_db/</code>. The tutor will
          retrieve relevant chunks at chat time (RAG).
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">
              Grade tag (0 = all grades)
            </label>
            <select
              value={grade}
              onChange={(e) => setGrade(parseInt(e.target.value))}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-white outline-none focus:border-cyan-400"
            >
              <option value={0}>All grades</option>
              {Array.from({ length: 7 }, (_, i) => i + 6).map((g) => (
                <option key={g} value={g}>
                  Grade {g}
                </option>
              ))}
            </select>
          </div>
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf"
            disabled={busy}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleUpload(f);
            }}
            className="block text-sm text-slate-300 file:mr-4 file:rounded-xl file:border-0 file:bg-gradient-to-r file:from-cyan-400 file:to-violet-500 file:px-5 file:py-2 file:text-slate-950 file:font-semibold"
          />
          {busy && (
            <span className="inline-flex items-center gap-2 text-slate-300 text-sm">
              <Loader className="h-4 w-4 animate-spin" /> Working...
            </span>
          )}
        </div>
        {msg && (
          <div className="mt-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {msg}
          </div>
        )}
        {err && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {err}
          </div>
        )}
      </div>

      {/* Indexed documents */}
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center gap-3 mb-4">
          <FileText className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold">Indexed documents</h3>
        </div>
        {sources.length === 0 ? (
          <p className="text-sm text-slate-400">No PDFs indexed yet.</p>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/80 text-slate-400 text-left text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Grade</th>
                  <th className="px-4 py-3">Chunks</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.source} className="border-t border-slate-800">
                    <td className="px-4 py-3 text-white truncate max-w-xs">{s.source}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {s.grade === 0 ? 'All' : s.grade}
                    </td>
                    <td className="px-4 py-3 text-slate-300">{s.chunks}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(s.source)}
                        disabled={busy}
                        className="inline-flex items-center gap-1 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs text-red-200 hover:bg-red-500/20 disabled:opacity-50"
                      >
                        <Trash2 className="h-3 w-3" /> Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Students */}
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center gap-3 mb-4">
          <Users className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold">Students</h3>
        </div>
        {Object.keys(students).length === 0 ? (
          <p className="text-sm text-slate-400">No students registered.</p>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/80 text-slate-400 text-left text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Grade</th>
                  <th className="px-4 py-3">Weak topics</th>
                  <th className="px-4 py-3">Lessons</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(students).map(([id, p]) => (
                  <tr key={id} className="border-t border-slate-800">
                    <td className="px-4 py-3 text-cyan-300 font-mono text-xs">{id}</td>
                    <td className="px-4 py-3 text-white">{p.name}</td>
                    <td className="px-4 py-3 text-slate-300">{p.grade}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {(p.weak_topics || []).join(', ') || '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {(p.completed_lessons || []).length}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
};

export default Admin;
