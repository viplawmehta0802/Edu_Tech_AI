# Supabase Database Setup

EduBot now stores **everything** in Supabase: student accounts, gamification,
analytics, study plans, quiz results, chat history, uploaded PDFs, and the
RAG vector index.

## 1. Create a Supabase project

1. Sign up at https://supabase.com (free tier — 500 MB DB + 1 GB Storage).
2. Create a new project. Pick the region closest to your Render service.
3. Wait for the project to provision (~2 minutes).

## 2. Run the schema

1. In the Supabase dashboard, go to **SQL Editor → New query**.
2. Paste the contents of [`db/schema.sql`](./schema.sql) and click **Run**.
3. This creates all tables, the `vector` extension, the `match_curriculum`
   function, and the `curriculum-pdfs` storage bucket.

## 3. Collect the connection settings

In the Supabase dashboard:

| Where to find it | Env var |
|---|---|
| **Settings → Database → Connection string → URI** (use the **Session pooler**, port 5432) | `DATABASE_URL` |
| **Settings → API → Project URL** | `SUPABASE_URL` |
| **Settings → API → service_role key** (NOT anon) | `SUPABASE_SERVICE_ROLE_KEY` |

⚠️ The service role key is a server-side secret. Never expose it in the
frontend or commit it to git.

## 4. Configure on Render

In your `EdTech-agent` service → **Environment** tab → add:

```
DATABASE_URL=postgresql://postgres.xxxxx:PASSWORD@aws-0-xx-xxxx-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
SUPABASE_BUCKET=curriculum-pdfs
```

(Plus your existing `OPENAI_API_KEY`, `OPENAI_API_BASE`, `MODEL_NAME`.)

Save → Render auto-redeploys.

## 5. Local development

Create `EdTech-agent/.env` with the same vars and run:

```powershell
cd EdTech-agent
pip install -r requirements.txt
python main.py
```

The server logs "Postgres connection pool ready." on startup if everything
is wired correctly.

## What gets stored where

| Data | Location |
|---|---|
| Students, passwords, profile, gamification, analytics | `students` table |
| Study plans | `study_plans` table |
| Quiz results | `quiz_results` table |
| Per-student chat history | `chat_messages` table |
| Uploaded PDF metadata | `curriculum_sources` table |
| Uploaded PDF raw bytes | Supabase Storage bucket `curriculum-pdfs` |
| RAG chunks + embeddings | `curriculum_chunks` table (pgvector) |

## Notes

- Embeddings use OpenAI `text-embedding-3-small` (1536 dims). Set
  `EMBEDDING_MODEL` to override. If your chat key is OpenRouter, set
  `OPENAI_EMBEDDINGS_KEY` and `OPENAI_EMBEDDINGS_BASE` to a real OpenAI key
  (OpenRouter doesn't reliably proxy embeddings).
- Free tier limits: 500 MB DB / 1 GB storage / 2 GB egress per month.
  Roughly enough for thousands of students and ~500 medium-sized textbook PDFs.
- For first-time RAG queries after a long sleep, the IVFFLAT index may
  benefit from `vacuum analyze curriculum_chunks;` once you have data.
