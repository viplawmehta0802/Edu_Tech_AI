-- ─────────────────────────────────────────────────────────────────────────────
-- EduBot Supabase schema. Run this once in Supabase SQL editor.
-- ─────────────────────────────────────────────────────────────────────────────

create extension if not exists vector;

-- ── Students ────────────────────────────────────────────────────────────────
create table if not exists students (
    id              text primary key,           -- usually the lowercased email
    email           text unique,
    name            text not null,
    grade           int  not null,
    password_hash   text,
    weak_topics     text[]   not null default '{}',
    completed_lessons text[] not null default '{}',
    gamification    jsonb    not null default jsonb_build_object(
                        'points', 0,
                        'badges', '[]'::jsonb,
                        'current_streak', 0,
                        'longest_streak', 0,
                        'last_activity', null
                    ),
    analytics       jsonb    not null default jsonb_build_object(
                        'quizzes_taken', 0,
                        'average_score', 0,
                        'total_questions', 0,
                        'correct_answers', 0,
                        'time_spent_minutes', 0,
                        'subjects_practiced', '[]'::jsonb
                    ),
    created_at      timestamptz not null default now()
);

-- ── Study plans ─────────────────────────────────────────────────────────────
create table if not exists study_plans (
    id          bigserial primary key,
    student_id  text not null references students(id) on delete cascade,
    plan        jsonb not null,
    created_at  timestamptz not null default now()
);
create index if not exists study_plans_student_idx on study_plans(student_id);

-- ── Quiz results ────────────────────────────────────────────────────────────
create table if not exists quiz_results (
    id                  bigserial primary key,
    student_id          text not null references students(id) on delete cascade,
    topic               text,
    score_percentage    real,
    questions_count     int,
    correct_count       int,
    time_spent_minutes  int,
    created_at          timestamptz not null default now()
);
create index if not exists quiz_results_student_idx on quiz_results(student_id);

-- ── Chat history ────────────────────────────────────────────────────────────
create table if not exists chat_messages (
    id          bigserial primary key,
    student_id  text not null references students(id) on delete cascade,
    role        text not null check (role in ('user', 'assistant', 'system')),
    content     text not null,
    created_at  timestamptz not null default now()
);
create index if not exists chat_messages_student_idx on chat_messages(student_id, created_at);

-- ── Curriculum (uploaded PDFs metadata) ─────────────────────────────────────
create table if not exists curriculum_sources (
    name          text primary key,        -- file name, used as source identifier
    grade         int not null default 0,
    storage_path  text,                    -- path in the Supabase Storage bucket
    pages         int not null default 0,
    chunks        int not null default 0,
    created_at    timestamptz not null default now()
);

-- ── Curriculum chunks with pgvector embeddings (text-embedding-3-small = 1536) ─
create table if not exists curriculum_chunks (
    id          text primary key,
    source      text not null references curriculum_sources(name) on delete cascade,
    page        int  not null default 0,
    grade       int  not null default 0,
    content     text not null,
    embedding   vector(1536),
    created_at  timestamptz not null default now()
);
create index if not exists curriculum_chunks_source_idx on curriculum_chunks(source);
create index if not exists curriculum_chunks_grade_idx  on curriculum_chunks(grade);
-- ANN index for cosine similarity search
create index if not exists curriculum_chunks_embedding_idx
    on curriculum_chunks using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ── Top-k similarity search RPC (called from Python) ────────────────────────
create or replace function match_curriculum(
    query_embedding vector(1536),
    match_count int default 4,
    filter_grade int default null
)
returns table (
    id      text,
    source  text,
    page    int,
    grade   int,
    content text,
    similarity float
)
language sql stable as $$
    select
        c.id,
        c.source,
        c.page,
        c.grade,
        c.content,
        1 - (c.embedding <=> query_embedding) as similarity
    from curriculum_chunks c
    where filter_grade is null or c.grade in (filter_grade, 0)
    order by c.embedding <=> query_embedding
    limit match_count;
$$;

-- ── Storage bucket for raw PDFs ─────────────────────────────────────────────
-- Run once in the Supabase dashboard (Storage tab), or via SQL:
insert into storage.buckets (id, name, public)
values ('curriculum-pdfs', 'curriculum-pdfs', false)
on conflict (id) do nothing;
