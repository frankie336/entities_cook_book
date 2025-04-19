#recipes/reccomender/search_movielens.py
"""
Fuzzy search against an existing MovieLens vector store.

Examples
--------
Single query:
    python search_movielens.py --store vect_I1KhGs8LkHJbbNh4fuKYDQ \
                               --query "90s romantic drama movie"

Interactive REPL:
    python search_movielens.py --store vect_I1KhGs8LkHJbbNh4fuKYDQ
"""
import argparse, os, sys
from dotenv import load_dotenv
from projectdavid import Entity

load_dotenv()

def lookup(store_id: str, q: str, top_k: int = 5):
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ENTITIES_API_KEY"),
    )
    embedder = client.vectors.file_processor.embedding_model
    qvec = embedder.encode(
        [q], convert_to_numpy=True, normalize_embeddings=True,
        truncate="model_max_length"
    )[0].tolist()
    hits = client.vectors.vector_manager.query_store(
        store_name=store_id, query_vector=qvec, top_k=top_k
    )
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        genres = ", ".join(m["genres"]) or "Unknown genre"
        year   = m["release_year"] or "—"
        print(f"{i}. 🎬 {m['title']} — [{genres}] ({year}) score={h['score']:.3f}")

def main(store: str, query: str | None, top_k: int):
    if query:
        lookup(store, query, top_k)
    else:
        print("Entering interactive mode (Ctrl‑D to exit)\n")
        try:
            while True:
                q = input("🔍 > ").strip()
                if not q:
                    continue
                lookup(store, q, top_k)
                print()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--store", required=True,
                   help="Vector‑store ID or collection name")
    p.add_argument("--query", help="Single query string (omit for REPL)")
    p.add_argument("--top-k", type=int, default=5)
    main(**vars(p.parse_args()))
