import { useEffect, useRef, useState } from 'react';
import {
  BookMarked,
  ClipboardCopy,
  FileQuestion,
  FileText,
  Loader,
  Sparkles,
  Upload,
} from 'lucide-react';
import { apiClient, type CurriculumSource } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type NoteStyle = 'bullets' | 'summary' | 'flashcards';

const StudyLab = () => {
  const { profile } = useAuth();

  // ── PDF viewer + note maker ────────────────────────────────────
  const [sources, setSources] = useState<CurriculumSource[]>([]);
  const [selectedPdf, setSelectedPdf] = useState<string | null>(null);
  const [highlight, setHighlight] = useState('');
  const [style, setStyle] = useState<NoteStyle>('bullets');
  const [notes, setNotes] = useState<string | null>(null);
  const [notesLoading, setNotesLoading] = useState(false);
  const [notesErr, setNotesErr] = useState<string | null>(null);

  // ── Quiz from Q&A PDF ──────────────────────────────────────────
  const [quizFile, setQuizFile] = useState<File | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);
  const [quiz, setQuiz] = useState<string | null>(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizErr, setQuizErr] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void apiClient
      .listCurriculum()
      .then((c) => {
        setSources(c.sources);
        if (c.sources.length && !selectedPdf) setSelectedPdf(c.sources[0].source);
      })
      .catch(() => {
        // non-fatal
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleMakeNotes = async () => {
    if (!highlight.trim()) return;
    setNotesLoading(true);
    setNotesErr(null);
    setNotes(null);
    try {
      const res = await apiClient.summarizeNotes({
        text: highlight,
        grade: profile?.grade,
        style,
      });
      setNotes(res.notes);
    } catch (e) {
      setNotesErr(e instanceof Error ? e.message : 'Failed to make notes');
    } finally {
      setNotesLoading(false);
    }
  };

  const captureSelectionFromPage = () => {
    const sel = window.getSelection()?.toString() || '';
    if (sel.trim()) setHighlight((prev) => (prev ? prev + '\n\n' + sel : sel));
  };

  const handleQuizFromPdf = async () => {
    if (!quizFile) return;
    setQuizLoading(true);
    setQuizErr(null);
    setQuiz(null);
    try {
      const res = await apiClient.quizFromPdf(quizFile, numQuestions, profile?.grade || 0);
      setQuiz(res.quiz);
    } catch (e) {
      setQuizErr(e instanceof Error ? e.message : 'Failed to build quiz');
    } finally {
      setQuizLoading(false);
    }
  };

  const copyNotes = async () => {
    if (!notes) return;
    try {
      await navigator.clipboard.writeText(notes);
    } catch {
      // ignore
    }
  };

  const pdfUrl = selectedPdf ? apiClient.curriculumFileUrl(selectedPdf) : null;

  return (
    <section className="space-y-6">
      {/* ── PDF Viewer + Short Notes ────────────────────────────── */}
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center gap-3 mb-2">
          <BookMarked className="h-5 w-5 text-cyan-400" />
          <h2 className="text-xl font-semibold">Read PDF & make short notes</h2>
        </div>
        <p className="text-sm text-slate-400 mb-5">
          Pick an indexed PDF, highlight any text inside the viewer, then either click{' '}
          <span className="text-cyan-300">“Add highlight”</span> or paste it below. Generate
          tight bullets, a summary, or flashcards in one click.
        </p>

        <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          {/* Viewer */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={selectedPdf || ''}
                onChange={(e) => setSelectedPdf(e.target.value || null)}
                className="flex-1 min-w-[200px] rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
              >
                {sources.length === 0 && <option value="">No PDFs indexed yet</option>}
                {sources.map((s) => (
                  <option key={s.source} value={s.source}>
                    {s.source}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={captureSelectionFromPage}
                className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800"
                title="Capture any text you've selected on this page"
              >
                + Add highlight
              </button>
            </div>
            <div className="rounded-2xl border border-slate-700 bg-slate-900/60 overflow-hidden h-[520px]">
              {pdfUrl ? (
                <iframe
                  title="PDF viewer"
                  src={pdfUrl}
                  className="w-full h-full bg-white"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-slate-400 text-sm">
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="h-10 w-10 opacity-50" />
                    Upload a PDF from the Admin page first.
                  </div>
                </div>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Tip: in most browsers, text selected inside the PDF viewer can be copied with{' '}
              <kbd className="rounded bg-slate-800 px-1.5 py-0.5">Ctrl</kbd>+
              <kbd className="rounded bg-slate-800 px-1.5 py-0.5">C</kbd>, then pasted into the
              highlight box on the right.
            </p>
          </div>

          {/* Notes panel */}
          <div className="space-y-3">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Highlighted text
            </label>
            <textarea
              value={highlight}
              onChange={(e) => setHighlight(e.target.value)}
              placeholder="Paste or type the passage you want short notes for..."
              className="w-full h-44 rounded-xl border border-slate-700 bg-slate-900/80 p-3 text-sm text-white outline-none focus:border-cyan-400 resize-none"
            />
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value as NoteStyle)}
                className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
              >
                <option value="bullets">Bullet notes</option>
                <option value="summary">Short summary</option>
                <option value="flashcards">Flashcards (Q/A)</option>
              </select>
              <button
                onClick={handleMakeNotes}
                disabled={notesLoading || !highlight.trim()}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
              >
                {notesLoading ? (
                  <Loader className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Make notes
              </button>
              <button
                onClick={() => {
                  setHighlight('');
                  setNotes(null);
                  setNotesErr(null);
                }}
                className="rounded-xl border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800"
              >
                Clear
              </button>
            </div>

            {notesErr && (
              <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                {notesErr}
              </div>
            )}
            {notes && (
              <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-100 whitespace-pre-wrap">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs uppercase tracking-wider text-cyan-300/80">
                    Short notes
                  </span>
                  <button
                    onClick={copyNotes}
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
                  >
                    <ClipboardCopy className="h-3 w-3" /> Copy
                  </button>
                </div>
                {notes}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Quiz from Q&A PDF ───────────────────────────────────── */}
      <div className="rounded-[32px] border border-slate-700/60 bg-slate-950/90 p-6 shadow-soft">
        <div className="flex items-center gap-3 mb-2">
          <FileQuestion className="h-5 w-5 text-cyan-400" />
          <h2 className="text-xl font-semibold">Make a quiz from a Q&amp;A PDF</h2>
        </div>
        <p className="text-sm text-slate-400 mb-5">
          Upload a PDF (study notes, an answer key, or a chapter). The AI will read it and
          build multiple-choice questions grounded in that content. The PDF is{' '}
          <span className="text-cyan-300">not</span> added to the RAG index.
        </p>

        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">
              Questions
            </label>
            <select
              value={numQuestions}
              onChange={(e) => setNumQuestions(parseInt(e.target.value))}
              className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            >
              {[3, 5, 10, 15, 20].map((n) => (
                <option key={n} value={n}>
                  {n} questions
                </option>
              ))}
            </select>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={(e) => setQuizFile(e.target.files?.[0] || null)}
            className="block text-sm text-slate-300 file:mr-4 file:rounded-xl file:border-0 file:bg-slate-800 file:px-4 file:py-2 file:text-slate-200 file:cursor-pointer"
          />
          <button
            onClick={handleQuizFromPdf}
            disabled={!quizFile || quizLoading}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
          >
            {quizLoading ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Generate quiz
          </button>
        </div>

        {quizErr && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {quizErr}
          </div>
        )}
        {quiz && (
          <div className="mt-5 rounded-2xl border border-slate-700 bg-slate-900/80 p-5 text-sm text-slate-100 whitespace-pre-wrap">
            {quiz}
          </div>
        )}
      </div>
    </section>
  );
};

export default StudyLab;
