"""
Retrieval-Augmented Generation backed by Supabase Postgres + pgvector.

PDFs are stored in Supabase Storage; their extracted text chunks and OpenAI
embeddings live in `curriculum_chunks` (pgvector). Retrieval uses cosine
similarity via the `match_curriculum` SQL function.
"""
from __future__ import annotations

import os
import uuid
from io import BytesIO
from typing import Iterable

from openai import OpenAI
from pypdf import PdfReader

from agent.openai_client import client as _llm_client  # noqa: F401  (ensures env vars set)
from config import OPENAI_API_BASE, OPENAI_API_KEY
from db import (
    execute,
    fetch,
    fetchrow,
    storage_delete,
    storage_download,
    storage_signed_url,
    storage_upload,
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = 1536  # text-embedding-3-small
EMBEDDING_BATCH = 64

# Embeddings always go to OpenAI (most non-OpenAI providers don't host them).
# Use OPENAI_EMBEDDINGS_BASE / OPENAI_EMBEDDINGS_KEY if they differ from the chat model's.
_embed_client = OpenAI(
    api_key=os.getenv("OPENAI_EMBEDDINGS_KEY") or OPENAI_API_KEY,
    base_url=os.getenv("OPENAI_EMBEDDINGS_BASE") or "https://api.openai.com/v1",
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    text = " ".join(text.split())
    chunks: list[str] = []
    i = 0
    while i < len(text):
        end = min(i + chunk_size, len(text))
        if end < len(text):
            space = text.rfind(" ", i, end)
            if space > i + chunk_size // 2:
                end = space
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        i = end - overlap if end - overlap > i else end
    return chunks


def _extract_pdf_text(stream: BytesIO) -> list[tuple[int, str]]:
    reader = PdfReader(stream)
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append((i + 1, txt))
        except Exception:
            continue
    return pages


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of texts."""
    if not texts:
        return []
    resp = _embed_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _to_pgvector(values: list[float]) -> str:
    """psycopg can take a string literal like '[0.1,0.2,...]' for the vector type."""
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"


# ── Public API ─────────────────────────────────────────────────────────────────

def ingest_pdf(file_bytes: bytes, source_name: str, grade: int | None = None) -> dict:
    """
    Upload a PDF to Supabase Storage, extract & chunk its text, embed each chunk
    with OpenAI, and persist embeddings to `curriculum_chunks`.
    """
    grade_val = int(grade) if grade else 0

    # Remove any previous version of this source first
    delete_source(source_name)

    # 1) Persist raw PDF in Storage so we can stream it back later
    storage_path = source_name  # use the file name as the object key
    storage_upload(storage_path, file_bytes, content_type="application/pdf")

    # 2) Extract text
    pages = _extract_pdf_text(BytesIO(file_bytes))
    if not pages:
        execute(
            "insert into curriculum_sources (name, grade, storage_path, pages, chunks) "
            "values (%s, %s, %s, %s, %s)",
            (source_name, grade_val, storage_path, 0, 0),
        )
        return {"source": source_name, "pages": 0, "chunks": 0, "error": "No extractable text"}

    # 3) Build chunks with metadata
    chunk_rows: list[tuple[str, str, int, int, str]] = []  # id, source, page, grade, content
    for page_num, page_text in pages:
        for chunk in _chunk_text(page_text):
            chunk_id = f"{source_name}::p{page_num}::{uuid.uuid4().hex[:8]}"
            chunk_rows.append((chunk_id, source_name, page_num, grade_val, chunk))

    if not chunk_rows:
        execute(
            "insert into curriculum_sources (name, grade, storage_path, pages, chunks) "
            "values (%s, %s, %s, %s, %s)",
            (source_name, grade_val, storage_path, len(pages), 0),
        )
        return {"source": source_name, "pages": len(pages), "chunks": 0}

    # 4) Embed in batches and insert
    execute(
        "insert into curriculum_sources (name, grade, storage_path, pages, chunks) "
        "values (%s, %s, %s, %s, %s)",
        (source_name, grade_val, storage_path, len(pages), len(chunk_rows)),
    )

    for start in range(0, len(chunk_rows), EMBEDDING_BATCH):
        batch = chunk_rows[start:start + EMBEDDING_BATCH]
        embeddings = _embed_batch([r[4] for r in batch])
        for (cid, src, page, gr, content), emb in zip(batch, embeddings):
            execute(
                "insert into curriculum_chunks (id, source, page, grade, content, embedding) "
                "values (%s, %s, %s, %s, %s, %s::vector)",
                (cid, src, page, gr, content, _to_pgvector(emb)),
            )

    return {"source": source_name, "pages": len(pages), "chunks": len(chunk_rows)}


def retrieve(query: str, grade: int | None = None, k: int = 4) -> list[dict]:
    """Return top-k similar chunks to the query, optionally filtered by grade."""
    if not query or not query.strip():
        return []
    if total_chunks() == 0:
        return []
    try:
        emb = _embed_batch([query])[0]
    except Exception:
        return []
    rows = fetch(
        "select source, page, content, similarity from match_curriculum(%s::vector, %s, %s)",
        (_to_pgvector(emb), int(k), int(grade) if grade else None),
    )
    return [
        {"text": r["content"], "source": r["source"], "page": r["page"]}
        for r in rows
    ]


def list_sources() -> list[dict]:
    rows = fetch(
        "select name, grade, pages, chunks from curriculum_sources order by created_at desc"
    )
    return [
        {"source": r["name"], "grade": r["grade"], "chunks": r["chunks"], "pages": r["pages"]}
        for r in rows
    ]


def delete_source(source_name: str) -> int:
    """Delete chunks + storage object for a source. Returns chunks removed."""
    row = fetchrow(
        "select chunks, storage_path from curriculum_sources where name = %s",
        (source_name,),
    )
    chunks = int(row["chunks"]) if row else 0
    # cascade deletes chunks
    execute("delete from curriculum_sources where name = %s", (source_name,))
    if row and row.get("storage_path"):
        try:
            storage_delete(row["storage_path"])
        except Exception:
            pass
    return chunks


def total_chunks() -> int:
    row = fetchrow("select count(*)::int as c from curriculum_chunks")
    return int(row["c"]) if row else 0


def get_pdf_bytes(source_name: str) -> bytes:
    """Download the raw PDF bytes for streaming back to a client."""
    row = fetchrow("select storage_path from curriculum_sources where name = %s", (source_name,))
    if not row or not row.get("storage_path"):
        raise FileNotFoundError(source_name)
    return storage_download(row["storage_path"])


def get_pdf_signed_url(source_name: str, expires_in: int = 3600) -> str:
    row = fetchrow("select storage_path from curriculum_sources where name = %s", (source_name,))
    if not row or not row.get("storage_path"):
        raise FileNotFoundError(source_name)
    return storage_signed_url(row["storage_path"], expires_in=expires_in)


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Source {i}: {c['source']}, page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)
