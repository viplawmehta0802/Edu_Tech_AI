"""
Supabase database client.

- Postgres connection pool via psycopg (sync) for simple synchronous use.
- Storage operations via Supabase REST API (avoids needing the supabase-py SDK
  which pulls in a lot of deps).

Required env vars:
    DATABASE_URL                   Postgres connection string from Supabase
                                   (Settings → Database → Connection string → URI).
                                   Use the **session pooler** (port 5432) URL.
    SUPABASE_URL                   https://<project-ref>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY      Service role key (server-side only, NEVER ship to client)
    SUPABASE_BUCKET                Bucket name (default: 'curriculum-pdfs')
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Iterable, Sequence

import httpx
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "curriculum-pdfs")

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def is_configured() -> bool:
    return bool(DATABASE_URL and SUPABASE_URL and SUPABASE_KEY)


def get_pool() -> ConnectionPool:
    """Lazy-init a thread-safe Postgres connection pool."""
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:
            return _pool
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. Configure Supabase Postgres connection string."
            )
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row, "autocommit": True},
            open=True,
        )
        return _pool


# ── Query helpers ──────────────────────────────────────────────────────────────

def fetch(sql: str, params: Sequence[Any] | None = None) -> list[dict]:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def fetchrow(sql: str, params: Sequence[Any] | None = None) -> dict | None:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        row = cur.fetchone()
        return row


def execute(sql: str, params: Sequence[Any] | None = None) -> int:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.rowcount


def executemany(sql: str, seq_of_params: Iterable[Sequence[Any]]) -> None:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.executemany(sql, list(seq_of_params))


# ── Supabase Storage helpers (REST API) ────────────────────────────────────────

def _storage_headers(extra: dict | None = None) -> dict:
    h = {"Authorization": f"Bearer {SUPABASE_KEY}"}
    if extra:
        h.update(extra)
    return h


def storage_upload(path: str, file_bytes: bytes, content_type: str = "application/pdf") -> str:
    """Upload bytes to the configured bucket. `path` is the object key."""
    if not is_configured():
        raise RuntimeError("Supabase storage not configured")
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{path}"
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            url,
            headers=_storage_headers({
                "Content-Type": content_type,
                "x-upsert": "true",
            }),
            content=file_bytes,
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"Storage upload failed ({resp.status_code}): {resp.text[:200]}")
    return path


def storage_download(path: str) -> bytes:
    if not is_configured():
        raise RuntimeError("Supabase storage not configured")
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{path}"
    with httpx.Client(timeout=60.0) as client:
        resp = client.get(url, headers=_storage_headers())
        if resp.status_code >= 300:
            raise RuntimeError(f"Storage download failed ({resp.status_code}): {resp.text[:200]}")
        return resp.content


def storage_delete(path: str) -> None:
    if not is_configured():
        return
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{path}"
    with httpx.Client(timeout=30.0) as client:
        client.delete(url, headers=_storage_headers())


def storage_signed_url(path: str, expires_in: int = 3600) -> str:
    """Create a time-limited signed URL for a private object."""
    url = f"{SUPABASE_URL}/storage/v1/object/sign/{SUPABASE_BUCKET}/{path}"
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            url,
            headers=_storage_headers({"Content-Type": "application/json"}),
            json={"expiresIn": expires_in},
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"Signed URL failed ({resp.status_code}): {resp.text[:200]}")
        signed_path = resp.json().get("signedURL", "")
        return f"{SUPABASE_URL}/storage/v1{signed_path}"
