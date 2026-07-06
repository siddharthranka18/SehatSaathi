"""
One-time script: rebuild store.json with cached embedding vectors.
Run this once; after that backend startup will be ~3 seconds instead of ~60s.
Uses in-memory Qdrant so it never conflicts with a running uvicorn instance.
"""
import os, sys, json, uuid, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["QDRANT_HOST"] = "local"  # force in-memory mode

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from rank_bm25 import BM25Okapi

BASE_DIR    = Path(__file__).resolve().parent
GUIDELINES  = BASE_DIR / "data" / "guidelines"
INDEX_DIR   = BASE_DIR / "data" / "rag_index"
COLLECTION  = "medical_guidelines"

# ---------- chunk helper ----------
parent_docs = {}

def create_chunks(text, source):
    result = []
    for section in (s.strip() for s in text.split("\n\n") if s.strip()):
        pid = str(uuid.uuid4())
        parent_docs[pid] = {"text": section, "source": source}
        for sent in section.split("."):
            sent = sent.strip()
            if len(sent) >= 30:
                result.append({"text": sent, "parent_id": pid, "source": source})
    return result

# ---------- load guideline files ----------
all_chunks = []
for fpath in glob.glob(str(GUIDELINES / "*.txt")):
    with open(fpath, encoding="utf-8") as f:
        all_chunks.extend(create_chunks(f.read(), os.path.basename(fpath)))

if not all_chunks:
    print("ERROR: No .txt files found in", GUIDELINES)
    sys.exit(1)

print(f"Loaded {len(all_chunks)} chunks from {GUIDELINES}")

# ---------- embed ----------
print("Loading embedding model (all-MiniLM-L6-v2)...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [c["text"] for c in all_chunks]
print(f"Encoding {len(texts)} chunks...")
embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
print("Encoding complete.")

# ---------- save store.json with vectors ----------
INDEX_DIR.mkdir(parents=True, exist_ok=True)
store = {
    "chunks":  all_chunks,
    "parents": parent_docs,
    "vectors": embeddings.tolist(),   # <-- cached vectors
}
store_path = INDEX_DIR / "store.json"
with open(store_path, "w", encoding="utf-8") as f:
    json.dump(store, f)

size_mb = store_path.stat().st_size / 1_000_000
print(f"\nstore.json written: {size_mb:.1f} MB  ({len(all_chunks)} chunks + vectors cached)")
print("Next uvicorn startup will use cached vectors — no re-encoding needed.")
print("Expected startup time: ~3-5 seconds (model load only, no embedding).")
