import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env once at import time
load_dotenv()

# === OpenAI ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # expects sk-proj-... or sk-live-...
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in environment/.env")

# Models (safe, inexpensive defaults)
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === Retrieval / Storage ===
TOP_K = int(os.getenv("TOP_K", "4"))
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", ".chroma_store")

# Project roots
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
