import os, re
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from app.config import CHROMA_PERSIST_DIR, EMBED_MODEL, DATA_DIR
from app.ingest.loaders import load_folder, load_urls

URLS_FILE = "urls.txt"  # optional file in app/data

_WS = re.compile(r"\s+")
_URL = re.compile(r"https?://\S+")
_NONALNUM = re.compile(r"[^a-z0-9]+")

def _norm_sig(s: str) -> str:
    s = s.lower()
    s = _URL.sub(" ", s)
    s = _WS.sub(" ", s)
    s = _NONALNUM.sub(" ", s)
    return s.strip()

AD_TOKENS = {"myplate", "available at", "subscribe", "sign up", "cookie", "privacy policy", "newsletter", "back to top", "sponsored"}

def _bad_chunk(txt: str) -> bool:
    low = txt.lower()
    if len(low) < 250:
        return True
    if low.count("http") >= 2:
        return True
    letters = sum(c.isalpha() for c in low)
    if letters < 100:
        return True
    if any(t in low for t in AD_TOKENS):
        return True
    return False

def build_index():
    base_dir = os.fspath(DATA_DIR)
    print(f"[ingest] corpus dir: {base_dir}")

    docs = load_folder(base_dir)

    urls_path = os.path.join(base_dir, URLS_FILE)
    if os.path.exists(urls_path):
        with open(urls_path, "r", encoding="utf-8") as f:
            url_docs = load_urls(f.readlines())
            docs.extend(url_docs)
            print(f"[ingest] loaded {len(url_docs)} docs from URLs")

    if not docs:
        raise SystemExit("No supported documents found. Add PDFs, DOCX, MD/HTML/TXT, or URLs.")

    splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", "? ", "! ", "; ", "• ", " - "]
    )

    chunks = splitter.split_documents(docs)

    # Deduplicate + quality filter
    seen = set()
    unique_chunks = []
    for c in chunks:
        if _bad_chunk(c.page_content or ""):
            continue
        m = c.metadata or {}
        sig = (m.get("source"), m.get("page"), _norm_sig(c.page_content)[:400])
        if sig in seen:
            continue
        seen.add(sig)
        unique_chunks.append(c)

    print(f"[ingest] {len(docs)} base docs → {len(unique_chunks)} unique chunks (filtered from {len(chunks)})")

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    vs = Chroma.from_documents(unique_chunks, embedding=embeddings, persist_directory=CHROMA_PERSIST_DIR)
    vs.persist()
    print(f"[ingest] ✅ index persisted at {CHROMA_PERSIST_DIR}")

if __name__ == "__main__":
    build_index()
