"""
RAG (Retrieval-Augmented Generation) module.
Indexes PDF curriculum into ChromaDB and retrieves relevant chunks at query time.
"""
import os
import ssl
import uuid
import httpx
from pypdf import PdfReader
from config import OPENAI_API_KEY, DISABLE_SSL_VERIFY

# Optional SSL workaround for corporate proxies
if DISABLE_SSL_VERIFY:
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    _orig_httpx_client = httpx.Client
    def _insecure_httpx_client(*args, **kwargs):
        kwargs["verify"] = False
        return _orig_httpx_client(*args, **kwargs)
    httpx.Client = _insecure_httpx_client

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
os.makedirs(CURRICULUM_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# ── Chroma client + collection ─────────────────────────────────────
# ChromaDB's OpenAIEmbeddingFunction reads from env vars
os.environ["CHROMA_OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_embed_fn = OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)
_collection = _client.get_or_create_collection(
    name="curriculum",
    embedding_function=_embed_fn
)


# ── Helpers ────────────────────────────────────────────────────────
def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by character count, trying to break on whitespace."""
    text = " ".join(text.split())  # normalize whitespace
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + chunk_size, len(text))
        # try to break on a space near the end
        if end < len(text):
            space = text.rfind(" ", i, end)
            if space > i + chunk_size // 2:
                end = space
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        i = end - overlap if end - overlap > i else end
    return chunks


def _extract_pdf_text(path: str) -> list[tuple[int, str]]:
    """Returns list of (page_number, page_text)."""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append((i + 1, txt))
        except Exception:
            continue
    return pages


# ── Public API ─────────────────────────────────────────────────────
def ingest_pdf(file_path: str, source_name: str, grade: int | None = None) -> dict:
    """
    Extract text from a PDF, chunk it, embed each chunk, and store in ChromaDB.
    Returns stats about the ingestion.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    # Remove any previous chunks for this source (allows re-ingest)
    delete_source(source_name)

    pages = _extract_pdf_text(file_path)
    if not pages:
        return {"source": source_name, "pages": 0, "chunks": 0, "error": "No extractable text"}

    docs, metas, ids = [], [], []
    for page_num, page_text in pages:
        for chunk in _chunk_text(page_text):
            docs.append(chunk)
            metas.append({
                "source": source_name,
                "page": page_num,
                "grade": grade if grade is not None else 0,
            })
            ids.append(f"{source_name}::p{page_num}::{uuid.uuid4().hex[:8]}")

    if docs:
        # Chroma has a max batch size; chunk uploads to be safe
        BATCH = 100
        for i in range(0, len(docs), BATCH):
            _collection.add(
                documents=docs[i:i + BATCH],
                metadatas=metas[i:i + BATCH],
                ids=ids[i:i + BATCH],
            )

    return {"source": source_name, "pages": len(pages), "chunks": len(docs)}


def retrieve(query: str, grade: int | None = None, k: int = 4) -> list[dict]:
    """Retrieve top-k relevant chunks for a query, optionally filtered by grade."""
    if _collection.count() == 0:
        return []

    where = None
    if grade is not None:
        # Match curriculum chunks for this exact grade OR ungraded (grade=0)
        where = {"grade": {"$in": [grade, 0]}}

    try:
        result = _collection.query(
            query_texts=[query],
            n_results=k,
            where=where,
        )
    except Exception:
        # Fallback: query without filter
        result = _collection.query(query_texts=[query], n_results=k)

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    return [{"text": d, "source": m.get("source", "?"), "page": m.get("page", 0)} for d, m in zip(docs, metas)]


def list_sources() -> list[dict]:
    """Return a list of unique source PDFs currently indexed, with chunk counts."""
    if _collection.count() == 0:
        return []
    all_meta = _collection.get(include=["metadatas"])
    metas = all_meta.get("metadatas", [])
    summary: dict[str, dict] = {}
    for m in metas:
        src = m.get("source", "?")
        if src not in summary:
            summary[src] = {"source": src, "chunks": 0, "grade": m.get("grade", 0)}
        summary[src]["chunks"] += 1
    return list(summary.values())


def delete_source(source_name: str) -> int:
    """Delete all chunks for a given source PDF. Returns number of chunks removed."""
    try:
        existing = _collection.get(where={"source": source_name})
        ids = existing.get("ids", [])
        if ids:
            _collection.delete(ids=ids)
        return len(ids)
    except Exception:
        return 0


def total_chunks() -> int:
    return _collection.count()


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a single context string for the LLM."""
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Source {i}: {c['source']}, page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)
